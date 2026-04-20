# -*- coding: utf-8 -*-
import re
import math
import hashlib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    JOBS_CSV, CORE_SKILLS_N, SOFT_SKILL_WEIGHT,
    WEIGHT_CORE, WEIGHT_SECONDARY, WEIGHT_TFIDF,
    WEIGHT_EXPERIENCE, WEIGHT_PROJECTS, WEIGHT_CERTS,
    OPTIMISTIC_BOOST, ATS_BASE_PENALTY, ATS_MISS_PENALTY, ATS_CORE_PENALTY,
    EXPERIENCE_LEVEL_MAP, TOP_N_PRIMARY, TOP_N_OTHER,
)
from modules.category_detector import detect_category, detect_full_category
from modules.skill_extractor import build_skill_vocab_from_jobs, extract_skills
from modules.jobs_store import get_open_jobs

# safety check — if detect_full_category failed to import, define it inline
try:
    detect_full_category
except NameError:
    def detect_full_category(text: str) -> dict:
        parent = detect_category(text)
        return {"parent": parent, "sub": "", "label": parent}


# ── Soft skills ────────────────────────────────────────────────────────────────
SOFT_SKILLS = {
    "communication", "teamwork", "leadership", "problem solving", "problem-solving",
    "critical thinking", "attention to detail", "time management", "customer focus",
    "adaptability", "storytelling", "presentation", "stakeholder management",
    "ownership", "mentorship", "empathy", "creativity",
}

# ── Skill alias map ────────────────────────────────────────────────────────────
SKILL_ALIASES: dict[str, str] = {
    "scikit-learn":           "scikit learn",
    "sklearn":                "scikit learn",
    "k-means":                "k means",
    "k means clustering":     "k means",
    "kmeans":                 "k means",
    "llm fine-tuning":        "llm fine tuning",
    "llm finetuning":         "llm fine tuning",
    "fine tuning":            "llm fine tuning",
    "ci/cd":                  "ci cd",
    "node.js":                "node js",
    "nodejs":                 "node js",
    "powerbi":                "power bi",
    "random forests":         "random forest",
    "decision trees":         "decision tree",
    "jupyter notebook":       "jupyter",
    "jupyter notebooks":      "jupyter",
    "feature engg":           "feature engineering",
    "feature engg.":          "feature engineering",
    "data viz":               "data visualization",
    "dl":                     "deep learning",
    "natural language processing": "nlp",
    "a/b testing":            "ab testing",
    "a b testing":            "ab testing",
    "git/github":             "git",
    "github":                 "git",
    "postgresql":             "sql",
    "mysql":                  "sql",
    "postgres":               "sql",
    "icd-10":                 "icd 10",
    "p&l management":         "p l management",
    "gd&t":                   "gd t",
    "matplotlb":              "matplotlib",
}

# ── Certification domain keywords ─────────────────────────────────────────────
CERT_DOMAIN_KEYWORDS: dict[str, list] = {
    "data & analytics":       ["data", "analytics", "analyst", "bi", "sql", "python", "tableau",
                                "power bi", "excel", "machine learning", "ai", "ml", "deloitte",
                                "google data", "ibm data"],
    "software engineering":   ["software", "developer", "java", "python", "cloud", "aws", "azure",
                                "gcp", "docker", "kubernetes", "devops", "system design"],
    "human resources":        ["hr", "human resource", "people", "shrm", "recruitment", "talent"],
    "finance & accounting":   ["finance", "accounting", "cfa", "cpa", "financial", "bloomberg"],
    "marketing & sales":      ["marketing", "seo", "google ads", "hubspot", "salesforce", "crm",
                                "digital marketing", "content"],
    "healthcare":             ["healthcare", "medical", "clinical", "nursing", "hipaa", "icd"],
    "operations & supply chain": ["operations", "supply chain", "logistics", "lean", "six sigma",
                                   "scm", "erp"],
    "mechanical & manufacturing": ["mechanical", "manufacturing", "cad", "autocad", "solidworks",
                                    "lean", "six sigma", "quality"],
}

