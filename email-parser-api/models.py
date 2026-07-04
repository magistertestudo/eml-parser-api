from pydantic import BaseModel
from typing import List


class EmailHeader(BaseModel):
    sender: str = ""
    to: str = ""
    cc: str = ""
    bcc: str = ""
    reply_to: str = ""
    subject: str = ""
    date: str = ""
    message_id: str = ""


class EmailBody(BaseModel):
    plain_text: str = ""
    html: str = ""


class Attachment(BaseModel):
    filename: str = ""
    mime_type: str = ""
    size: int = 0
    inline: bool = False
    content_id: str = ""


class ParsedEmail(BaseModel):
    header: EmailHeader
    body: EmailBody
    attachments: List[Attachment] = []


class ParseResponse(BaseModel):
    emails: List[ParsedEmail]