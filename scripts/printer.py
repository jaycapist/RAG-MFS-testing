import json

def format_answer_with_sources_json(answer: str, docs, preview=150):
    seen = set()
    sources = []

    for d in docs:
        payload = d.payload or {}
        src = payload.get("source", "unknown")
        if src in seen:
            continue
        seen.add(src)

        source_entry = {
            "source": src,
            "link": payload.get("link"),
            "file_type": payload.get("file_type"),

            # Group codes
            "committee_codes": payload.get("committee_codes", []), # list
            "body_code": payload.get("body_code"),

            # Dates
            "full_date": payload.get("full_date"),
            "year": payload.get("year"),
            "semester": payload.get("semester"),
            "month": payload.get("month", []), # list

            # Extra
            "stance": payload.get("stance", []), # list
            "topic": payload.get("topic", []), # list
            "meta": payload.get("meta", []), # list
            "status": payload.get("status"),
            "action_type": payload.get("action_type"),

            "snippet": (
                (payload.get("text") or "")
                .replace("\n", " ")
                .strip()[:preview]
                or None
            ),
        }

        sources.append(source_entry)

    result = {
        "answer": answer.strip(),
        "sources": sources
    }

    print(json.dumps(result, indent=2))
    return result
