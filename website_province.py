"""Conservative, bounded fallback to the contact's own public HTTPS website."""
import http.client
import ipaddress
import logging
import os
import re
import socket
import ssl
import time
from email.utils import parseaddr
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from province_resolver import Resolution, indexes, key, resolve_province

# Provider brands are blocked across country TLDs (e.g. yahoo.it/co.uk).
PROVIDER_BRANDS = set('''gmail googlemail outlook hotmail live msn yahoo ymail rocketmail
 aol aim icloud me mac proton protonmail pm tutanota tuta tutamail tuta-mail
 gmx mail email zoho zohomail fastmail hey hushmail mailfence mailbox posteo
 libero virgilio alice tim tin tiscali fastwebnet iol inwind wind kataweb
 interfree emailit supereva excite katamail poste postecert pec arubapec
 legalmail registerpec pecmail mypec laposte orange wanadoo free sfr neuf
 bouyguestelecom t-online web freenet qq 163 126 139 sina sohu yeah yandex
 rambler mailinator guerrillamail yopmail tempmail 10minutemail dispostable
 outlook-email btinternet btopenworld blueyonder virginmedia ntlworld talktalk sky
 comcast verizon att sbcglobal bellsouth cox charter earthlink roadrunner icloud
 bluewin sunrise hispeed quicknet seznam centrum abv wp onet o2 interia ukr
 bigpond optusnet telstra iinet uol bol terra globo rediffmail naver daum hanmail
 orangeemail yahooemail inbox mailnesia getnada sharklasers trashmail'''.split())
RESERVED = {'example.com', 'example.org', 'example.net'}
MAX_BYTES = 512_000
LOG = logging.getLogger(__name__)


def contact_domain(email):
    address = parseaddr(str(email or ''))[1]
    if address.count('@') != 1:
        return ''
    try:
        domain = address.rsplit('@', 1)[1].rstrip('.').encode('idna').decode().lower()
    except UnicodeError:
        return ''
    labels = domain.split('.')
    extra = {x.strip().lower() for x in os.getenv('PROVINCE_EXCLUDED_DOMAINS', '').split(',') if x.strip()}
    if (len(labels) < 2 or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', x) for x in labels)
            or any(x in PROVIDER_BRANDS for x in labels[:-1])
            or labels[-1] in {'invalid', 'test', 'localhost', 'local', 'internal', 'example'}
            or any(domain == x or domain.endswith('.' + x) for x in RESERVED | extra)):
        return ''
    try:
        ipaddress.ip_address(domain)
        return ''
    except ValueError:
        return domain


def allowed_url(url, domain):
    try:
        p = urlsplit(url)
        return (p.scheme == 'https' and p.hostname in {domain, 'www.' + domain}
                and p.port in {None, 443} and not p.username and not p.password)
    except ValueError:
        return False


