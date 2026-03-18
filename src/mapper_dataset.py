import os
import json
import textwrap

def prepare_raw_dataset(chemin_dataset="dataset.json", dossier_raw="data/raw/"):
    
    if not os.path.exists(chemin_dataset):
        print(f"[ERROR] {chemin_dataset} introuvable.")
        return 0

    os.makedirs(dossier_raw, exist_ok=True)
    
    with open(chemin_dataset, "r", encoding="utf-8") as f:
        factures = json.load(f)

    compteur = 0
    for facture in factures:
        doc_id = facture.get("document_id", f"DOC-{compteur}")
        
        crea = facture.get("creancier", {})
        
        texte_ocr = textwrap.dedent(f"""\
            FACTURE N° {doc_id}
            Date de facturation : {facture.get("date_facturation")}
            Echéance : {facture.get("date_echeance")}
            
            EMETTEUR :
            {crea.get("nom", "")} {crea.get("prenom", "")}
            SIRET : {crea.get("siret", "")}
            TVA : {crea.get("n_tva", "")}
            Adresse : {crea.get("adresse", "")}, {crea.get("code_postal", "")} {crea.get("commune", "")}
            
            MONTANTS :
            Total HT : {facture.get("montant_ht")} €
            TVA : {facture.get("tva")} €
            Total TTC : {facture.get("montant_ttc")} €
        """)
        
        json_a_sauvegarder = {
            "document_id": doc_id,
            "type_document": "facture",
            "texte_ocr": texte_ocr
        }
        
        nom_fichier = f"{doc_id}.json"
        chemin_fichier = os.path.join(dossier_raw, nom_fichier)
        
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(json_a_sauvegarder, f, indent=4, ensure_ascii=False)
            
        compteur += 1

    print(f"[INFO] {compteur} fichiers Raw generes.")
    return compteur

if __name__ == "__main__":
    prepare_raw_dataset("dataset.json", "data/raw/")
