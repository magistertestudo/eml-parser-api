"""Offline import: python scripts/update_istat.py official.xlsx existing.json output.json.

Official XLSX contains no postal codes. Preserve CAP only for exact municipality
name matches; new/renamed municipalities remain without CAP pending verification.
"""
import hashlib
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


def build(source, existing):
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(source) as archive:
        strings = [''.join(x.itertext()) for x in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('m:si', ns)]
        rows = []
        for row in ET.fromstring(archive.read('xl/worksheets/sheet1.xml')).findall('.//m:sheetData/m:row', ns):
            values = {}
            for cell in row:
                value = cell.find('m:v', ns)
                text = value.text if value is not None else ''
                values[re.sub(r'\d', '', cell.attrib['r'])] = strings[int(text)] if cell.attrib.get('t') == 's' else text
            rows.append(values)
    assert rows[0]['G'] == 'Denominazione in italiano', 'Unexpected ISTAT schema'
    assert rows[0]['O'] == 'Sigla automobilistica', 'Unexpected ISTAT schema'
    previous = {row['comune']: row for row in existing}
    result = []
    for row in rows[1:]:
        if not row.get('G'):
            continue
        old = previous.get(row['G'], {})
        result.append({'comune': row['G'], 'alias': row.get('H') or None,
                       'sigla': row['O'], 'provincia': row['L'].split('/')[0],
                       'cap': old.get('cap', []), 'istat': row['E']})
    assert len({r['istat'] for r in result}) == len(result)
    return result


if __name__ == '__main__':
    source, existing, output = map(Path, sys.argv[1:])
    result = build(source, json.loads(existing.read_text()))
    output.write_text('[\n' + ',\n'.join('  '+json.dumps(r, ensure_ascii=False) for r in result)+'\n]\n')
    print(json.dumps({'municipalities': len(result), 'missing_cap': [r['comune'] for r in result if not r['cap']],
                      'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}, ensure_ascii=False))
