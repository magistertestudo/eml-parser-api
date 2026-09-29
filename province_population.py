"""Rank only observed candidate provinces by the official population snapshot."""
import json
from functools import lru_cache
from pathlib import Path
from province_resolver import Resolution


@lru_cache(maxsize=1)
def populations():
    return json.loads((Path(__file__).parent / 'data/province_population.json').read_text())['populations']


def most_populous(candidates):
    candidates = set(candidates) - {''}
    if not candidates:
        return Resolution(reason='website_not_found')
    if len(candidates) == 1:
        return Resolution(candidates.pop(), 'website_resolved')
    counts = populations()
    # Never silently treat a missing demographic value as zero.
    if any(p not in counts for p in candidates):
        return Resolution(reason='website_population_missing')
    largest = max(counts[p] for p in candidates)
    winners = [p for p in candidates if counts[p] == largest]
    if len(winners) != 1:
        return Resolution(reason='website_population_tie')
    return Resolution(winners[0], 'website_population_fallback')
