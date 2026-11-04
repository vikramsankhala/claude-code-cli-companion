"""Automatic metadata: language, document type, tags and a suggested classification.
Rules are transparent and testable; swap in an LLM classifier (stretch goal) when rules run out."""
import re

LANG_WORDS = {
    "en": {"the", "and", "must", "with", "for", "employees", "policy", "of"},
    "de": {"der", "die", "und", "das", "mit", "für", "nicht", "vertrag", "ist"},
    "fr": {"le", "la", "les", "et", "des", "pour", "avec", "contrat", "est"},
    "es": {"el", "los", "las", "y", "para", "con", "contrato", "es", "del"},
}
TYPE_WORDS = {
    "contract": {"contract", "agreement", "vertrag", "contrat", "contrato", "termination", "kündigung"},
    "invoice": {"invoice", "rechnung", "facture", "factura", "amount due"},
    "hr-record": {"salary", "payroll", "gehalt", "salaire", "appraisal"},
    "policy": {"policy", "richtlinie", "politique", "must", "mandatory"},
    "guide": {"how to", "step", "install", "setup", "anleitung", "guide"},
}
TAG_WORDS = {"security": {"vpn", "mfa", "password", "security"}, "travel": {"travel", "reise", "voyage"},
             "privacy": {"gdpr", "dpdp", "personal data", "datenschutz"}, "finance": {"invoice", "expense", "budget"}}
SENSITIVE = {"salary", "payroll", "gehalt", "salaire", "bank account", "passport", "medical", "confidential"}


def _words(text):
    return re.findall(r"[\wäöüßéèàçñ]+", text.lower())


def detect_language(text: str) -> str:
    words = _words(text)
    scores = {lang: sum(w in vocab for w in words) for lang, vocab in LANG_WORDS.items()}
    return max(scores, key=scores.get) if any(scores.values()) else "und"


def classify(text: str, filename: str = "") -> dict:
    low = (filename + " " + text).lower()
    def hits(vocab):
        return sum(low.count(v) for v in vocab)
    doc_type = max(TYPE_WORDS, key=lambda t: hits(TYPE_WORDS[t]))
    if hits(TYPE_WORDS[doc_type]) == 0:
        doc_type = "general"
    tags = sorted(t for t, vocab in TAG_WORDS.items() if hits(vocab))
    classification = "confidential" if hits(SENSITIVE) or doc_type in {"contract", "hr-record"} else "internal"
    title = next((l.lstrip("# ").strip() for l in text.splitlines() if l.strip()), filename)[:120]
    return {"language": detect_language(text), "doc_type": doc_type, "tags": tags,
            "classification": classification, "title": title}
