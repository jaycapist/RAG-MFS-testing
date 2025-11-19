import re
import calendar

MISSING_DATES_LOG = "missing_dates.txt"
UNKNOWN_TOKENS_LOG = "unknown_tokens.txt"

CANONICAL_FILE_TYPES = {"resolution", "report", "election", "minutes", "agenda", "motion", "policy", "memorandum", "dashboard", "plan", "other"}
CANONICAL_STANCE = {"oppose", "endorse", "support", "approve", "accept"}
CANONICAL_STATUS = {"draft", "proposed", "approved", "accepted"}
CANONICAL_ACTION_TYPE = {"request", "recommend"}
CANONICAL_META = {"censuring", "reasserting"}
CANONICAL_TOPIC = {"issue", "review", "plans", "dashboard", "election", "slate", "nomination"}
COMMITTEE_CODES = {"CAB", "CAPP", "CEE", "CFS", "COA", "CON", "COR", "CoRGE", "CPM", "CSA", "GEC", "SEC", "SEN"}

STANCE_MAP = {
"oppose": "oppose", "opposed": "oppose", "opposing": "oppose",
"endorse": "endorse", "endorsing": "endorse", "endorsed": "endorse", "endosing": "endorse",
"support": "support", "supporting": "support", "supported": "support",
"approve": "approve", "approved": "approve", "approval": "approve",
"accept": "accept", "accepted": "accept", "acceptance": "accept",
}

STATUS_MAP = {
"draft": "draft",
"proposal": "proposed", "proposed": "proposed",
"approved": "approved", "adopted": "approved",
"accepted": "accepted", "acceptance": "accepted",
}

META_MAP = {
"censure": "censuring", "censuring": "censuring", "censur": "censuring",
"reassert": "reasserting", "reasserting": "reasserting", "reassurting": "reasserting",
}

TOPIC_MAP = {
"issue": "issue", "issues": "issue",
"review": "review", "reviews": "review",
"plan": "plans", "plans": "plans", "planning": "plans",
"dashboard": "dashboard", "dashboards": "dashboard",
"election": "election", "elections": "election",
"slate": "slate", "slates": "slate",
"nomination": "nomination", "nominations": "nomination",
}

BODY_OR_COMMITTEE_MAP = {k.lower(): k for k in COMMITTEE_CODES}

FILE_TYPE_KEYWORDS = {
"resolution": "resolution", "reso": "resolution", "res": "resolution",
"report": "report", "minutes": "minutes", "minute": "minutes",
"agenda": "agenda", "election": "election", "ballot": "election",
"motion": "motion", "policy": "policy", "memo": "memorandum",
"memorandum": "memorandum", "dashboard": "dashboard",
"plan": "plan", "plans": "plan",
}

ACTION_TYPE_MAP = {
"request": "request", "requesting": "request", "requests": "request",
"recommend": "recommend", "recommends": "recommend",
"recommending": "recommend", "recommendation": "recommend",
}

