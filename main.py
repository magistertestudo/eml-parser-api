from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import Response

from typing import List
from zipfile import ZipFile
from io import BytesIO
from pathlib import Path
import json

from parser import parse_eml
from openai_client import ask_gpt
from crm_mapper import map_to_delera
from csv_exporter import build_csv


PROMPT = Path("prompt_v1.md").read_text(encoding="utf-8")


app = FastAPI(
    title="EML CRM Extractor API",
    version="2.0"
)


@app.get("/")
def home():

    return {

        "service": "EML CRM Extractor API",

        "version": "2.0",

        "status": "running"

    }


def process_email(
    eml_bytes: bytes,
    filename: str,
    protocol: str
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

    return map_to_delera(
        ai,
        filename=filename,
        protocol=protocol
    )


@app.post("/parse")
async def parse(

    files: List[UploadFile] = File(...),

    protocol_start: str = Form(...)

):

    year, progressive = protocol_start.split()

    progressive = int(progressive)

    records = []

    for file in files:

        data = await file.read()

        if file.filename.lower().endswith(".zip"):

            with ZipFile(BytesIO(data)) as archive:

                for name in archive.namelist():

                    if name.startswith("__MACOSX/"):
                        continue

                    if name.split("/")[-1].startswith("._"):
                        continue

                    if not name.lower().endswith(".eml"):
                        continue

                    protocol = f"{year} {progressive}"

                    record = process_email(

                        archive.read(name),

                        filename=name,

                        protocol=protocol

                    )

                    records.append(record)

                    progressive += 1

        else:

            protocol = f"{year} {progressive}"

            record = process_email(

                data,

                filename=file.filename,

                protocol=protocol

            )

            records.append(record)

            progressive += 1

    csv_data = build_csv(records)

    return Response(

        content=csv_data,

        media_type="text/csv",

        headers={

            "Content-Disposition":
            'attachment; filename="contatti_delera.csv"'

        }

    )