import json
import os

from extractor import extract_information
from evaluator import evaluate


INPUT_FOLDER = "inputs"
OUTPUT_FILE = "results.json"


results = []

for filename in os.listdir(INPUT_FOLDER):

    path = os.path.join(INPUT_FOLDER, filename)

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    data = extract_information(text)

    score = evaluate(data)

    result = {
        "file": filename,
        "extracted_data": data,
        "extraction_score": score
    }

    results.append(result)


with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)


print("Results saved in results.json")