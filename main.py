from fastapi import FastAPI, UploadFile, File
from typing import List
from zipfile import ZipFile
from io import BytesIO
from pathlib import Path
import json

from parser import parse_eml
from openai_client import ask_gpt

PROMPT = Path("prompts/prompt_v1.md").read_text(encoding="utf-8")

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


@app.post("/parse")
async def parse(files: List[UploadFile] = File(...)):

    emails = []

    for file in files:

        data = await file.read()

        # ZIP
        if file.filename.lower().endswith(".zip"):

            with ZipFile(BytesIO(data)) as z:

                for name in z.namelist():

                    # ignora file nascosti MacOS
                    if name.startswith("__MACOSX/"):
                        continue

                    if not name.lower().endswith(".eml"):
                        continue

                    parsed = parse_eml(z.read(name))

                    user_prompt = json.dumps(
                        {
                            "sender": parsed["header"]["sender"],
                            "subject": parsed["header"]["subject"],
                            "body": parsed["body"]["plain_text"],
                        },
                        ensure_ascii=False,
                    )

                    crm = ask_gpt(PROMPT, user_prompt)

                    emails.append(json.loads(crm))

        # EML singolo
        else:

            parsed = parse_eml(data)

            user_prompt = json.dumps(
                {
                    "sender": parsed["header"]["sender"],
                    "subject": parsed["header"]["subject"],
                    "body": parsed["body"]["plain_text"],
                },
                ensure_ascii=False,
            )

            crm = ask_gpt(PROMPT, user_prompt)

            emails.append(json.loads(crm))

    return emails
