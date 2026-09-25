from email import policy
from email.parser import BytesParser
import mimetypes
from bs4 import BeautifulSoup


def parse_eml(file_bytes: bytes):
    msg = BytesParser(policy=policy.default).parsebytes(file_bytes)
    names = {'sender': 'From', 'to': 'To', 'cc': 'Cc', 'bcc': 'Bcc',
             'reply_to': 'Reply-To', 'subject': 'Subject', 'date': 'Date', 'message_id': 'Message-ID'}
    header = {name: str(msg.get(field, '')) for name, field in names.items()}
    plain, html, attachments = [], [], []

    def visit(part):
        content_type = part.get_content_type()
        disposition = part.get_content_disposition()
        filename = part.get_filename()
        cid = part.get('Content-ID')
        if filename or cid or disposition == 'attachment' or content_type == 'message/rfc822':
            payload = part.get_payload(decode=True)
            if payload is None and part.is_multipart():
                if content_type == 'message/rfc822':
                    payload = b'\r\n'.join(child.as_bytes(policy=policy.SMTP) for child in part.get_payload())
                else:
                    payload = part.as_bytes(policy=policy.SMTP)
            payload = payload or b''
            suffix = '.eml' if content_type == 'message/rfc822' else (mimetypes.guess_extension(content_type) or '.bin')
            attachments.append({'filename': filename or f'allegato-{len(attachments)+1}{suffix}',
                                'mime_type': content_type, 'size': len(payload),
                                'inline': disposition == 'inline' or cid is not None,
                                'content_id': str(cid or ''), 'content': payload})
            return  # Attached emails must not contaminate sender/body extraction.
        if part.is_multipart():
            for child in part.iter_parts():
                visit(child)
        elif content_type in ('text/plain', 'text/html'):
            content = part.get_content(errors='replace')
            (plain if content_type == 'text/plain' else html).append(content)

    visit(msg)
    body = '\n'.join(plain)
    if not body.strip() and html:
        soup = BeautifulSoup('\n'.join(html), 'lxml')
        for element in soup(['script', 'style']):
            element.decompose()
        body = soup.get_text('\n', strip=True)
    return {'header': header, 'body': {'plain_text': body}, 'attachments': attachments}
