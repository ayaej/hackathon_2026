import os

# Project Root Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data Directories
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
RAW_DIR = os.getenv("RAW_DIR", os.path.join(DATA_DIR, "raw"))
SILVER_DIR = os.getenv("SILVER_DIR", os.path.join(DATA_DIR, "silver"))
CURATED_DIR = os.getenv("CURATED_DIR", os.path.join(DATA_DIR, "curated"))
PDF_DIR = os.getenv("PDF_DIR", os.path.join(BASE_DIR, "pdf"))

# File Names
DATASET_JSON = os.getenv("DATASET_JSON", os.path.join(BASE_DIR, "dataset.json"))
SIRENE_CSV = os.getenv("SIRENE_CSV", os.path.join(RAW_DIR, "sirene_sample.csv"))
VALIDATION_LOG = os.getenv("VALIDATION_LOG", "validation.log")

# OCR Configuration
POPPLER_PATH = os.getenv("POPPLER_PATH", "")

# Create directories if they don't exist
def init_directories():
    for d in [RAW_DIR, SILVER_DIR, CURATED_DIR, PDF_DIR]:
        os.makedirs(d, exist_ok=True)
