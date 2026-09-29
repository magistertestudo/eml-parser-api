from urllib.parse import parse_qs
import httpx
import pytest
from pcloud_oauth import exchange, save_token
from pcloud_client import PCloudError


def test_exchange_keeps_credentials_in_https_body():
    def handler(request):
        assert request.method == 'POST'
        assert str(request.url) == 'https://api.pcloud.com/oauth2_token'
        assert parse_qs(request.content.decode())['code'] == ['test-code']
        return httpx.Response(200, json={'result': 0, 'access_token': 'test-token'})
    assert exchange('test-code', 'test-secret', httpx.MockTransport(handler)) == 'test-token'


def test_exchange_redacts_provider_error():
    transport = httpx.MockTransport(lambda r: httpx.Response(
        200, json={'result': 2000, 'error': 'test-secret'}))
    with pytest.raises(PCloudError) as caught:
        exchange('test-code', 'test-secret', transport)
    assert 'test-secret' not in str(caught.value)
    assert '2000' in str(caught.value)


def test_token_file_is_private_and_never_overwritten(tmp_path):
    path = tmp_path / 'secret'
    save_token(path, 'test-token')
    assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        save_token(path, 'replacement')
    assert 'replacement' not in path.read_text()
