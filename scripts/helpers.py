import re
from datetime import datetime
from collections import Counter

def parse_year_window(q: str):
    q = q.lower()
    this = datetime.now().year
    YEAR = r"(?:19|20)\d{2}"

    m = re.search(rf"\b({YEAR})\s*(?:-|–|to)\s*({YEAR})\b", q)
    if m:
        y1, y2 = int(m.group(1)), int(m.group(2))
        return (y1, y2) if y1 <= y2 else (y2, y1)

    yrs = [int(y) for y in re.findall(rf"\b{YEAR}\b", q)]
    if yrs:
        y = max(yrs)
        return y, y

    m = re.search(r"(last|past)\s+(\d+)\s+year", q)
    if m:
        n = int(m.group(2))
        return this - n + 1, this

    if "this year" in q:
        return this, this
    if "last year" in q:
        return this - 1, this - 1
    if "recent" in q:
        return this - 2, this

    return None, None


def add_year_metadata_consistent(docs):
    """
    Adds a 'year' field to each Document's metadata by scanning
    the document text and filename for 4-digit years <= current year.
    """
    current_year = datetime.now().year
    year_pattern = re.compile(r"\b(19\d{2}|20\d{2})\b")

    for doc in docs:
        metadata = doc.metadata
        if "year" in metadata:
            continue

        text = doc.page_content
        source = metadata.get("source", "")

        # Find all years in text
        years_in_text = [int(y) for y in year_pattern.findall(text) if int(y) <= current_year]
        years_in_source = [int(y) for y in year_pattern.findall(source) if int(y) <= current_year]

        if years_in_text:
            most_common_year = Counter(years_in_text).most_common(1)[0][0]
            metadata["year"] = most_common_year
        elif years_in_source:
            metadata["year"] = years_in_source[0]

        doc.metadata = metadata