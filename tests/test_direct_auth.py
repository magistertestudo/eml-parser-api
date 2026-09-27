from urllib.parse import parse_qs
import stat
import httpx
import pytest
from pcloud_client import Settings, PCloudClient, PCloudError
from pcloud_login import acquire_token, save_token, verify_folder


def test_direct_request_and_hidden_repr():
    settings = Settings('secret', 'api.pcloud.com', 29662386698, 'direct')
    assert 'secret' not in repr(settings)
    def handle(request):
        assert 'secret' not in str(request.url)
        assert parse_qs(request.content.decode()) == {'auth':['secret']}
        return httpx.Response(200,json={'result':0})
    with PCloudClient(settings,httpx.MockTransport(handle)) as client:
        client.call('userinfo',{})


def test_env_direct(monkeypatch):
    for k,v in {'PCLOUD_ENABLED':'true','PCLOUD_AUTH_TYPE':'direct','PCLOUD_AUTH_TOKEN':'direct-secret','PCLOUD_ACCESS_TOKEN':'oauth-secret','PCLOUD_LINK_MODE':'upload_request'}.items():
        monkeypatch.setenv(k,v)
    assert Settings.from_env().token == 'direct-secret'
    monkeypatch.delenv('PCLOUD_AUTH_TOKEN')
    with pytest.raises(PCloudError): Settings.from_env()


def test_login_uses_https_body():
    def handle(request):
        params=parse_qs(request.content.decode())
        assert request.url == 'https://api.pcloud.com/userinfo'
        assert params['password']==['password-secret']
        assert params['getauth']==['1']
        assert params['authexpire']==['2592000']
        return httpx.Response(200,json={'result':0,'auth':'token-secret'})
    assert acquire_token('user@example.org','password-secret',httpx.MockTransport(handle))=='token-secret'


@pytest.mark.parametrize('response',[{'result':2000,'error':'password-secret'}, {'result':0}, {'result':0,'auth':'bad\nvalue'}])
def test_login_failure_redacts(response):
    with pytest.raises(PCloudError) as exc:
        acquire_token('user@example.org','password-secret',httpx.MockTransport(lambda r:httpx.Response(200,json=response)))
    assert 'password-secret' not in str(exc.value)


def test_token_private_and_no_overwrite(tmp_path):
    path=tmp_path/'.env.pcloud.secret'
    save_token(path,'token-secret')
    assert stat.S_IMODE(path.stat().st_mode)==0o600
    assert 'PCLOUD_AUTH_TOKEN=token-secret' in path.read_text()
    with pytest.raises(FileExistsError): save_token(path,'replacement')


def test_verify_folder_without_writes():
    def handle(request):
        assert request.url.path=='/listfolder'
        assert parse_qs(request.content.decode())['auth']==['token-secret']
        return httpx.Response(200,json={'result':0,'metadata':{'folderid':29662386698,'isfolder':True,'ismine':True}})
    verify_folder('token-secret',httpx.MockTransport(handle))
