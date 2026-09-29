import json
from pathlib import Path
import province_population as p
from province_resolver import indexes


def test_population_is_province_not_capital():
    # Florence city is larger than Bergamo city, but Bergamo province is larger.
    assert p.most_populous({'Firenze','Bergamo'}).name == 'Bergamo'
    assert p.most_populous({'Milano','Roma'}).name == 'Roma'


def test_only_observed_provinces_are_candidates():
    assert p.most_populous({'Firenze','Como',''}).name == 'Firenze'
    assert not p.most_populous({''}).name
    assert p.most_populous({'Como',''}).name == 'Como'


def test_missing_population_and_ties(monkeypatch):
    monkeypatch.setattr(p, 'populations', lambda: {'A':10,'B':10})
    assert p.most_populous({'A','B'}).reason == 'website_population_tie'
    assert p.most_populous({'A','C'}).reason == 'website_population_missing'


def test_all_current_provinces_have_population():
    _, cities, _ = indexes()
    current = set().union(*cities.values())
    assert current <= set(p.populations())
    assert all(v > 0 for v in p.populations().values())
    data=json.loads((Path(__file__).resolve().parents[1]/'data/province_population.json').read_text())
    assert data['municipalities'] == 7896
    assert sum(p.populations().values()) == data['total_population']
