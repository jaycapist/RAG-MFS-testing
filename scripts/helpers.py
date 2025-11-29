import re
import calendar

MISSING_DATES_LOG = "missing_dates.txt"
UNKNOWN_TOKENS_LOG = "unknown_tokens.txt"

CANONICAL_FILE_TYPES = {"resolution", "report", "election", "minutes", "agenda", "motion", "policy", "memorandum", "dashboard", "plan", "charter", "other"}
CANONICAL_STANCE = {"oppose", "endorse", "support", "approve", "accept"}
CANONICAL_STATUS = {"draft", "proposed", "approved", "accepted"}
CANONICAL_ACTION_TYPE = {"request", "recommend"}
CANONICAL_META = {"censuring", "reasserting"}
CANONICAL_TOPIC = {"issue", "review", "plans", "dashboard", "election", "slate", "nomination"}
COMMITTEE_CODES = {"CAB", "CAPP", "CEE", "CFS", "COA", "CON", "COR", "CoRGE", "CPM", "CSA", "GEC", "SEC", "SEN", "MFS"}

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
"report": "report", "minutes": "minutes", "minute": "minutes", "min": "minutes",
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
    (r"(?<!\d)(19|20)\d{2}(0[1-9]|1[0-2])([0-3]\d)(?!\d)", "ymd"), # e.g., 19530328, 20050621
    (r"(?<!\d)(19|20)\d{2}(?!\d)", "year"), # e.g., 2015, 2025
    (r"(?<!\d)(0?[1-9]|1[0-2])[-_](\d{1,2})[-_]((19|20)\d{2})(?!\d)", "mdy"), # e.g., 06-30=2024, 08_24_94
    (r"(?<!\d)(19|20)\d{2}(0[1-9]|1[0-2])(?!\d)", "ym"), # e.g., 202502, 198907
    (r"(?<![A-Za-z])(January|February|March|April|May|June|July|August|September|October|November|December)(?![A-Za-z])", "monthname"), # e.g., April, May
    (r"(?<![A-Za-z])(Spring|Summer|Fall)(?![A-Za-z])", "semester"), # e.g., Fall, Spring
    (r"(?<![A-Za-z])(Fall|Spring|Summer)[-_ ]?(19|20)\d{2}(?!\d)", "sem_year"), # e.g., Fall2019, Summer2018
    (r"(?<!\d)((19|20)\d{2})[-_](\d{2})(?!\d)", "year_range"), # e.g., 2009-12, 2021-24
]

    result = {}

    for pattern, kind in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if not match:
            continue

        if kind == "ymd":
            full = match.group(0)
            year = int(full[0:4])
            month = int(full[4:6])
            day = int(full[6:8])
            month_name = calendar.month_name[month]

            result.setdefault("year", year)
            result.setdefault("months", [month_name])
            result.setdefault("full_date", f"{year}.{month:02}.{day:02}")

        elif kind == "year":
            result.setdefault("year", int(match.group()))

        elif kind == "mdy":
            month = int(match.group(1))
            day = int(match.group(2))
            year = int(match.group(3))
            result.setdefault("year", year)
            result.setdefault("months", [month])
            result.setdefault("full_date", f"{year}.{month:02}.{day:02}")

        elif kind == "ym":
            year = int(match.group(0)[:4])
            month = int(match.group(0)[4:6])
            month_name = calendar.month_name[month]
            result.setdefault("year", year)
            result.setdefault("months", [month_name])

        elif kind == "monthname":
            result.setdefault("months", match.group().capitalize())

        elif kind == "semester":
            semester = match.group().capitalize()
            result.setdefault("semester", semester)
            if semester == "Spring":
                result.setdefault("months", ["January", "February", "March", "April", "May"])
            elif semester == "Summer":
                result.setdefault("months", ["May", "June", "July", "August"])
            elif semester == "Fall":
                result.setdefault("months", ["August", "September", "October", "November", "December"])

        elif kind == "sem_year":
            semester = match.group(1).capitalize()
            year_match = re.search(r"(19|20)\d{2}", match.group(0))
            if year_match:
                result.setdefault("year", int(year_match.group()))
                result.setdefault("semester", semester)
                if semester == "Spring":
                    result.setdefault("months", ["January", "February", "March", "April", "May"])
                elif semester == "Summer":
                    result.setdefault("months", ["May", "June", "July", "August"])
                elif semester == "Fall":
                    result.setdefault("months", ["August", "September", "October", "November", "December"])

        elif kind == "year_range":
            year_start = int(match.group(1))
            year_suffix = int(match.group(3))
            if year_suffix < 100:
                year_end = (year_start // 100) * 100 + year_suffix
                result.setdefault("year_range", f"{year_start}-{year_end}")
        if "month" in result and "semester" not in result:
            month_name = str(result["month"]).capitalize()
            semester_map = {
                "Spring": ["January", "February", "March", "April", "May"],
                "Summer": ["June", "July", "August"],
                "Fall": ["September", "October", "November", "December"]
            }
            for semester, months in semester_map.items():
                if month_name in months:
                    result.setdefault("semester", semester)
                    result.setdefault("months", months)
                    break

    return result

def split_token_by_keywords(token, keyword_map):
    matched = []
    remaining = token
    while remaining:
        for keyword in sorted(keyword_map.keys(), key=len, reverse=True):
            if remaining.startswith(keyword):
                matched.append(keyword)
                remaining = remaining[len(keyword):]
                break
        else:
            matched.append(remaining[0])
            remaining = remaining[1:]
    return [t for t in matched if len(t) > 2 and t in keyword_map]

def extract_semantic_metadata(filename: str):
    metadata = {
        "stance": [],
        "topic": [],
        "meta": [],
        "committee_codes": [],
    }

    raw_tokens = re.findall(r"[a-zA-Z0-9]+", filename.lower())
    tokens = []
    for tok in raw_tokens:
        clean_tok = tok.lower()
        if clean_tok in BODY_OR_COMMITTEE_MAP:
            tokens.append(clean_tok)
            continue

        if clean_tok in FILE_TYPE_KEYWORDS:
            tokens.append(clean_tok)
            continue

        tokens.extend(split_token_by_keywords(clean_tok, FILE_TYPE_KEYWORDS))

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

    for doc in docs:
        metadata = doc.metadata
        filename = metadata.get("source", "")
        date_info = extract_date_from_filename(filename)
        semantic_info = extract_semantic_metadata(filename)

        if not date_info and not semantic_info:
            log_missing(filename)
        elif not date_info:
            log_missing(filename)
        elif not semantic_info:
            log_missing(filename)

        metadata.update(date_info)
        metadata.update(semantic_info)
        doc.metadata = metadata
