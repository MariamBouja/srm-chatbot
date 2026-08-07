"""Deterministic agency lookup by region.

Answers are built directly from the structured agencies table
(data/agencies.json, produced by chatbot.scraper.scrape_agencies_table) —
no LLM call — so there is no hallucination risk on addresses/phone-adjacent
data, consistent with the rest of the app's hallucination-prevention design.
"""
import json
import re

from chatbot.config import AGENCIES_DATA_PATH

# The site's own agencies table is inconsistent about casing for the same
# province ("CHTOUKA AIT BAHA" vs "Chtouka ait baha"), and users will type a
# short city name rather than the full administrative province name. This
# maps every accepted spelling/alias to one of the six fixed Souss-Massa
# provinces so both grouping and lookup are reliable regardless of source
# formatting.
_REGION_ALIASES = {
    "AGADIR IDA OUTANANE": "AGADIR IDA OUTANANE",
    "AGADIR": "AGADIR IDA OUTANANE",
    "INEZGANE AIT MELLOUL": "INEZGANE AIT MELLOUL",
    "INEZGANE": "INEZGANE AIT MELLOUL",
    "AIT MELLOUL": "INEZGANE AIT MELLOUL",
    "CHTOUKA AIT BAHA": "CHTOUKA AIT BAHA",
    "CHTOUKA": "CHTOUKA AIT BAHA",
    "TAROUDANT": "TAROUDANT",
    "TIZNIT": "TIZNIT",
    "TATA": "TATA",
}

AGENCY_KEYWORDS = ("agence", "agences")


def _normalize(text):
    return " ".join(text.strip().upper().split())


def _canonicalize(raw_region):
    return _REGION_ALIASES.get(_normalize(raw_region), _normalize(raw_region))


def _display_label(canonical_region):
    return canonical_region.title()


def _load_records():
    if not AGENCIES_DATA_PATH.exists():
        return []
    return json.loads(AGENCIES_DATA_PATH.read_text(encoding="utf-8"))


def _build_index():
    index = {}
    for record in _load_records():
        canonical = _canonicalize(record["region"])
        index.setdefault(canonical, []).append(record)
    return index


_REGION_INDEX = _build_index()


def is_agency_question(text):
    normalized = text.lower()
    return any(keyword in normalized for keyword in AGENCY_KEYWORDS)


def list_regions():
    """Region display labels, sorted alphabetically."""
    return sorted(_display_label(region) for region in _REGION_INDEX)


def match_region(text):
    """Find a known region/city name mentioned in free text.

    Returns the canonical display label, or None if no region is recognized.
    Aliases are checked longest-first so "Inezgane Ait Melloul" wins over
    the shorter "Inezgane" when both would match.
    """
    normalized_text = _normalize(text)

    for alias in sorted(_REGION_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", normalized_text):
            return _display_label(_REGION_ALIASES[alias])

    return None


def agencies_for_region(region_label):
    canonical = _canonicalize(region_label)
    return _REGION_INDEX.get(canonical, [])


def format_region_options_message():
    options = "\n".join(f"• {region}" for region in list_regions())
    return f"Pour quelle région souhaitez-vous connaître les agences ?\n\n{options}"


def format_agency_list(region_label, agencies):
    if not agencies:
        return (
            f"Je n'ai trouvé aucune agence pour la région « {region_label} ».\n\n"
            + format_region_options_message()
        )

    lines = [f"Voici les agences SRM-SM pour la région **{region_label}** :\n"]
    for agency in agencies:
        lines.append(f"• **{agency['agency']}** ({agency['service']}) — {agency['address']}")

    return "\n".join(lines)
