from fastapi import FastAPI, UploadFile, File
from typing import List
from zipfile import ZipFile
from io import BytesIO
from pathlib import Path
import json

from parser import parse_eml
from openai_client import ask_gpt
from crm_enricher import enrich
from fastapi.responses import Response
from csv_exporter import build_csv

PROMPT = Path("prompt_v1.md").read_text(encoding="utf-8")

app = FastAPI(
    title="EML Parser API",
    version="1.1"
)


@app.get("/")
def home():
    return {
        "service": "EML Parser API",
        "version": "1.1",
        "status": "running"
    }


def process_email(eml_bytes: bytes, filename: str) -> dict:
    """
    Elabora una singola email:
    - parsing MIME
    - chiamata GPT
    - arricchimento CRM
    """

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

    crm = ask_gpt(PROMPT, user_prompt)

    crm = enrich(
        crm,
        filename=filename
    )

    return crm


@app.post("/parse")
async def parse(files: List[UploadFile] = File(...)):

    records = []

    for file in files:

        data = await file.read()

        # ==========================
        # ZIP
        # ==========================
        if file.filename.lower().endswith(".zip"):

            with ZipFile(BytesIO(data)) as archive:

                for name in archive.namelist():

                    # ignora cartelle MacOS
                    if name.startswith("__MACOSX/"):
                        continue

                    # ignora file nascosti Finder
                    if name.split("/")[-1].startswith("._"):
                        continue

                    if not name.lower().endswith(".eml"):
                        continue

                    records.append(
                        process_email(
                            archive.read(name),
                            filename=name
                        )
                    )

        # ==========================
        # EML singolo
        # ==========================
        else:

            records.append(
                process_email(
                    data,
                    filename=file.filename
                )
            )

csv_data = build_csv(records)

return Response(
    content=csv_data,
    media_type="text/csv",
    headers={
        "Content-Disposition": 'attachment; filename="contatti_delera.csv"'
    }
)