# ── Project domain keywords ───────────────────────────────────────────────────
PROJECT_DOMAIN_KEYWORDS: dict[str, list] = {
    "data & analytics":       ["data", "analytics", "eda", "dashboard", "kpi", "visualization",
                                "machine learning", "ml", "prediction", "model", "dataset",
                                "regression", "classification", "clustering", "nlp", "deep learning",
                                "neural", "streamlit", "tableau", "power bi", "sql", "python",
                                "pandas", "numpy", "scikit", "tensorflow", "pytorch", "analysis",
                                "forecast", "insight", "report"],
    "software engineering":   ["app", "application", "web", "api", "backend", "frontend",
                                "microservice", "database", "system", "platform", "tool",
                                "automation", "script", "bot", "deploy", "docker", "cloud"],
    "human resources":        ["hr", "employee", "recruitment", "people", "payroll", "attendance",
                                "performance review", "hiring"],
    "finance & accounting":   ["finance", "stock", "trading", "portfolio", "budget", "invoice",
                                "accounting", "financial", "revenue", "cost"],
    "marketing & sales":      ["marketing", "campaign", "seo", "ad", "customer", "sales",
                                "funnel", "conversion", "social media", "content"],
    "healthcare":             ["health", "medical", "patient", "hospital", "clinical", "drug",
                                "disease", "diagnosis", "wellness"],
    "operations & supply chain": ["supply", "inventory", "logistics", "warehouse", "procurement",
                                   "demand", "forecast", "erp", "operations"],
    "mechanical & manufacturing": ["mechanical", "design", "cad", "manufacturing", "product",
                                    "simulation", "testing", "quality", "robot"],
}


# ══════════════════════════════════════════════════════════════════════════════
# SKILL NORMALIZATION
# ══════════════════════════════════════════════════════════════════════════════

def _normalize_skill(skill: str) -> str:
    s = skill.lower().strip()
    if s in SKILL_ALIASES:
        return SKILL_ALIASES[s]
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s in SKILL_ALIASES:
        return SKILL_ALIASES[s]
    return s


def _split_skills(skills_text: str) -> list:
    if not skills_text:
        return []
    parts = re.split(r"[,\|;/\n]+", str(skills_text).lower())
    seen, result = set(), []
    for p in parts:
        norm = _normalize_skill(p)
        if norm and norm not in seen:
            seen.add(norm)
            result.append(norm)
    return result


def _is_soft(skill: str) -> bool:
    return skill.strip().lower() in SOFT_SKILLS


def _normalize_resume_skills(resume_skills: set) -> set:
    normalized = set()
    for skill in resume_skills:
        normalized.add(_normalize_skill(skill))
        plain = re.sub(r"[^a-z0-9\s]", " ", skill.lower().strip())
        plain = re.sub(r"\s+", " ", plain).strip()
        if plain:
            normalized.add(plain)
    return normalized


def _auto_core_secondary(required: list, core_n: int = CORE_SKILLS_N):
    hard = [s for s in required if not _is_soft(s)]
    soft = [s for s in required if _is_soft(s)]
    core = hard[:core_n]
    secondary = hard[core_n:] + soft
    return core, secondary


def _stable_jitter(job_id) -> float:
    s = str(job_id).encode("utf-8")
    h = hashlib.md5(s).hexdigest()
    return (int(h[:6], 16) % 1000) / 1_000_000.0


# ══════════════════════════════════════════════════════════════════════════════
# RESUME SECTION EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def _extract_resume_experience_years(resume_text: str) -> int:
    """
    Estimate candidate's years of experience from resume text.
    Checks explicit mentions first, then date ranges, then fresher keywords.
    Returns 0 for freshers/students.
    """
    text = resume_text.lower()

    # Pattern 1: "3 years of experience", "2+ years exp"
    explicit = re.findall(r"(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)", text)
    if explicit:
        return max(int(y) for y in explicit)

    # Pattern 2: date ranges like "Jan 2021 - Dec 2023" or "2020 – 2022"
    year_ranges = re.findall(r"\b(20\d{2})\b.*?\b(20\d{2}|present|current)\b", text)
    if year_ranges:
        total = 0
        for start, end in year_ranges:
            s = int(start)
            e = 2025 if end in ("present", "current") else int(end)
            if 2000 <= s <= 2025 and s <= e:
                total += (e - s)
        if total > 0:
            return min(total, 30)

    # Pattern 3: fresher / student keywords → 0 years
    fresher_kws = ["fresher", "student", "b.tech", "b.e.", "pursuing", "expected", "internship"]
    if any(kw in text for kw in fresher_kws):
        return 0

    return 0


