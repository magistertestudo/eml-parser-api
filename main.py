from fastapi import FastAPI, UploadFile, File
from typing import List
from zipfile import ZipFile
from io import BytesIO
from pathlib import Path
import json

from parser import parse_eml
from openai_client import ask_gpt

PROMPT = Path("prompt_v1.md").read_text(encoding="utf-8")

app = FastAPI(
    title="EML Parser API",
    version="1.0"
)


@app.get("/")
def home():
    return {
        "service": "EML Parser API",
        "version": "1.0",
        "status": "running"
    }


def process_email(eml_bytes: bytes) -> dict:
    """
    Estrae i dati dall'email, prepara il prompt
    e richiama GPT.
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
        ensure_ascii=False,
    )

    return ask_gpt(PROMPT, user_prompt)


@app.post("/parse")
async def parse(files: List[UploadFile] = File(...)):

    emails = []

    for file in files:

        data = await file.read()

        # ZIP
        if file.filename.lower().endswith(".zip"):

            with ZipFile(BytesIO(data)) as archive:

                for name in archive.namelist():

                    # ignora file nascosti macOS
                    if name.startswith("__MACOSX/"):
                        continue

                    if name.startswith("._"):
                        continue

                    if not name.lower().endswith(".eml"):
                        continue

                    emails.append(
                        process_email(
                            archive.read(name)
                        )
                    )

        # EML singolo
        else:

            emails.append(
                process_email(data)
            )

    return emails
