import re
from datetime import datetime

def parse_year_window(q: str):
    q = q.lower()
    this = datetime.now().year
    YEAR = r"(?:19|20)\d{2}"

    # Match ranges like "2010-2015"
    m = re.search(rf"\b({YEAR})\s*(?:-|–|to)\s*({YEAR})\b", q)
    if m:
        y1, y2 = int(m.group(1)), int(m.group(2))
        return (y1, y2) if y1 <= y2 else (y2, y1)

    # Match single years like "2023"
    yrs = [int(y) for y in re.findall(rf"\b{YEAR}\b", q)]
    if yrs:
        y = max(yrs)
        return y, y

    # Match "last 5 years" etc.
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
    both the text content and the source path for years.
    """
    year_pattern = re.compile(r"\b(19[0-9]{2}|20[0-2][0-9]|2025)\b")

    for doc in docs:
        text = doc.page_content
        metadata = doc.metadata

        # Look for year
        source = metadata.get("source", "")
        match_text = year_pattern.search(text)
        match_source = year_pattern.search(source)

        # Add year
        if match_text:
            metadata["year"] = int(match_text.group())
        elif match_source:
            metadata["year"] = int(match_source.group())

        doc.metadata = metadata
