from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup


def parse_eml(file_bytes: bytes):

    msg = BytesParser(policy=policy.default).parsebytes(file_bytes)

    header = {
        "sender": msg.get("From", ""),
        "to": msg.get("To", ""),
        "cc": msg.get("Cc", ""),
        "bcc": msg.get("Bcc", ""),
        "reply_to": msg.get("Reply-To", ""),
        "subject": msg.get("Subject", ""),
        "date": msg.get("Date", ""),
        "message_id": msg.get("Message-ID", "")
    }

    plain_text = ""
    html = ""
    attachments = []

    for part in msg.walk():

        content_type = part.get_content_type()
        disposition = str(part.get_content_disposition())

        if content_type == "text/plain" and disposition != "attachment":
            try:
                plain_text += part.get_content()
            except Exception:
                pass

        elif content_type == "text/html" and disposition != "attachment":
            try:
                html += part.get_content()
            except Exception:
                pass

        filename = part.get_filename()
        content_id = part.get("Content-ID")

        if filename or content_id:

            payload = part.get_payload(decode=True) or b""

            attachments.append({
                "filename": filename or "",
                "mime_type": content_type,
                "size": len(payload),
                "inline": content_id is not None,
                "content_id": content_id or ""
            })

    if html:
        soup = BeautifulSoup(html, "lxml")
        html = str(soup)

    return {
        "header": header,
        "body": {
            "plain_text": plain_text,
            "html": html
        },
        "attachments": attachments
    }
