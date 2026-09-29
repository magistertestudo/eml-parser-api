"""Small HTTP adapter for documented pCloud endpoints; no SDK required."""
import hashlib
import os
import re
import unicodedata
from dataclasses import dataclass, field
import httpx


class PCloudError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    token: str = field(repr=False)
    host: str
    parent_id: int
    auth_type: str = "oauth"
    link_mode: str = "upload_request"

    def __post_init__(self):
        if self.auth_type not in {"oauth", "direct"}:
            raise PCloudError("PCLOUD_AUTH_TYPE deve essere oauth o direct.")

    @classmethod
    def from_env(cls):
        if os.getenv('PCLOUD_ENABLED', 'false').lower() != 'true':
            return None
        auth_type = os.getenv('PCLOUD_AUTH_TYPE', 'oauth')
        if auth_type not in {'oauth', 'direct'}:
            raise PCloudError('PCLOUD_AUTH_TYPE deve essere oauth o direct.')
        token = os.getenv('PCLOUD_AUTH_TOKEN' if auth_type == 'direct' else 'PCLOUD_ACCESS_TOKEN', '')
        host = os.getenv('PCLOUD_API_HOST', 'api.pcloud.com')
        parent = os.getenv('PCLOUD_PARENT_FOLDER_ID', '29662386698')
        if not token or host not in {'api.pcloud.com', 'eapi.pcloud.com'} or not parent.isdigit() or int(parent) <= 0:
            raise PCloudError('Configurare token, host regionale e ID della cartella di destinazione.')
        link_mode = os.getenv('PCLOUD_LINK_MODE', '')
        if link_mode != 'upload_request':
            raise PCloudError('Impostare PCLOUD_LINK_MODE=upload_request per consentire caricamenti senza account.')
        return cls(token, host, int(parent), auth_type, link_mode)


def safe_name(name):
    original = unicodedata.normalize('NFC', str(name))
    cleaned = re.sub(r'[/\\\x00-\x1f\x7f]', '_', original).strip().strip('.')
    if not cleaned:
        cleaned = 'file'
    if cleaned != original or len(cleaned.encode('utf-8')) > 180:
        cleaned = cleaned.encode('utf-8')[:150].decode('utf-8', errors='ignore') + '-' + hashlib.sha256(original.encode()).hexdigest()[:12]
    return cleaned


class PCloudClient:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.http = httpx.Client(base_url=f'https://{settings.host}',
                                 timeout=httpx.Timeout(120, connect=15), follow_redirects=False,
                                 transport=transport)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.http.close()

    def call(self, method, data, files=None):
        try:
            response = self.http.post('/' + method, data={**data, ('auth' if self.settings.auth_type == 'direct' else 'access_token'): self.settings.token}, files=files)
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError):
            raise PCloudError(f'pCloud: errore di trasporto/risposta durante {method}; riprovare con gli stessi input.') from None
        if not isinstance(result, dict) or result.get('result') != 0:
            code = result.get('result', 'invalid') if isinstance(result, dict) else 'invalid'
            raise PCloudError(f'pCloud: {method} fallito (codice {code}).')
        return result

    def archive_email(self, opportunity, eml, attachments):
        if not opportunity.strip():
            raise PCloudError('Opportunity Name mancante.')
        parent = self.call('listfolder', {'folderid': self.settings.parent_id}).get('metadata', {})
        if (parent.get('folderid') != self.settings.parent_id
                or not parent.get('isfolder') or not parent.get('ismine')):
            raise PCloudError('La destinazione deve corrispondere all’ID configurato ed essere una cartella di proprietà dell’account.')
        folder = self.call('createfolderifnotexists', {'folderid': self.settings.parent_id, 'name': safe_name(opportunity)}).get('metadata', {})
        folder_id = folder.get('folderid')
        if not isinstance(folder_id, int) or folder_id <= 0:
            raise PCloudError('pCloud: ID della cartella non restituito.')
        digest = hashlib.sha256(eml).hexdigest()
        # Stable names: retries overwrite identical bytes; different messages never collide.
        uploads = [(f'{digest}-originale.eml', eml, 'message/rfc822')]
        uploads.extend((f'{digest}-{i:03d}-{safe_name(a["filename"])}', a['content'], a['mime_type'])
                       for i, a in enumerate(attachments, 1))
        for name, content, mime in uploads:
            result = self.call('uploadfile', {'folderid': folder_id, 'nopartial': 1},
                               files={'file': (name, content, mime)})
            metadata = result.get('metadata', [])
            if len(metadata) != 1 or metadata[0].get('size') != len(content):
                raise PCloudError('pCloud: dimensione upload non confermata.')
        if self.settings.link_mode == 'shared_upload':
            return self.shared_upload_link(folder_id)
        existing = self.call('listuploadlinks', {})
        for link in existing.get('uploadlinks', []):
            metadata = link.get('metadata', {})
            if metadata.get('folderid') == folder_id and not any(link.get(k) for k in ('expires', 'expire', 'maxspace', 'maxfiles')):
                if str(link.get('link', '')).startswith('https://'):
                    return link['link']
        link = self.call('createuploadlink', {'folderid': folder_id, 'comment': f'Carica documenti per {opportunity}'})
        url = link.get('link', '')
        if not url.startswith('https://'):
            raise PCloudError('pCloud: link di caricamento non restituito.')
        return url

    def shared_upload_link(self, folder_id):
        link = self.call('getfolderpublink', {'folderid': folder_id})
        link_id = link.get('linkid')
        url = link.get('link', '')
        if type(link_id) is not int or link_id <= 0 or not url.startswith('https://'):
            raise PCloudError('pCloud: link condiviso non restituito.')
        # Official pCloud console-client/publiclinks.c: do_change_link_enable_upload.
        self.call('changepublink', {'linkid': link_id,
                                   'enableuploadforeveryone': 1,
                                   'enableuploadforchosenusers': 0})
        links = self.call('listpublinks', {}).get('publinks', [])
        verified = next((item for item in links if item.get('linkid') == link_id), {})
        if (verified.get('metadata', {}).get('folderid') != folder_id
                or not verified.get('enableuploadforeveryone')
                or verified.get('enableuploadforchosenusers')):
            raise PCloudError('pCloud: permesso di caricamento sul link condiviso non confermato.')
        return url