def _extract_section(resume_text: str, section_headers: list, stop_headers: list) -> str:
    """Generic section extractor — finds first matching header and extracts until next section."""
    text = resume_text.lower()
    start_idx = -1
    for hdr in section_headers:
        idx = text.find(hdr)
        if idx != -1:
            start_idx = idx
            break
    if start_idx == -1:
        return ""
    end_idx = len(text)
    for hdr in stop_headers:
        idx = text.find(hdr, start_idx + 1)
        if idx != -1 and idx < end_idx:
            end_idx = idx
    return text[start_idx:end_idx]


def _get_project_text(resume_text: str) -> str:
    return _extract_section(
        resume_text,
        ["technical projects", "projects", "personal projects", "academic projects", "key projects"],
        ["certifications", "education", "experience", "skills", "awards", "references"],
    ) or resume_text.lower()


def _get_cert_text(resume_text: str) -> str:
    return _extract_section(
        resume_text,
        ["certifications", "certificates", "courses", "training"],
        ["education", "projects", "skills", "experience", "awards", "references"],
    )


# ══════════════════════════════════════════════════════════════════════════════
# BONUS SIGNAL SCORING
# ══════════════════════════════════════════════════════════════════════════════

def _score_experience(resume_years: int, job_exp_level: str, job_req_years) -> float:
    """
    Score experience match between candidate and job.
    Returns 0.0–1.0.
    - Meets or slightly exceeds requirement  → 1.0
    - Over-qualified                         → 0.70–0.85
    - Under by 1 year                        → 0.60
    - Under by 2 years                       → 0.35
    - Under by 3+ years                      → 0.10
    - No info available                      → 0.50
    """
    try:
        req_years = int(float(str(job_req_years)))
    except (ValueError, TypeError):
        req_years = None

    level       = str(job_exp_level).strip().lower()
    level_range = EXPERIENCE_LEVEL_MAP.get(level)

    if req_years is not None:
        diff = resume_years - req_years
        if diff >= 0:
            if diff <= 2:   return 1.0
            elif diff <= 4: return 0.85
            else:           return 0.70
        else:
            gap = abs(diff)
            if gap == 1:   return 0.60
            elif gap == 2: return 0.35
            else:          return 0.10

    if level_range is not None:
        lo, hi = level_range
        if lo <= resume_years <= hi:
            return 1.0
        elif resume_years > hi:
            return max(0.70, 1.0 - (resume_years - hi) * 0.05)
        else:
            gap = lo - resume_years
            if gap == 1:   return 0.60
            elif gap == 2: return 0.35
            else:          return 0.10

    return 0.50


def _score_projects(resume_text: str, job_category: str) -> float:
    """
    Score project relevance to the job category using keyword matching.
    Uses sqrt curve so partial matches still get decent credit.
    Returns 0.0–1.0.
    """
    project_text = _get_project_text(resume_text)
    category_key = str(job_category).strip().lower()
    keywords     = PROJECT_DOMAIN_KEYWORDS.get(category_key, [])

    if not keywords:
        return 0.50

    matched   = sum(1 for kw in keywords if kw in project_text)
    raw_ratio = matched / len(keywords)
    return min(math.sqrt(raw_ratio), 1.0)


def _score_certifications(resume_text: str, job_category: str) -> float:
    """
    Score certification relevance to the job category.
    Returns 0.0–1.0.
    - No certs section         → 0.0
    - Certs but irrelevant     → 0.10
    - Partially relevant       → 0.60
    - Relevant                 → 0.85
    - Highly relevant          → 1.0
    """
    cert_text    = _get_cert_text(resume_text)
    if not cert_text:
        return 0.0

    category_key = str(job_category).strip().lower()
    keywords     = CERT_DOMAIN_KEYWORDS.get(category_key, [])

    if not keywords:
        return 0.30

    matched = sum(1 for kw in keywords if kw in cert_text)
    if matched == 0:   return 0.10
    elif matched <= 2: return 0.60
    elif matched <= 4: return 0.85
    else:              return 1.0


# ══════════════════════════════════════════════════════════════════════════════
# TF-IDF SIMILARITY
# ══════════════════════════════════════════════════════════════════════════════

def _build_resume_doc(resume_text: str, resume_skills: set) -> str:
    skills_text = " ".join(sorted(resume_skills))
    return f"{resume_text.lower()} {skills_text} {skills_text}".strip()