def extract_date_from_filename(filename: str):
    patterns = [
        (r"\b(19|20)\d{2}(0[1-9]|1[0-2])([0-3]\d)\b", "ymd"),  # 20250526
        (r"\b(19|20)\d{2}\b", "year"),                         # 2007
        (r"\b(0?[1-9]|1[0-2])[_-](\d{1,2})[_-]((19|20)\d{2})\b", "mdy"),  # 03-24-2005
        (r"\b(19|20)\d{2}(0[1-9]|1[0-2])\b", "ym"),            # 202404
        (r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b", "monthname"), # April
        (r"\b(Spring|Summer|Fall)\b", "semester"), # Fall
        (r"\b(Fall|Spring|Summer)[-_ ]?(19|20)\d{2}\b", "sem_year"), # Fall2024
    ]

    result = {}

    for pattern, kind in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if not match:
            continue

        if kind == "ymd":
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            month_name = calendar.month_name[month]
            result.setdefault("year", year)
            result.setdefault("month", month_name)
            result.setdefault("full_date", f"{year}.{month:02}.{day:02}")

        elif kind == "year":
            result.setdefault("year", int(match.group()))

        elif kind == "mdy":
            month = int(match.group(1))
            day = int(match.group(2))
            year = int(match.group(3))
            result.setdefault("year", year)
            result.setdefault("month", month)
            result.setdefault("full_date", f"{year}.{month:02}.{day:02}")

        elif kind == "ym":
            year = int(match.group(0)[:4])
            month = int(match.group(0)[4:6])
            month_name = calendar.month_name[month]
            result.setdefault("year", year)
            result.setdefault("month", month_name)

        elif kind == "monthname":
            result.setdefault("month", match.group().capitalize())

        elif kind == "semester":
            result.setdefault("semester", match.group().capitalize())

        elif kind == "sem_year":
            semester = match.group(1).capitalize()
            year_match = re.search(r"(19|20)\d{2}", match.group(0))
            if year_match:
                result.setdefault("year", int(year_match.group()))
                result.setdefault("semester", semester)

    return result

def extract_semantic_metadata(filename: str):
    metadata = {
        "stance": [],
        "topic": [],
        "meta": [],
        "committee_codes": [],
    }

    tokens = re.findall(r"[a-zA-Z0-9]+", filename.lower())
    seen = set()

    for tok in tokens:
        if tok in seen:
            continue
        seen.add(tok)

        if tok in STANCE_MAP:
            metadata["stance"].append(STANCE_MAP[tok])

        if tok in STATUS_MAP:
            metadata["status"] = STATUS_MAP[tok]

        if tok in META_MAP:
            metadata["meta"].append(META_MAP[tok])

        if tok in TOPIC_MAP:
            metadata["topic"].append(TOPIC_MAP[tok])

        if tok in BODY_OR_COMMITTEE_MAP:
            code = BODY_OR_COMMITTEE_MAP[tok]

            metadata.setdefault("body_code", code)

            if code not in metadata["committee_codes"]:
                metadata["committee_codes"].append(code)

        if tok in FILE_TYPE_KEYWORDS:
            metadata["file_type"] = FILE_TYPE_KEYWORDS[tok]

        if tok in ACTION_TYPE_MAP:
            metadata["action_type"] = ACTION_TYPE_MAP[tok]

        if (
            tok not in STANCE_MAP
            and tok not in STATUS_MAP
            and tok not in META_MAP
            and tok not in TOPIC_MAP
            and tok not in BODY_OR_COMMITTEE_MAP
            and tok not in FILE_TYPE_KEYWORDS
            and tok not in ACTION_TYPE_MAP
        ):
            with open(UNKNOWN_TOKENS_LOG, "a", encoding="utf-8") as f:
                f.write(tok + "\n")

    return metadata


def log_missing(filename):
    """Append filename to missing_dates.txt"""
    try:
        with open(MISSING_DATES_LOG, "a+", encoding="utf-8") as f:
            f.seek(0)
            existing = set(line.strip() for line in f if line.strip())
            if filename not in existing:
                f.write(filename + "\n")
    except Exception as e:
        print(f"Failed to write to `missing_date.txt`: {e}")

def enrich_metadata_from_filename(docs):
    year_pattern = re.compile(r"\b(19[0-9]{2}|20[0-2][0-9]|2025)\b")

    for doc in docs:
        text = doc.page_content
        metadata = doc.metadata
        filename = metadata.get("source", "")
        date_info = extract_date_from_filename(filename)
        semantic_info = extract_semantic_metadata(filename)

        file_date_info = extract_date_from_filename(filename)
        if not date_info or not semantic_info:
            metadata = doc.metadata

        filename = metadata.get("source", "")
        date_info = extract_date_from_filename(filename)
        semantic_info = extract_semantic_metadata(filename)

        if not date_info:
            log_missing(filename)
        if not semantic_info:
            log_missing(filename)
        metadata.update(date_info)
        metadata.update(semantic_info)
        doc.metadata = metadata