class PublicHTTPS(http.client.HTTPSConnection):
    """Connect to a validated IP once; retain hostname for TLS and Host header."""
    def connect(self):
        addresses = socket.getaddrinfo(self.host, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
            raise ValueError('Non-public destination')
        family, kind, proto, _, sockaddr = addresses[0]
        sock = socket.socket(family, kind, proto)
        try:
            sock.settimeout(self.timeout)
            sock.connect(sockaddr)
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except Exception:
            sock.close()
            raise


def fetch_page(url, domain, deadline):
    for _ in range(3):
        if not allowed_url(url, domain) or time.monotonic() >= deadline:
            return None
        p = urlsplit(url)
        connection = PublicHTTPS(p.hostname, timeout=min(3, max(.1, deadline-time.monotonic())),
                                 context=ssl.create_default_context())
        try:
            connection.request('GET', p.path or '/', headers={
                'User-Agent': 'EML-Parser/2.1 (contact address lookup)',
                'Accept': 'text/html', 'Accept-Encoding': 'identity'})
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                url = urljoin(url, response.getheader('Location', ''))
                continue
            if response.status != 200 or 'text/html' not in response.getheader('Content-Type', '').lower():
                return None
            chunks, size = [], 0
            while time.monotonic() < deadline:
                chunk = response.read1(min(16384, MAX_BYTES + 1 - size))
                if not chunk:
                    return url, b''.join(chunks)
                chunks.append(chunk)
                size += len(chunk)
                if size > MAX_BYTES:
                    return None
            return None
        finally:
            connection.close()
    return None


def page_provinces(soup):
    # Use actual postal localities, never arbitrary city mentions or street names.
    for node in soup(['script', 'style', 'noscript', 'nav', 'header']):
        node.decompose()
    return text_provinces(' '.join(soup.stripped_strings))


def text_provinces(text):
    _, cities, _ = indexes()
    found = set()
    for match in re.finditer(r'(?<!\d)(\d{5})\s+([^\d]{2,100})', text):
        locality = key(match[2])
        matches = [city for city in cities if locality == city or locality.startswith(city + ' ')]
        if not matches:
            continue
        city = max(matches, key=len)
        result = resolve_province({'Comune': city, 'CAP': match[1]})
        if result.name:
            found.add(result.name)
        else:
            # Conflicting postcode/locality must prevent assigning another location.
            found.add('')
    return found


# A legal-office label applies only until the next office label, never to a
# later operational branch. Combined legal/operational offices are supported.
OFFICE_LABEL = re.compile(
    r"\b(?:sede\s+(?:legale(?:\s+(?:e|ed)\s+(?:operativa|amministrativa))?"
    r"|operativa|amministrativa|commerciale|secondaria|produttiva)"
    r"|(?:registered|legal|head|branch)\s+office|stabilimento|filiale)\b", re.I)
LEGAL_LABEL = re.compile(r"\b(?:sede\s+legale|(?:registered|legal)\s+office)\b", re.I)


def registered_office_provinces(soup):
    for node in soup(['script', 'style', 'noscript', 'nav', 'header']):
        node.decompose()
    text = ' '.join(soup.stripped_strings)
    labels = list(OFFICE_LABEL.finditer(text))
    found = set()
    for i, label in enumerate(labels):
        if not LEGAL_LABEL.search(label[0]):
            continue
        end = labels[i + 1].start() if i + 1 < len(labels) else len(text)
        # Bounded context avoids assigning distant addresses to a bare label.
        candidates = text_provinces(text[label.end():min(end, label.end() + 500)])
        found.update(candidates or {''})
    return found


def website_province(email, fetcher=None):
    domain = contact_domain(email)
    if not domain:
        return Resolution(reason='website_domain_excluded')
    fetcher = fetcher or fetch_page
    deadline = time.monotonic() + 12
    queue = ['https://' + domain + '/', 'https://www.' + domain + '/']
    seen, provinces, legal_provinces = set(), set(), set()
    pages = 0
    while queue and pages < 4 and time.monotonic() < deadline:
        url = queue.pop(0)
        if url in seen or not allowed_url(url, domain):
            continue
        seen.add(url)
        pages += 1
        try:
            page = fetcher(url, domain, deadline)
        except (OSError, ValueError, http.client.HTTPException):
            continue
        if not page:
            continue
        final_url, html = page
        seen.add(final_url)
        soup = BeautifulSoup(html, 'html.parser')
        # Only follow contact/location/about links found on this same site.
        links = []
        for a in soup.find_all('a', href=True):
            try:
                target = urljoin(final_url, a['href']).split('#', 1)[0]
                label = key(a.get_text(' ', strip=True) + ' ' + urlsplit(target).path)
            except ValueError:
                continue
            if re.search(r'\b(contatti|contatto|contact|contacts|sedi|sede|dove siamo|chi siamo|about)\b', label):
                if allowed_url(target, domain) and target not in seen:
                    links.append(target)
        queue = list(dict.fromkeys(links + queue))
        legal_provinces.update(registered_office_provinces(soup))
        provinces.update(page_provinces(soup))
    if legal_provinces:
        if len(legal_provinces) == 1 and '' not in legal_provinces:
            return Resolution(legal_provinces.pop(), 'website_registered_office')
        return Resolution(reason='website_registered_office_conflict')
    if len(provinces) == 1 and '' not in provinces:
        return Resolution(provinces.pop(), 'website_resolved')
    return Resolution(reason='website_conflict' if provinces else 'website_not_found')


def fallback_province(ai, sender=''):
    existing = resolve_province(ai)
    if existing.name or existing.reason != 'not_found' or os.getenv('PROVINCE_WEBSITE_ENABLED', 'true').lower() != 'true':
        return existing
    # An explicit contact email wins, including a provider address: never switch
    # to the sender (which may be the forwarding employee) to evade exclusion.
    return website_province(ai.get('Email') or sender)
