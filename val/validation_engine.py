
import json
from validator import DocumentValidator

with open("sample_data.json") as f:
    data = json.load(f)

validator = DocumentValidator()

result = validator.validate(
    data["facture"],
    data["attestation"]
)

print("\n====== VALIDATION REPORT ======")
print(result)
print("================================")