def _build_tfidf_similarity(jobs_df: pd.DataFrame, resume_text: str, resume_skills: set) -> list:
    job_docs = []
    for _, r in jobs_df.iterrows():
        title    = str(r.get("job_title", ""))
        skills   = " ".join(_split_skills(r.get("skills", "")))
        desc     = str(r.get("job_description", ""))
        industry = str(r.get("industry", ""))
        category = str(r.get("category", ""))
        doc = f"{title} {skills} {skills} {desc} {industry} {category}".strip().lower()
        job_docs.append(doc)

    resume_doc = _build_resume_doc(resume_text, resume_skills)
    corpus     = job_docs + [resume_doc]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )
    tfidf = vectorizer.fit_transform(corpus)
    sims  = cosine_similarity(tfidf[-1], tfidf[:-1]).flatten()
    return sims.tolist()


# ══════════════════════════════════════════════════════════════════════════════
# CORE SKILL SCORING
# ══════════════════════════════════════════════════════════════════════════════

def _weighted_fraction(skills: list, resume_skills: set, soft_weight: float = SOFT_SKILL_WEIGHT) -> float:
    if not skills:
        return 0.0
    def w(s): return soft_weight if _is_soft(s) else 1.0
    total = sum(w(s) for s in skills)
    if total <= 0:
        return 0.0
    return sum(w(s) for s in skills if s in resume_skills) / total


def _score_one_job(required: list, resume_skills: set) -> dict:
    core, secondary = _auto_core_secondary(required)
    req_set         = set(required)
    core_set        = set(core)
    secondary_set   = set(secondary)

    return {
        "matched_skills":    sorted(req_set & resume_skills),
        "missing_skills":    sorted(req_set - resume_skills),
        "matched_core":      sorted(core_set & resume_skills),
        "missing_core":      sorted(core_set - resume_skills),
        "matched_secondary": sorted(secondary_set & resume_skills),
        "missing_secondary": sorted(secondary_set - resume_skills),
        "core_match":        float(_weighted_fraction(core, resume_skills)),
        "secondary_match":   float(_weighted_fraction(secondary, resume_skills)),
        "core_count":        len(core),
        "missing_core_count":len(core_set - resume_skills),
    }


# ══════════════════════════════════════════════════════════════════════════════
# FINAL SCORE COMPUTATION
# ══════════════════════════════════════════════════════════════════════════════

def _compute_final_scores(
    core_match, secondary_match, tfidf_sim,
    missing_core_count, core_count,
    exp_score, project_score, cert_score,
):
    """
    Compute recruiter, optimistic, and ATS scores using all six signals.

    Weights (from config.py):
      WEIGHT_CORE        = 0.60  — hard skill overlap (most important)
      WEIGHT_SECONDARY   = 0.13  — secondary skills + soft skills
      WEIGHT_TFIDF       = 0.09  — semantic similarity
      WEIGHT_EXPERIENCE  = 0.08  — experience level / years match
      WEIGHT_PROJECTS    = 0.06  — project domain relevance
      WEIGHT_CERTS       = 0.04  — certification relevance
    """
    tfidf_sim       = max(min(float(tfidf_sim),       1.0), 0.0)
    core_match      = max(min(float(core_match),      1.0), 0.0)
    secondary_match = max(min(float(secondary_match), 1.0), 0.0)
    exp_score       = max(min(float(exp_score),       1.0), 0.0)
    project_score   = max(min(float(project_score),   1.0), 0.0)
    cert_score      = max(min(float(cert_score),      1.0), 0.0)

    recruiter = (
        WEIGHT_CORE      * core_match      +
        WEIGHT_SECONDARY * secondary_match +
        WEIGHT_TFIDF     * tfidf_sim       +
        WEIGHT_EXPERIENCE * exp_score      +
        WEIGHT_PROJECTS  * project_score   +
        WEIGHT_CERTS     * cert_score
    )

    optimistic = min(recruiter + OPTIMISTIC_BOOST, 1.0)

    miss_ratio = (missing_core_count / core_count) if core_count > 0 else 1.0
    ats = max(
        recruiter
        - ATS_BASE_PENALTY
        - (ATS_MISS_PENALTY * miss_ratio)
        - (ATS_CORE_PENALTY * (1 - core_match)),
        0.0,
    )

    return recruiter, optimistic, ats


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SCORING LOOP
# ══════════════════════════════════════════════════════════════════════════════

