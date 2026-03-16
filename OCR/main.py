import json
from extractor import extract_information
from evaluator import evaluate


def process_text(text):

    extracted = extract_information(text)

    score = evaluate(extracted)

    result = {
        "ocr_text": text,
        "extracted_data": extracted,
        "ocr_score": score
    }

    return result


if __name__ == "__main__":

    with open("texte_brut.txt", "r") as f:
        text = f.read()

    result = process_text(text)

    print(json.dumps(result, indent=4))