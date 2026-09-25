import csv
import io
import json
from email.message import EmailMessage
from urllib.parse import parse_qs
from zipfile import ZipFile
import httpx
import pytest
from fastapi.testclient import TestClient
import main
from parser import parse_eml
from province_resolver import resolve_province
from pcloud_client import PCloudClient, PCloudError, Settings, safe_name
from crm_schema import CSV_COLUMNS


@pytest.mark.parametrize('fields,expected', [
    ({'Provincia': ' fi '}, 'Firenze'),
    ({'Provincia': 'FORLI CESENA'}, 'Forlì-Cesena'),
    ({'Provincia': 'Provincia di Milano'}, 'Milano'),
    ({'Provincia': None, 'Comune': 'Sesto Fiorentino'}, 'Firenze'),
    ({'Comune': 'Busto Arsizio'}, 'Varese'),
    ({'CAP': '00118'}, 'Roma'),
    ({'CAP': '50019'}, 'Firenze'),
    ({'Indirizzo': 'Via Roma 20, 50019 Sesto Fiorentino (FI)'}, 'Firenze'),
    ({'Indirizzo': 'Via Roma 1 (MI)'}, 'Milano'),
    ({'Indirizzo': 'Via Roma 1'}, ''),
    ({'Comune': 'Milano', 'Provincia': 'FI'}, ''),
    ({'Comune': 'Milano', 'CAP': '50019'}, ''),
    ({'CAP': '99999'}, ''),
    ({'Provincia': 'NA', 'Nazione': 'USA'}, ''),
    ({'Provincia': 'fantasia'}, ''),
    ({'Provincia': 'Bolzano/Bozen'}, 'Bolzano'),
    ({}, ''),
])
def test_province(fields, expected):
    assert resolve_province(fields).name == expected


def email():
    msg = EmailMessage()
    msg['From'] = 'Mario <mario@example.org>'
    msg['Subject'] = 'Preventivo'
    msg.set_content('<html><body>Richiesta da Sesto Fiorentino</body></html>', subtype='html')
    msg.add_attachment(b'\x00\xffpdf', maintype='application', subtype='pdf', filename='prova.pdf')
    msg.add_attachment(b'second', maintype='application', subtype='pdf', filename='prova.pdf')
    nested = EmailMessage()
    nested.set_content('Firma estranea da non estrarre')
    msg.add_attachment(nested, filename='forward.eml')
    return msg.as_bytes()


def test_parser_preserves_files_and_separates_forward():
    parsed = parse_eml(email())
    assert parsed['body']['plain_text'] == 'Richiesta da Sesto Fiorentino'
    assert len(parsed['attachments']) == 3
    assert parsed['attachments'][0]['content'] == b'\x00\xffpdf'
    assert b'Firma estranea' in parsed['attachments'][2]['content']


def test_unnamed_and_inline():
    msg = EmailMessage()
    msg.set_content('hello')
    msg.add_attachment(b'file', maintype='application', subtype='octet-stream')
    msg.add_attachment(b'img', maintype='image', subtype='png', disposition='inline', cid='<img>')
    parts = parse_eml(msg.as_bytes())['attachments']
    assert len(parts) == 2
    assert all(p['filename'] and p['content'] for p in parts)
    assert parts[1]['inline']


def pcloud_mock(fail=None, existing=False):
    calls = []
    def handler(request):
        method = request.url.path[1:]
        calls.append((method, request))
        assert b'test-secret' in request.content
        assert b'access_token' in request.content
        assert 'test-secret' not in str(request.url)
        if method == fail:
            return httpx.Response(200, json={'result': 2000, 'error': 'secret server details'})
        if method == 'listfolder':
            payload = {'metadata': {'name': 'OFFERTE 2026', 'ismine': True}}
        elif method == 'createfolderifnotexists':
            payload = {'metadata': {'folderid': 7}}
        elif method == 'uploadfile':
            # Parse actual multipart, verifying decoded bytes and metadata size.
            boundary = request.headers['content-type'].split('boundary=')[1].encode()
            file_part = request.content.split(b'--' + boundary)[-2]
            body = file_part.split(b'\r\n\r\n', 1)[1][:-2]
            payload = {'metadata': [{'size': len(body)}]}
        elif method == 'listuploadlinks':
            payload = {'uploadlinks': [{'metadata': {'folderid': 7}, 'link': 'https://my.pcloud.com/existing'}] if existing else []}
        elif method == 'createuploadlink':
            payload = {'link': 'https://my.pcloud.com/upload'}
        else:
            raise AssertionError(method)
        return httpx.Response(200, json={'result': 0, **payload})
    return httpx.MockTransport(handler), calls


