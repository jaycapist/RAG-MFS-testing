import re
from datetime import datetime

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
    year_pattern = re.compile(r"(19|20)\d{2}")
    for doc in docs:
        source = doc.metadata.get("source", "")
        match = year_pattern.search(source)
        if match:
            doc.metadata["year"] = int(match.group(0))
