import os
import json
import easyocr
import re
from datetime import datetime

reader = easyocr.Reader(['fr'], gpu=False)


def lire_image(chemin):
    resultats = reader.readtext(chemin, detail=0)
    return " ".join(resultats)


def lire_pdf_numerique(chemin):
    try:
        import PyPDF2
    except ImportError:
        raise ImportError("PyPDF2 n'est pas installe. Lance : pip install PyPDF2")

    texte = ""
    with open(chemin, "rb") as f:
        lecteur = PyPDF2.PdfReader(f)
        for page in lecteur.pages:
            texte += page.extract_text() or ""
    return texte.strip()


def lire_pdf_scanne(chemin):
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError(
            "pdf2image n'est pas installe. Lance : pip install pdf2image\n"
            "Installe aussi Poppler (Windows) : https://github.com/oschwartz10612/poppler-windows/releases"
        )

    pages = convert_from_path(chemin, dpi=300)
    texte_total = ""
    for i, page in enumerate(pages):
        chemin_tmp = f"_tmp_page_{i}.png"
        page.save(chemin_tmp, "PNG")
        texte_total += lire_image(chemin_tmp) + "\n"
        os.remove(chemin_tmp)
    return texte_total.strip()


def lire_docx(chemin):
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx n'est pas installe. Lance : pip install python-docx")

    doc = Document(chemin)
    paragraphes = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphes)


def extraire_texte(chemin_fichier):
    if not os.path.exists(chemin_fichier):
        raise FileNotFoundError(f"Fichier introuvable : {chemin_fichier}")

    extension = os.path.splitext(chemin_fichier)[1].lower()
    print(f"Lecture : {chemin_fichier} ({extension})")

    try:
        if extension in (".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"):
            return lire_image(chemin_fichier)

        elif extension == ".pdf":
            texte = lire_pdf_numerique(chemin_fichier)
            if len(texte) < 50:
                print("PDF numerique trop court, on passe en OCR scanne...")
                texte = lire_pdf_scanne(chemin_fichier)
            return texte

        elif extension == ".docx":
            return lire_docx(chemin_fichier)

        else:
            raise ValueError(f"Format non supporte : {extension}")

    except Exception as e:
        return f"Erreur lors de la lecture : {str(e)}"


def traiter_json_brut(chemin_json, chemin_sortie):
    from src.ocr_module.parser import extraire_infos_cles
    from src.ocr_module.classifier import classifier_document

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"Fichier introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        entree = json.load(f)

    texte = entree.get("texte_ocr", "")
    if not texte:
        raise ValueError("Le champ 'texte_ocr' est absent ou vide dans le JSON.")

    print(f"Traitement JSON : {chemin_json}")

    donnees = extraire_infos_cles(texte)

    champs_fournis = {k: v for k, v in entree.items() if k != "texte_ocr"}
    donnees["extraction"].update({k: v for k, v in champs_fournis.items() if v is not None})

    type_doc = entree.get("type_document") or classifier_document(texte)

    donnees["meta"] = {
        "fichier_source": os.path.basename(chemin_json),
        "document_id": entree.get("document_id"),
        "type_document": type_doc,
        "date_traitement": datetime.now().isoformat(),
        "statut": "succes"
    }

    dossier_sortie = os.path.dirname(chemin_sortie)
    if dossier_sortie:
        os.makedirs(dossier_sortie, exist_ok=True)

    with open(chemin_sortie, "w", encoding="utf-8") as f:
        json.dump(donnees, f, indent=4, ensure_ascii=False)

    print(f"Sauvegarde : {chemin_sortie}")
    return donnees


def traiter_document(chemin_fichier, chemin_sortie):
    from src.ocr_module.parser import extraire_infos_cles
    from src.ocr_module.classifier import classifier_document

    print(f"Traitement de : {chemin_fichier}")

    texte = extraire_texte(chemin_fichier)
    donnees = extraire_infos_cles(texte)
    type_doc = classifier_document(texte)

    donnees["meta"] = {
        "fichier_source": os.path.basename(chemin_fichier),
        "type_document": type_doc,
        "date_traitement": datetime.now().isoformat(),
        "statut": "succes" if "Erreur" not in texte else "echec_partiel"
    }

    dossier_sortie = os.path.dirname(chemin_sortie)
    if dossier_sortie:
        os.makedirs(dossier_sortie, exist_ok=True)

    with open(chemin_sortie, "w", encoding="utf-8") as f:
        json.dump(donnees, f, indent=4, ensure_ascii=False)

    print(f"Sauvegarde : {chemin_sortie}")
    return donnees


if __name__ == "__main__":
    fichier_test = "data/raw/exemple_facture.jpg"

    if os.path.exists(fichier_test):
        traiter_document(fichier_test, "data/silver/resultat_test.json")
    else:
        print(f"Pas de fichier a '{fichier_test}'.")
        print("Mets un document dans data/raw/ pour tester.")