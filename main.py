from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

from typing import List
from zipfile import ZipFile
from io import BytesIO
from pathlib import Path
import json
import logging
from starlette.concurrency import run_in_threadpool
from pcloud_client import PCloudClient, PCloudError, Settings
from website_province import fallback_province

from parser import parse_eml
from openai_client import ask_gpt
from crm_mapper import map_to_delera
from csv_exporter import build_csv


PROMPT = Path(__file__).with_name("prompt_v1.md").read_text(encoding="utf-8")


app = FastAPI(
    title="EML CRM Extractor API",
    version="2.0.2"
)


@app.get("/")
def home():

    return {

        "service": "EML CRM Extractor API",

        "version": "2.0.2",

        "status": "running"

    }


def process_email(
    eml_bytes: bytes,
    filename: str,
    protocol: str,
    pcloud=None
) -> dict:

    parsed = parse_eml(eml_bytes)

    user_prompt = json.dumps(
        {
            "sender": parsed["header"].get("sender", ""),
            "subject": parsed["header"].get("subject", ""),
            "body": parsed["body"].get("plain_text", ""),
            "attachments": [
                a.get("filename", "")
                for a in parsed.get("attachments", [])
            ]
        },
        ensure_ascii=False
    )

    ai = ask_gpt(
        PROMPT,
        user_prompt
    )

    resolution = fallback_province(ai, parsed["header"].get("sender", ""))
    if not resolution.name:
        logging.getLogger(__name__).warning("Provincia non risolta (%s), protocollo %s", resolution.reason, protocol)

    record = map_to_delera(
        ai,
        filename=filename,
        protocol=protocol
    )

    record["Provincia"] = resolution.name
    if resolution.reason in {"website_resolved", "website_registered_office"}:
        logging.getLogger(__name__).info("Provincia ricavata dal sito del contatto, protocollo %s", protocol)

    if pcloud is not None:
        record["Cartella Allegati"] = pcloud.archive_email(
            record["Opportunity Name"], eml_bytes, parsed["attachments"]
        )
    return record


def build_records(inputs, protocol_start, pcloud=None):
    try:
        year, progressive = protocol_start.split()
        if len(year) != 4 or not year.isdigit() or not progressive.isdigit():
            raise ValueError
        progressive = int(progressive)
    except ValueError:
        raise HTTPException(422, 'protocol_start deve avere formato 2026 4000.') from None
    records = []
    def consume(data, name):
        nonlocal progressive
        records.append(process_email(data, name, f"{year} {progressive}", pcloud))
        progressive += 1
    for filename, data in inputs:
        if filename.lower().endswith('.zip'):
            from zipfile import BadZipFile
            try:
                with ZipFile(BytesIO(data)) as archive:
                    for item in archive.infolist():
                        name = item.filename
                        if item.is_dir() or name.startswith('__MACOSX/') or name.split('/')[-1].startswith('._'):
                            continue
                        if name.lower().endswith('.eml'):
                            consume(archive.read(item), name)
            except BadZipFile:
                raise HTTPException(422, 'Archivio ZIP non valido.') from None
        elif filename.lower().endswith('.eml'):
            consume(data, filename)
        else:
            raise HTTPException(422, 'Sono ammessi file .eml e .zip.')
    if not records:
        raise HTTPException(422, 'Nessuna email .eml trovata.')
    return records


def run_pipeline(inputs, protocol_start):
    try:
        settings = Settings.from_env()
        if settings is None:
            return build_csv(build_records(inputs, protocol_start))
        with PCloudClient(settings) as pcloud:
            return build_csv(build_records(inputs, protocol_start, pcloud))
    except PCloudError as exc:
        # Never return a success CSV with partially archived email attachments.
        raise HTTPException(502, str(exc)) from None


@app.post('/parse')
async def parse(files: List[UploadFile] = File(...), protocol_start: str = Form(...)):
    inputs = [(file.filename or '', await file.read()) for file in files]
    csv_data = await run_in_threadpool(run_pipeline, inputs, protocol_start)
    return Response(content=csv_data, media_type='text/csv',
                    headers={'Content-Disposition': 'attachment; filename="contatti_delera.csv"'})
