import os
import json
import easyocr
import tempfile
from datetime import datetime
from PIL import Image, ImageOps, ImageEnhance
import PyPDF2
from pdf2image import convert_from_path
from docx import Document
from src.ocr_module.parser import extraire_infos_cles
from src.ocr_module.classifier import classifier_document

reader = easyocr.Reader(['fr'], gpu=False)


def pretraiter_image(chemin):
    """Prétraite l'image pour améliorer l'OCR et retourne le chemin d'un fichier temporaire."""
    with Image.open(chemin) as img:
        # Conversion en niveaux de gris
        img = ImageOps.grayscale(img)
        # Augmentation du contraste
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        # Augmentation de la netteté
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)
        
        # Utilisation de tempfile pour un nom unique et sécurisé
        fd, tmp_path = tempfile.mkstemp(suffix=".png", prefix="preprocessed_")
        os.close(fd) # On ferme le descripteur, PIL s'occupera d'ouvrir le fichier par son chemin
        img.save(tmp_path)
        return tmp_path


def lire_image(chemin):
    """Lit le texte d'une image après prétraitement."""
    tmp = pretraiter_image(chemin)
    try:
        resultats = reader.readtext(tmp, detail=0)
        return " ".join(resultats)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def lire_pdf_numerique(chemin):
    """Extrait le texte d'un PDF natif (non scanné)."""
    texte = ""
    with open(chemin, "rb") as f:
        lecteur = PyPDF2.PdfReader(f)
        for page in lecteur.pages:
            texte += page.extract_text() or ""
    return texte.strip()


def lire_pdf_scanne(chemin):
    """Convertit un PDF scanné en images puis effectue l'OCR sur chaque page."""
    poppler_path = os.environ.get("POPPLER_PATH", None)
    if poppler_path and not os.path.isdir(poppler_path):
        poppler_path = None

    pages = convert_from_path(chemin, dpi=300, poppler_path=poppler_path)
    texte_total = []

    for page in pages:
        # Utilisation de tempfile pour chaque page
        fd, tmp_path = tempfile.mkstemp(suffix=".png", prefix="ocr_page_")
        os.close(fd)
        try:
            page.save(tmp_path, "PNG")
            texte_total.append(lire_image(tmp_path))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return "\n".join(texte_total).strip()


def lire_docx(chemin):
    """Extrait le texte d'un fichier DOCX."""
    doc = Document(chemin)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def extraire_texte(chemin_fichier):
    """Fonction principale d'extraction de texte selon l'extension du fichier."""
    extension = os.path.splitext(chemin_fichier)[1].lower()

    if extension in (".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"):
        return lire_image(chemin_fichier)

    elif extension == ".pdf":
        texte = lire_pdf_numerique(chemin_fichier)
        if len(texte) < 50:
            texte = lire_pdf_scanne(chemin_fichier)
        return texte

    elif extension == ".docx":
        return lire_docx(chemin_fichier)

    else:
        raise ValueError(f"Format non supporte : {extension}")
    

def traiter_json_brut(chemin_json, chemin_sortie):
    """Traite un JSON contenant du texte OCR pour extraire les données structurées."""
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