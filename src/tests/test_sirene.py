import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
import json
sys.path.insert(0, ".")

from src.utils.sirene_checker import charger_base, verifier_siren, verifier_siret, detecter_incoherences

charger_base("data/raw/sirene_sample.csv")

res = verifier_siren("000325175")
print(json.dumps(res, indent=2, ensure_ascii=False))

res = verifier_siret("00032517500065")
print(json.dumps(res, indent=2, ensure_ascii=False))

res = verifier_siret("99999999900001")
print(json.dumps(res, indent=2, ensure_ascii=False))

res = detecter_incoherences("00032517500065", "DUPONT & Associes")
print(json.dumps(res, indent=2, ensure_ascii=False))

res = detecter_incoherences("00180725400022", "BRETON")
print(json.dumps(res, indent=2, ensure_ascii=False))

res = detecter_incoherences("00032517500065", "JANOYER")
print(json.dumps(res, indent=2, ensure_ascii=False))
