from fastapi import FastAPI, UploadFile, File
from typing import List

from parser import parse_eml

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
async def parse(files: list[UploadFile] = File(...)):

    emails = []

    for file in files:
        data = await file.read()

        result = parse_eml(data)

        emails.append({
            "filename": file.filename,
            "parsed": result
        })

    return {
        "count": len(emails),
        "emails": emails
    }
