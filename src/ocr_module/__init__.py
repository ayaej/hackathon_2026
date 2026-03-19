from .extractor import extraire_texte
from .parser import extraire_infos_cles
from .classifier import classifier_document
from .evaluator import evaluate_global

__all__ = [
    "extraire_texte",
    "extraire_infos_cles",
    "classifier_document",
    "evaluate_global",
]