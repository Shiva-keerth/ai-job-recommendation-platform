import re
import pandas as pd


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_skill_vocab_from_jobs(csv_path: str) -> set:
    df = pd.read_csv(csv_path).fillna("")
    vocab = set()

    for skills in df["skills"]:
        parts = re.split(r"[,\|;/\n]+", str(skills).lower())
        for p in parts:
            skill = p.strip()
            if skill and len(skill) > 2:
                vocab.add(skill)

    return vocab


def extract_skills(resume_text: str, vocab: set) -> set:
    resume_clean = clean_text(resume_text)

    found = set()

    for skill in vocab:
        skill_clean = clean_text(skill)

        # match full phrase
        pattern = r"\b" + re.escape(skill_clean) + r"\b"
        if re.search(pattern, resume_clean):
            found.add(skill_clean)

    return found
