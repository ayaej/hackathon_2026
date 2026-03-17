import json
import os

from extractor import extract_information
from evaluator import evaluate

INPUT_FOLDER = "inputs"
OUTPUT_FOLDER = "outputs"
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "results.json")


results = []

for filename in os.listdir(INPUT_FOLDER):

    print("Processing:", filename)

    path = os.path.join(INPUT_FOLDER, filename)

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    data = extract_information(text)
    score = evaluate(data)

    results.append({
        "file": filename,
        "extracted_data": data,
        "extraction_score": score
    })

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("DONE → results.json created")