def test_archive_original_attachments_and_retry_names():
    transport, calls = pcloud_mock(existing=True)
    raw = email()
    with PCloudClient(Settings('test-secret', 'eapi.pcloud.com', 1), transport) as client:
        for _ in range(2):
            assert client.archive_email('2026 4000 | ACME', raw, parse_eml(raw)['attachments']).endswith('/existing')
    uploads = [r for m,r in calls if m == 'uploadfile']
    assert len(uploads) == 8
    assert raw in uploads[0].content
    assert b'\x00\xffpdf' in uploads[1].content
    assert b'2026 4000' in [r for m,r in calls if m=='createfolderifnotexists'][0].content.replace(b'+', b' ')
    # Boundary differs, filenames remain stable and distinct even with duplicate names.
    import re
    names = [re.search(rb'filename="([^"]+)"', r.content)[1] for r in uploads]
    assert names[:4] == names[4:]
    assert len(set(names[:4])) == 4
    assert not any(m=='createuploadlink' for m,r in calls)


def test_create_upload_link():
    transport, calls = pcloud_mock()
    with PCloudClient(Settings('test-secret', 'api.pcloud.com', 1), transport) as client:
        assert client.archive_email('2026 1', b'original', []).endswith('/upload')
    assert calls[-1][0] == 'createuploadlink'


@pytest.mark.parametrize('failure', ['listfolder', 'createfolderifnotexists', 'uploadfile', 'listuploadlinks', 'createuploadlink'])
def test_remote_error_does_not_succeed_or_leak(failure):
    transport, calls = pcloud_mock(fail=failure)
    with PCloudClient(Settings('test-secret', 'api.pcloud.com', 1), transport) as client:
        with pytest.raises(PCloudError) as exc:
            client.archive_email('2026 1', b'original', [])
    assert 'test-secret' not in str(exc.value)
    assert 'secret server details' not in str(exc.value)
    assert calls[-1][0] == failure


def test_transport_failure():
    def handler(request):
        raise httpx.ReadTimeout('secret')
    with PCloudClient(Settings('test-secret', 'api.pcloud.com', 1), httpx.MockTransport(handler)) as client:
        with pytest.raises(PCloudError, match='trasporto'):
            client.archive_email('x', b'x', [])


def test_safe_names():
    assert safe_name('2026 4000 | ACME') == '2026 4000 | ACME'
    assert safe_name('a/b') != safe_name('a\\b')
    assert '/' not in safe_name('../../file')
    assert len(safe_name('é'*300).encode()) <= 180


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv('PCLOUD_ENABLED', 'false')
    monkeypatch.setattr(main, 'ask_gpt', lambda *a: {'Azienda':'ACME','Comune':'Sesto Fiorentino'})
    return TestClient(main.app)


def test_api_zip_csv_contract(api):
    archive = io.BytesIO()
    with ZipFile(archive, 'w') as z:
        z.writestr('__MACOSX/._test.eml', b'bad')
        z.writestr('first.eml', email())
        z.writestr('folder/second.eml', email())
    response = api.post('/parse', data={'protocol_start':'2026 4000'}, files=[('files', ('test.zip', archive.getvalue()))])
    assert response.status_code == 200
    reader = csv.DictReader(io.StringIO(response.text))
    assert reader.fieldnames == CSV_COLUMNS
    rows = list(reader)
    assert [r['Numero di Protocollo'] for r in rows] == ['2026 4000','2026 4001']
    assert rows[0]['Provincia'] == 'Firenze'
    assert rows[0]['Cartella Allegati'] == ''


def test_process_attaches_only_names_to_ai(monkeypatch):
    raw = email()
    def ai(prompt, data):
        payload = json.loads(data)
        assert payload['attachments'] == ['prova.pdf','prova.pdf','forward.eml']
        return {'Azienda':'ACME','Provincia':'FI'}
    class Cloud:
        def archive_email(self, opportunity, original, attachments):
            assert original == raw
            assert opportunity == '2026 1 | ACME'
            assert len(attachments)==3
            return 'https://my.pcloud.com/upload'
    monkeypatch.setattr(main, 'ask_gpt', ai)
    record = main.process_email(raw, 'file.eml', '2026 1', Cloud())
    assert record['Cartella Allegati'].endswith('/upload')


