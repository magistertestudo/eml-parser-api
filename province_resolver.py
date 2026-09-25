"""Conservative offline resolution: unknown/contradictory locations stay empty."""
import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from province_legacy import PROVINCE


def key(value):
    text = unicodedata.normalize('NFKD', str(value or '')).casefold()
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', ''.join(c for c in text if not unicodedata.combining(c))).split())


@dataclass(frozen=True)
class Resolution:
    name: str = ''
    reason: str = 'not_found'


@lru_cache(maxsize=1)
def indexes():
    rows = json.loads((Path(__file__).parent / 'data/comuni.json').read_text())
    aliases, cities, caps = {}, {}, {}
    for short, full in PROVINCE.items():
        if short == "SU":
            continue  # Abolished: resolve via municipality/CAP, not the former province.
        aliases[key(short)] = full
        aliases[key(full)] = full
    aliases.update({key('Bolzano/Bozen'): 'Bolzano', key("Valle d'Aosta/Vallée d'Aoste"): 'Aosta'})
    for row in rows:
        name = PROVINCE.get(row['sigla'], row['provincia'])
        aliases[key(row['provincia'])] = name
        if row['sigla']:
            aliases[key(row['sigla'])] = name
        for city in (row['comune'], row['alias']):
            if city:
                cities.setdefault(key(city), set()).add(name)
        for cap in row['cap']:
            caps.setdefault(cap, set()).add(name)
    return aliases, cities, caps


def resolve_province(ai):
    country = key(ai.get('Nazione'))
    if country and country not in {'italia', 'italy', 'it', 'ita', 'italien', 'italie'}:
        return Resolution(reason='foreign_country')
    aliases, cities, caps = indexes()
    evidence = []
    explicit = key(re.sub(r'\s*\([A-Za-z]{2}\)\s*$', '', str(ai.get('Provincia') or '')))
    explicit = re.sub(r'^(provincia di|provincia|prov) ', '', explicit)
    if explicit in aliases:
        evidence.append({aliases[explicit]})
    city = key(ai.get('Comune'))
    if city in cities:
        evidence.append(cities[city])
    cap = str(ai.get('CAP') or '').strip()
    if re.fullmatch(r'\d{5}', cap) and cap in caps:
        evidence.append(caps[cap])
    address = str(ai.get('Indirizzo') or '')
    # Only labelled/parenthesized abbreviations: never interpret words like "via" or "di".
    abbreviations = re.findall(r'\(([A-Za-z]{2})\)|\bprov(?:incia)?\.?\s*(?:di\s+)?([A-Za-z]{2})\b', address, re.I)
    found = {aliases[key(a or b)] for a, b in abbreviations if key(a or b) in aliases}
    if found:
        evidence.append(found)
    for address_cap in re.findall(r'(?<!\d)\d{5}(?!\d)', address):
        if address_cap in caps:
            evidence.append(caps[address_cap])
    # Municipality must occur in postal locality position, not in street names (Via Roma).
    postal = re.search(r'(?<!\d)\d{5}\s+(.+)$', address)
    if postal:
        locality = key(postal.group(1))
        matches = [(len(c), provinces) for c, provinces in cities.items()
                   if locality == c or locality.startswith(c + ' ')]
        if matches:
            evidence.append(max(matches, key=lambda item: item[0])[1])
    else:
        # Exact locality or locality after comma; do not scan arbitrary email prose.
        for segment in address.split(','):
            locality = key(segment)
            if locality in cities:
                evidence.append(cities[locality])
            else:
                # A trailing abbreviation is meaningful only after a known municipality.
                match = re.fullmatch(r'(.+?)\s+\(?([A-Z]{2})\)?', segment.strip())
                if match and key(match[1]) in cities and key(match[2]) in aliases:
                    evidence.extend([cities[key(match[1])], {aliases[key(match[2])]}])
    if not evidence:
        return Resolution()
    candidates = set.intersection(*evidence)
    if len(candidates) == 1:
        return Resolution(candidates.pop(), 'resolved')
    return Resolution(reason='conflict' if not candidates else 'ambiguous')
