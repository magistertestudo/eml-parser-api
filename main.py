from fastapi import FastAPI, UploadFile, File
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


# ==========================================================
# CONFIGURAZIONE
# ==========================================================

PROMPT = Path("prompt_v1.md").read_text(encoding="utf-8")


app = FastAPI(
    title="EML CRM Extractor API",
    version="2.0"
)


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.get("/")
def home():

    return {

        "service": "EML CRM Extractor API",

        "version": "2.0",

        "status": "running"

    }


# ==========================================================
# ELABORAZIONE SINGOLA EMAIL
# ==========================================================

def process_email(
    eml_bytes: bytes,
    filename: str
) -> dict:

    # Parsing MIME

    parsed = parse_eml(eml_bytes)

    # Costruzione prompt GPT

    user_prompt = json.dumps(

        {

            "sender":
            parsed["header"].get("sender", ""),

            "subject":
            parsed["header"].get("subject", ""),

            "body":
            parsed["body"].get("plain_text", ""),

            "attachments": [

                a.get("filename", "")

                for a in parsed.get(
                    "attachments",
                    []
                )

            ]

        },

        ensure_ascii=False

    )

    # Estrazione AI

    ai_record = ask_gpt(
        PROMPT,
        user_prompt
    )

    # Mapping CRM

    crm_record = map_to_delera(

        ai_record,

        filename=filename

    )

    return crm_record


# ==========================================================
# ENDPOINT PRINCIPALE
# ==========================================================

@app.post("/parse")
async def parse(
    files: List[UploadFile] = File(...)
):

    records = []

    for file in files:

        data = await file.read()

        # --------------------------------------
        # ZIP
        # --------------------------------------

        if file.filename.lower().endswith(".zip"):

            with ZipFile(BytesIO(data)) as archive:

                for name in archive.namelist():

                    # Cartelle MacOS

                    if name.startswith("__MACOSX/"):
                        continue

                    # File Finder

                    if name.split("/")[-1].startswith("._"):
                        continue

                    # Solo EML

                    if not name.lower().endswith(".eml"):
                        continue

                    record = process_email(

                        archive.read(name),

                        filename=name

                    )

                    records.append(record)

        # --------------------------------------
        # EML
        # --------------------------------------

        else:

            record = process_email(

                data,

                filename=file.filename

            )

            records.append(record)

    # ======================================================
    # GENERAZIONE CSV
    # ======================================================

    csv_data = build_csv(records)

    return Response(

        content=csv_data,

        media_type="text/csv",

        headers={

            "Content-Disposition":
            'attachment; filename="contatti_delera.csv"'

        }

    )