@pytest.mark.parametrize('protocol,name,data', [('bad','a.eml',b'x'),('2026 1','a.zip',b'bad'),('2026 1','a.txt',b'x')])
def test_bad_inputs(api, protocol, name, data):
    assert api.post('/parse', data={'protocol_start': protocol}, files={'files':(name,data)}).status_code == 422


def test_missing_config_fails_closed(api, monkeypatch):
    monkeypatch.setenv('PCLOUD_ENABLED','true')
    monkeypatch.delenv('PCLOUD_ACCESS_TOKEN', raising=False)
    response = api.post('/parse', data={'protocol_start':'2026 1'}, files={'files':('a.eml',email())})
    assert response.status_code == 502
    assert 'text/csv' not in response.headers['content-type']


def test_parent_must_match_and_be_owned():
    for metadata in ({'name':'IN-SAFETY-2026','ismine':True}, {'name':'OFFERTE 2026','ismine':False}):
        transport = httpx.MockTransport(lambda request: httpx.Response(200,json={'result':0,'metadata':metadata}))
        with PCloudClient(Settings('x','api.pcloud.com',1),transport) as cloud:
            with pytest.raises(PCloudError, match='OFFERTE 2026'):
                cloud.archive_email('2026 1',b'x',[])


def test_unconfirmed_upload_size_rejected():
    base, calls = pcloud_mock()
    def handler(request):
        if request.url.path == '/uploadfile':
            return httpx.Response(200,json={'result':0,'metadata':[{'size':999}]})
        return base.handle_request(request)
    with PCloudClient(Settings('test-secret','api.pcloud.com',1),httpx.MockTransport(handler)) as cloud:
        with pytest.raises(PCloudError,match='dimensione'):
            cloud.archive_email('2026 1',b'x',[])


def test_cloud_failure_returns_error_not_csv(api, monkeypatch):
    transport, calls = pcloud_mock(fail='uploadfile')
    monkeypatch.setattr(main.Settings,'from_env',lambda: Settings('test-secret','api.pcloud.com',1))
    monkeypatch.setattr(main,'PCloudClient',lambda settings: PCloudClient(settings, transport))
    response = api.post('/parse',data={'protocol_start':'2026 1'},files={'files':('a.eml',email())})
    assert response.status_code == 502
    assert 'text/csv' not in response.headers['content-type']


def test_mode_must_be_explicit(monkeypatch):
    for k,v in {'PCLOUD_ENABLED':'true','PCLOUD_ACCESS_TOKEN':'test','PCLOUD_API_HOST':'api.pcloud.com','PCLOUD_PARENT_FOLDER_ID':'1','PCLOUD_LINK_MODE':'shared_upload'}.items():
        monkeypatch.setenv(k,v)
    with pytest.raises(PCloudError,match='upload_request'):
        Settings.from_env()


@pytest.mark.parametrize('fields,expected', [
    ({'Comune':'Olbia'}, 'Gallura Nord-Est Sardegna'),
    ({'Comune':'Tortolì'}, 'Ogliastra'),
    ({'Comune':'Carbonia'}, 'Sulcis Iglesiente'),
    ({'Comune':'Sanluri'}, 'Medio Campidano'),
    ({'Provincia':'OT'}, 'Gallura Nord-Est Sardegna'),
    ({'Provincia':'CI'}, 'Sulcis Iglesiente'),
    ({'Provincia':'OG'}, 'Ogliastra'),
    ({'Provincia':'VS'}, 'Medio Campidano'),
    ({'Provincia':'SU'}, ''),
    ({'Provincia':'SU','Comune':'Carbonia'}, 'Sulcis Iglesiente'),
    ({'Comune':'Castegnero Nanto'}, 'Vicenza'),
    ({'Comune':'Murisengo Monferrato'}, 'Alessandria'),
    ({'Provincia':'FI','Indirizzo':'Via Garibaldi 3, Milano'}, ''),
    ({'Indirizzo':'Via Garibaldi 3, Milano MI'}, 'Milano'),
    ({'Indirizzo':'Via Garibaldi 3, Milano FI'}, ''),
])
def test_current_geography_and_address_consistency(fields,expected):
    assert resolve_province(fields).name == expected


def test_official_geographic_snapshot():
    from pathlib import Path
    data=json.loads(Path('data/comuni.json').read_text())
    assert len(data)==7894
    assert len({row['istat'] for row in data})==7894
    assert not any(row['sigla']=='SU' for row in data)
    assert all(row['provincia'] for row in data)
