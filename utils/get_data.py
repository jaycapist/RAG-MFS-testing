import json
from bs4 import BeautifulSoup
import re

# ------------------------
# Utility functions from simplify_nq_example
# ------------------------
def get_nq_tokens(simplified_nq_example):
    if "document_text" not in simplified_nq_example:
        raise ValueError("`get_nq_tokens` should be called on a simplified NQ example with `document_text`.")
    return simplified_nq_example["document_text"].split(" ")

def simplify_nq_example(nq_example):
    def _clean_token(token):
        return re.sub(u" ", "_", token["token"])

    text = " ".join([_clean_token(t) for t in nq_example["document_tokens"]])

    def _remove_html_byte_offsets(span):
        span = dict(span)  # copy
        span.pop("start_byte", None)
        span.pop("end_byte", None)
        return span

    def _clean_annotation(annotation):
        annotation["long_answer"] = _remove_html_byte_offsets(annotation["long_answer"])
        annotation["short_answers"] = [_remove_html_byte_offsets(sa) for sa in annotation["short_answers"]]
        return annotation

    simplified_nq_example = {
        "question_text": nq_example["question_text"],
        "example_id": nq_example["example_id"],
        "document_url": nq_example["document_url"],
        "document_text": text,
        "long_answer_candidates": [_remove_html_byte_offsets(c) for c in nq_example["long_answer_candidates"]],
        "annotations": [_clean_annotation(a) for a in nq_example["annotations"]]
    }

    if len(get_nq_tokens(simplified_nq_example)) != len(nq_example["document_tokens"]):
        raise ValueError("Incorrect number of tokens.")

    return simplified_nq_example

# ------------------------
# Main function
# ------------------------
def get_data(lines_to_read=5):
    file_path='./data/natural_questions.jsonl'
    data = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= lines_to_read:
                break
            try:
                obj = json.loads(line)
                data.append(obj)
            except json.JSONDecodeError as e:
                print(f"Skipping line {i} due to JSON error: {e}")

    document_texts = []
    qna_pairs = []

    for item in data:
        simplified = simplify_nq_example(item)
        doc_text = simplified["document_text"]
        document_texts.append(doc_text)

        # Extract top-level long answer spans as text
        top_level_answers = []
        tokens = get_nq_tokens(simplified)
        for candidate in simplified["long_answer_candidates"]:
            if candidate.get("top_level", False):
                start = candidate["start_token"]
                end = candidate["end_token"]
                answer_text = " ".join(tokens[start:end])
                top_level_answers.append(answer_text)

        qna_pairs.append({
            "question": simplified["question_text"],
            "answer": top_level_answers
        })

    return document_texts, qna_pairs

# ------------------------
# Example usage:
# ------------------------
# document_texts, qna_list = get_simplified_qna()
# print(document_texts[0])
# print(qna_list[0])
