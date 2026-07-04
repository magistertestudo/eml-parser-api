from fastapi import FastAPI, UploadFile, File
from typing import List
from zipfile import ZipFile
from io import BytesIO

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
async def parse(files: List[UploadFile] = File(...)):

    emails = []

    for file in files:

        data = await file.read()

        # ZIP
        if file.filename.lower().endswith(".zip"):

            with ZipFile(BytesIO(data)) as z:

                for name in z.namelist():

                    if name.lower().endswith(".eml"):

                        eml_bytes = z.read(name)

                        emails.append({
                            "filename": name,
                            "parsed": parse_eml(eml_bytes)
                        })

        # EML
        else:

            emails.append({
                "filename": file.filename,
                "parsed": parse_eml(data)
            })

    return {
        "count": len(emails),
        "emails": emails
    }
