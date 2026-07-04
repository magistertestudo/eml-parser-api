from zipfile import ZipFile
from io import BytesIO

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
