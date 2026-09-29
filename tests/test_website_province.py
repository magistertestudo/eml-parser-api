import socket
from bs4 import BeautifulSoup
import pytest
import website_province as w


@pytest.mark.parametrize('email', ['a@gmail.com', 'a@outlook.it', 'a@yahoo.co.uk',
    'a@libero.it', 'a@icloud.com', 'a@proton.me', 'a@pec.it', 'a@arubapec.it',
    'a@tiscali.it', 'a@hotmail.fr', 'a@127.0.0.1', 'a@example.invalid', '', 'garbage'])
def test_excluded_without_network(email):
    assert w.website_province(email, lambda *a: pytest.fail('Network on excluded domain')).name == ''


def test_custom_domain_and_exclusion(monkeypatch):
    assert w.contact_domain('Mario <mario@azienda-demo.it>') == 'azienda-demo.it'
    monkeypatch.setenv('PROVINCE_EXCLUDED_DOMAINS', 'azienda-demo.it')
    assert not w.contact_domain('a@azienda-demo.it')


def test_only_same_website():
    for url in ['https://evil.it/', 'https://azienda-demo.it.evil.it/',
                'http://azienda-demo.it/', 'https://azienda-demo.it:123/',
                'https://user@azienda-demo.it/', 'file:///etc/passwd']:
        assert not w.allowed_url(url, 'azienda-demo.it')
    assert w.allowed_url('https://www.azienda-demo.it/contatti', 'azienda-demo.it')


def page(text):
    return BeautifulSoup(text, 'html.parser')


def test_postal_addresses_and_no_street_guess():
    assert w.page_provinces(page('<footer>Via Roma 10<br>50019 <b>Sesto Fiorentino</b> (FI)</footer>')) == {'Firenze'}
    assert w.page_provinces(page('<p>Via Roma 10. Operiamo a Milano e Firenze</p>')) == set()
    assert w.page_provinces(page('<p>50019 Milano</p>')) == {''}
    assert w.page_provinces(page('<script>50019 Sesto Fiorentino</script>')) == set()


def test_contact_page_and_ambiguity():
    calls = []
    def fetch(url, *_):
        calls.append(url)
        return url, ('<a href="/contatti">Contatti</a><footer>50019 Sesto Fiorentino (FI)</footer>'
                     if url.endswith('/') else '<address>20121 Milano (MI)</address>')
    assert w.website_province('a@azienda-demo.it', fetch).name == 'Milano'
    assert 'https://azienda-demo.it/contatti' in calls
    assert len(calls) <= 4


def test_success_no_email_content_sent():
    def fetch(url, domain, deadline):
        assert '@' not in url and domain == 'azienda-demo.it'
        return url, '<footer>Via Roma 10, 50019 Sesto Fiorentino (FI)</footer>'
    assert w.website_province('mario@azienda-demo.it', fetch).name == 'Firenze'


def test_network_failure_is_optional():
    def fetch(*args):
        raise socket.timeout()
    assert w.website_province('mario@azienda-demo.it', fetch).name == ''


@pytest.mark.parametrize('ai', [{'Provincia':'MI'}, {'Nazione':'France'},
    {'Comune':'Milano', 'Provincia':'FI'}])
def test_existing_foreign_or_conflicting_not_overwritten(monkeypatch, ai):
    monkeypatch.setattr(w, 'website_province', lambda *a: pytest.fail('Unexpected website lookup'))
    assert w.fallback_province(ai) == w.resolve_province(ai)


def test_provider_contact_does_not_use_forwarder(monkeypatch):
    monkeypatch.setattr(w, 'fetch_page', lambda *a: pytest.fail('Unexpected lookup'))
    assert not w.fallback_province({'Email':'a@gmail.com'}, 'b@azienda-demo.it').name


def test_private_dns_is_blocked(monkeypatch):
    monkeypatch.setattr(w.socket, 'getaddrinfo', lambda *a, **kw: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 443))])
    with pytest.raises(ValueError, match='Non-public'):
        w.PublicHTTPS('azienda-demo.it').connect()


def test_pipeline_uses_website_result(monkeypatch):
    import main
    from email.message import EmailMessage
    monkeypatch.setattr(main, 'ask_gpt', lambda *a: {'Email':'a@azienda-demo.it'})
    monkeypatch.setattr(w, 'website_province', lambda *a: w.Resolution('Firenze', 'website_resolved'))
    msg = EmailMessage()
    msg['From'] = 'a@azienda-demo.it'
    msg.set_content('Richiesta preventivo, senza indirizzo')
    assert main.process_email(msg.as_bytes(), 'test.eml', '2026 1')['Provincia'] == 'Firenze'


def test_malformed_site_link_does_not_abort_extraction():
    def fetch(url, *_):
        return url, '<a href="https://[invalid">Contatti</a><footer>50019 Sesto Fiorentino</footer>'
    assert w.website_province('a@azienda-demo.it', fetch).name == 'Firenze'


@pytest.mark.parametrize('label', ['Sede legale', 'SEDE LEGALE E OPERATIVA', 'Registered office'])
def test_legal_office_wins_over_operational_branch(label):
    def fetch(url, *_):
        return url, f'<h2>{label}</h2><p>Via Roma 1, 50019 Sesto Fiorentino (FI)</p><h2>Sede operativa</h2><p>20121 Milano</p>'
    result = w.website_province('a@azienda-demo.it', fetch)
    assert result.name == 'Firenze'
    assert result.reason == 'website_registered_office'


def test_legal_office_found_on_contact_page():
    def fetch(url, *_):
        return url, ('<a href="/contatti">Contatti</a><p>Sede operativa: 20121 Milano</p>'
                     if url.endswith('/') else '<p>Sede legale: Via Roma 1<br>50019 Sesto Fiorentino</p>')
    assert w.website_province('a@azienda-demo.it', fetch).name == 'Firenze'


def test_conflicting_legal_offices_on_different_pages():
    def fetch(url, *_):
        return url, ('<a href="/contatti">Contatti</a><p>Sede legale: 20121 Milano</p>'
                     if url.endswith('/') else '<p>Sede legale: 50019 Sesto Fiorentino</p>')
    result = w.website_province('a@azienda-demo.it', fetch)
    assert result.name == 'Milano'
    assert result.reason == 'website_population_fallback'


@pytest.mark.parametrize('html', [
    '<p>Sede legale: indirizzo non disponibile</p><h2>Sede operativa</h2><p>20121 Milano</p>',
    '<p>Sede legale: 50019 Milano</p><p>Filiale: 20121 Milano</p>',
    '<p>Sede legale: 50019 Sesto Fiorentino; 20121 Milano</p>',
])
def test_unresolved_legal_office_uses_observed_provinces(html):
    assert w.website_province('a@azienda-demo.it', lambda url,*_: (url,html)).name == 'Milano'
