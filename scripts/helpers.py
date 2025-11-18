import re
from datetime import datetime
from collections import Counter

def extract_date_from_filename(filename: str):
    patterns = [
        (r"\b(19|20)\d{2}(0[1-9]|1[0-2])([0-3]\d)\b", "ymd"),                # 20130924
        (r"\b(19|20)\d{2}\b", "year"),                                       # 2007
        (r"\b(0?[1-9]|1[0-2])[_-](\d{1,2})[_-]((19|20)\d{2})\b", "mdy"),     # 03_24_2005 or 3-24-2005
        (r"\b(19|20)\d{2}(0[1-9]|1[0-2])\b", "ym"),                          # 202404
        (r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b", "monthname"),
        (r"\b(Spring|Summer|Fall)\b", "semester"),
        (r"\b(Fall|Spring|Summer)[-_ ]?(19|20)\d{2}\b", "sem_year"), # Fall2024
    ]

    for pattern, kind in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            if kind == "ymd":
                return {"year": int(match.group(1) + match.group(2) + match.group(3))[:4]}
            if kind == "year":
                return {"year": int(match.group())}
            if kind == "mdy":
                return {"year": int(match.group(3))}
            if kind == "ym":
                return {"year": int(match.group()[:4])}
            if kind == "monthname":
                return {"month": match.group().capitalize()}
            if kind == "semester":
                return {"semester": match.group().capitalize()}
            if kind == "sem_year":
                return {
                    "semester": match.group(1).capitalize(),
                    "year": int(match.group(2) + match.group(3))
                }
    return {}


def enrich_metadata_from_filename(docs):
    year_pattern = re.compile(r"\b(19[0-9]{2}|20[0-2][0-9]|2025)\b")

    for doc in docs:
        text = doc.page_content
        metadata = doc.metadata
        filename = metadata.get("source", "")

        # 1. Try extract from filename
        file_date_info = extract_date_from_filename(filename)
        if file_date_info:
            metadata.update(file_date_info)

        # 2. Fallback: scan document text commented out to see missed date formats
        # years_in_text = re.findall(year_pattern, text)
        # if years_in_text:
            # Use most common year in text
            # most_common_year = Counter(years_in_text).most_common(1)[0][0]
            # metadata.setdefault("year", int(most_common_year))

        # Making a list to see if there are missed date formats
        else:
            log_missing(filename)

        doc.metadata = metadata