def _score_jobs(
    jobs_df: pd.DataFrame,
    resume_text: str,
    resume_skills: set,
    resume_years: int,
) -> pd.DataFrame:
    jobs_df       = jobs_df.reset_index(drop=True).copy()
    resume_skills = _normalize_resume_skills(resume_skills)
    sims          = _build_tfidf_similarity(jobs_df, resume_text, resume_skills)

    rows = []
    for i, row in jobs_df.iterrows():
        required = _split_skills(row.get("skills", ""))
        s        = _score_one_job(required, resume_skills)

        job_category  = str(row.get("category", ""))
        job_exp_level = str(row.get("experience_level", ""))
        job_req_years = row.get("required_experience_years", "")

        exp_score     = _score_experience(resume_years, job_exp_level, job_req_years)
        project_score = _score_projects(resume_text, job_category)
        cert_score    = _score_certifications(resume_text, job_category)

        recruiter, optimistic, ats = _compute_final_scores(
            core_match         = s["core_match"],
            secondary_match    = s["secondary_match"],
            tfidf_sim          = float(sims[i]),
            missing_core_count = int(s["missing_core_count"]),
            core_count         = int(s["core_count"]),
            exp_score          = exp_score,
            project_score      = project_score,
            cert_score         = cert_score,
        )

        jid    = row.get("job_id", i + 1)
        jitter = _stable_jitter(jid)
        recruiter  = max(min(recruiter  + jitter, 1.0), 0.0)
        optimistic = max(min(optimistic + jitter, 1.0), 0.0)
        ats        = max(min(ats        + jitter, 1.0), 0.0)

        rows.append({
            "job_id":                    jid,
            "job_title":                 row.get("job_title", ""),
            "category":                  row.get("category", "General"),
            "industry":                  row.get("industry", ""),
            "company":                   row.get("company", "Demo Company"),
            "company_size":              row.get("company_size", ""),
            "location":                  row.get("location", ""),
            "work_mode":                 row.get("work_mode", ""),
            "experience_level":          row.get("experience_level", ""),
            "required_experience_years": row.get("required_experience_years", ""),
            "salary_range":              row.get("salary_range", ""),
            "posted_date":               row.get("posted_date", ""),
            "match_recruiter":           float(recruiter),
            "match_optimistic":          float(optimistic),
            "match_ats":                 float(ats),
            "match_score":               float(recruiter),
            "matched_skills":            s["matched_skills"],
            "missing_skills":            s["missing_skills"],
            "matched_core":              s["matched_core"],
            "missing_core":              s["missing_core"],
            "matched_secondary":         s["matched_secondary"],
            "missing_secondary":         s["missing_secondary"],
            # Breakdown for UI display
            "core_match":                round(s["core_match"] * 100, 1),
            "secondary_match":           round(s["secondary_match"] * 100, 1),
            "experience_score":          round(exp_score * 100, 1),
            "project_score":             round(project_score * 100, 1),
            "cert_score":                round(cert_score * 100, 1),
        })

    df = pd.DataFrame(rows)
    return df.sort_values("match_recruiter", ascending=False).reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def match_resume_to_jobs(
    resume_text: str,
    csv_path: str = None,
    top_n_primary: int = TOP_N_PRIMARY,
    top_n_other: int = TOP_N_OTHER,
    include_db_jobs: bool = True,
):
    """
    Main entry point. Match a resume against all jobs and return:
      primary_results  — top matches in candidate's detected category
      other_results    — top matches outside their category
      resume_skills    — list of extracted + normalized skills
      resume_category  — detected category (e.g. 'Data & Analytics')
    """
    if csv_path is None:
        csv_path = str(JOBS_CSV)

    # ── Load CSV jobs ─────────────────────────────────────────────────────────
    jobs_csv = pd.read_csv(csv_path).fillna("")
    jobs_csv["job_source"]     = "csv"
    jobs_csv["employer_email"] = ""
    if "job_id" not in jobs_csv.columns:
        jobs_csv["job_id"] = [f"csv_{i+1}" for i in range(len(jobs_csv))]
    else:
        jobs_csv["job_id"] = jobs_csv["job_id"].astype(str).apply(lambda x: f"csv_{x}")

    # ── Load DB jobs ──────────────────────────────────────────────────────────
    jobs_db = pd.DataFrame()
    if include_db_jobs:
        try:
            db_rows = get_open_jobs()
            if db_rows:
                jobs_db = pd.DataFrame([dict(r) for r in db_rows]).fillna("")
                if "company" not in jobs_db.columns:
                    jobs_db["company"] = "Employer Posted"
                jobs_db["job_source"]     = "db"
                jobs_db["employer_email"] = jobs_db.get("employer_email", "")
                jobs_db["job_id"] = jobs_db["job_id"].astype(str).apply(lambda x: f"db_{x}")
        except Exception:
            jobs_db = pd.DataFrame()

    jobs = pd.concat([jobs_csv, jobs_db], ignore_index=True).fillna("")

    # ── Parse resume ──────────────────────────────────────────────────────────
    full_cat           = detect_full_category(resume_text)
    resume_category    = full_cat["parent"]
    resume_subcategory = full_cat["sub"]
    resume_cat_label   = full_cat["label"]
    vocab              = build_skill_vocab_from_jobs(csv_path)
    resume_skills   = extract_skills(resume_text, vocab)
    resume_skills   = _normalize_resume_skills(resume_skills)
    resume_years    = _extract_resume_experience_years(resume_text)

    # ── Split primary vs other jobs ───────────────────────────────────────────
    if "category" in jobs.columns and resume_category != "General":
        # The CSV uses abbreviated subcategory names (e.g. "Data Science & ML")
        # that differ from both the parent names and the detector's full subcategory names.
        # Explicit mapping → parent is the most reliable approach.
        _CSV_CAT_TO_PARENT = {
            # Software Engineering
            "AI & ML Engineering":            "Software Engineering",
            "Backend & Full Stack":           "Software Engineering",
            "DevOps & Cloud":                 "Software Engineering",
            "Frontend & Mobile":              "Software Engineering",
            "Automation & Robotics":          "Mechanical & Manufacturing",
            # Data & Analytics
            "Data Science & ML":              "Data & Analytics",
            "Data Engineering & BI":          "Data & Analytics",
            "Business & Product Analytics":   "Data & Analytics",
            # Finance & Accounting
            "Accounting & Audit":             "Finance & Accounting",
            "Financial Planning & Risk":      "Finance & Accounting",
            "Treasury & Compliance":          "Finance & Accounting",
            # Marketing & Sales
            "Digital Marketing":              "Marketing & Sales",
            "Brand & Content":                "Marketing & Sales",
            "Sales & CRM":                    "Marketing & Sales",
            # Human Resources
            "HR Operations & Analytics":      "Human Resources",
            "HR Business Partnering":         "Human Resources",
            "Talent & Recruitment":           "Human Resources",
            # Healthcare
            "Clinical & Medical":             "Healthcare",
            "Health IT & Informatics":        "Healthcare",
            "Public Health & Administration": "Healthcare",
            "Pharma & Life Sciences":         "Healthcare",
            # Operations & Supply Chain
            "Supply Chain & Procurement":     "Operations & Supply Chain",
            "Logistics & Warehousing":        "Operations & Supply Chain",
            "Operations & Quality":           "Operations & Supply Chain",
            # Mechanical & Manufacturing
            "Mechanical Design & CAD":        "Mechanical & Manufacturing",
            "Manufacturing & Production":     "Mechanical & Manufacturing",
            "Quality & Maintenance":          "Mechanical & Manufacturing",
        }

        job_parents  = jobs["category"].map(_CSV_CAT_TO_PARENT).fillna(jobs["category"])
        is_primary   = job_parents == resume_category
        primary_jobs = jobs[is_primary].copy()
        other_jobs   = jobs[~is_primary].copy()
        if len(primary_jobs) == 0:
            primary_jobs = jobs.copy()
            other_jobs   = jobs.iloc[0:0].copy()
    else:
        primary_jobs = jobs.copy()
        other_jobs   = jobs.iloc[0:0].copy()

    # ── Score ─────────────────────────────────────────────────────────────────
    primary_results = _score_jobs(
        primary_jobs, resume_text, resume_skills, resume_years
    ).head(top_n_primary)

    other_results = (
        _score_jobs(other_jobs, resume_text, resume_skills, resume_years).head(top_n_other)
        if len(other_jobs) else pd.DataFrame()
    )

    # ── Merge source metadata ─────────────────────────────────────────────────
    meta_cols = ["job_id", "job_source", "employer_email"]
    meta = jobs[meta_cols].drop_duplicates(subset=["job_id"]).copy()

    if len(primary_results) > 0:
        primary_results = primary_results.merge(meta, on="job_id", how="left")
        primary_results["job_source"]     = primary_results["job_source"].fillna("csv")
        primary_results["employer_email"] = primary_results["employer_email"].fillna("")

    if other_results is not None and len(other_results) > 0:
        other_results = other_results.merge(meta, on="job_id", how="left")
        other_results["job_source"]     = other_results["job_source"].fillna("csv")
        other_results["employer_email"] = other_results["employer_email"].fillna("")

    return primary_results, other_results, sorted(list(resume_skills)), resume_category, resume_subcategory, resume_cat_label