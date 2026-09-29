"""Offline import: python scripts/update_population.py official-p2-2025.zip.
Aggregate official municipality population using our current ISTAT geography.
"""
import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from province_resolver import key
from province_legacy import PROVINCE


def build(source):
    geo = json.loads((ROOT / 'data/comuni.json').read_text())
    bycode = {r['istat']: r for r in geo}
    byname = {}
    for r in geo:
        byname.setdefault(key(r['comune']), []).append(r)
    merged = {'024027': '024129', '024071': '024129', '018082': '018094'}
    populations = Counter()
    seen = set()
    with zipfile.ZipFile(source) as archive:
        text = archive.read('P2_2025_it_Comuni.csv').decode('utf-8-sig')
    assert '31 dicembre 2025' in text.splitlines()[0]
    for row in csv.DictReader(io.StringIO(text.split('\n', 1)[1]), delimiter=';'):
        code = row['Codice comune']
        if not re.fullmatch(r'\d{6}', code or ''):
            continue  # ISTAT explanatory footer.
        assert code not in seen, code
        seen.add(code)
        match = bycode.get(merged.get(code, code))
        if not match:
            assert code[:3] in {'090', '091', '092', '095', '111'}, code
            matches = [r for r in byname.get(key(row['Comune']), [])
                       if r['istat'][:3] in {'112','113','114','115','116','117','118','119'}]
            assert len(matches) == 1, row['Comune']
            match = matches[0]  # Sardinian municipality recoding.
        population = int(row['Popolazione al 31 dicembre - Totale'])
        assert population >= 0
        populations[PROVINCE.get(match['sigla'], match['provincia'])] += population
    assert len(seen) == 7896
    expected = {PROVINCE.get(r['sigla'], r['provincia']) for r in geo}
    assert set(populations) == expected
    return {'reference_date': '2025-12-31', 'status': 'provisional',
            'source': 'https://demo.istat.it/data/p2/P2_2025_it_Comuni.zip',
            'source_sha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(),
            'municipalities': len(seen), 'total_population': sum(populations.values()),
            'populations': dict(sorted(populations.items()))}


if __name__ == '__main__':
    result = build(sys.argv[1])
    (ROOT / 'data/province_population.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print({k:v for k,v in result.items() if k != 'populations'})
    print('Province:', len(result['populations']))
