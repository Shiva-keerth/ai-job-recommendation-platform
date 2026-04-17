from pathlib import Path
import os

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # dotenv not installed, fall back to system env vars

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
DB_PATH     = BASE_DIR / "db" / "app.db"
CSV_USERS   = BASE_DIR / "db" / "users.csv"
JOBS_CSV    = BASE_DIR / "data" / "jobs_dataset.csv"

# ── Matching weights (must sum to 1.0) ────────────────────────────────
#   Core skill overlap        — 60%  (reduced from 72% to make room)
#   Secondary skill overlap   — 13%  (reduced from 18%)
#   TF-IDF semantic similarity—  9%  (reduced from 10%)
#   Experience level match    —  8%  (NEW)
#   Projects relevance        —  6%  (NEW)
#   Certifications bonus      —  4%  (NEW)
CORE_SKILLS_N       = 8
SOFT_SKILL_WEIGHT   = 0.25

WEIGHT_CORE         = 0.60
WEIGHT_SECONDARY    = 0.13
WEIGHT_TFIDF        = 0.09
WEIGHT_EXPERIENCE   = 0.08   # experience level + years match
WEIGHT_PROJECTS     = 0.06   # project domain relevance
WEIGHT_CERTS        = 0.04   # certifications relevance

# ── Experience level mapping ───────────────────────────────────────────
# Maps resume years-of-experience → expected job experience_level labels
# 0 yrs  → Intern / Fresher
# 1-2    → Junior
# 3-5    → Mid
# 6+     → Senior
EXPERIENCE_LEVEL_MAP = {
    "intern":  (0, 0),
    "fresher": (0, 1),
    "junior":  (1, 2),
    "mid":     (3, 5),
    "senior":  (6, 99),
}

# ── ATS penalty constants ──────────────────────────────────────────────
OPTIMISTIC_BOOST    = 0.08
ATS_BASE_PENALTY    = 0.05
ATS_MISS_PENALTY    = 0.20
ATS_CORE_PENALTY    = 0.15

# ── Results counts ─────────────────────────────────────────────────────
TOP_N_PRIMARY   = 12
TOP_N_OTHER     = 4

# ── Skill-gap learning resources ──────────────────────────────────────
SKILL_RESOURCES: dict[str, str] = {
    "python":           "https://www.learnpython.org/",
    "sql":              "https://sqlzoo.net/",
    "machine learning": "https://www.coursera.org/learn/machine-learning",
    "deep learning":    "https://www.coursera.org/specializations/deep-learning",
    "tableau":          "https://www.tableau.com/learn/training",
    "power bi":         "https://learn.microsoft.com/en-us/power-bi/",
    "excel":            "https://support.microsoft.com/en-us/excel",
    "docker":           "https://docs.docker.com/get-started/",
    "kubernetes":       "https://kubernetes.io/docs/tutorials/",
    "aws":              "https://aws.amazon.com/training/",
    "azure":            "https://learn.microsoft.com/en-us/azure/",
    "gcp":              "https://cloud.google.com/learn",
    "react":            "https://react.dev/learn",
    "django":           "https://docs.djangoproject.com/en/stable/intro/tutorial01/",
    "flask":            "https://flask.palletsprojects.com/en/stable/tutorial/",
    "java":             "https://dev.java/learn/",
    "javascript":       "https://javascript.info/",
    "typescript":       "https://www.typescriptlang.org/docs/handbook/",
    "postgresql":       "https://www.postgresql.org/docs/current/tutorial.html",
    "mongodb":          "https://learn.mongodb.com/",
    "redis":            "https://redis.io/learn",
    "git":              "https://git-scm.com/book/en/v2",
    "linux":            "https://linuxjourney.com/",
    "data visualization":"https://www.kaggle.com/learn/data-visualization",
    "pandas":           "https://pandas.pydata.org/docs/getting_started/",
    "numpy":            "https://numpy.org/learn/",
    "scikit-learn":     "https://scikit-learn.org/stable/getting_started.html",
    "tensorflow":       "https://www.tensorflow.org/tutorials",
    "pytorch":          "https://pytorch.org/tutorials/",
    "nlp":              "https://www.nltk.org/book/",
    "statistics":       "https://www.khanacademy.org/math/statistics-probability",
    "communication":    "https://www.coursera.org/learn/communication-skills",
    "leadership":       "https://www.coursera.org/learn/leading-teams",
    "agile":            "https://www.atlassian.com/agile",
    "scrum":            "https://www.scrum.org/resources/what-is-scrum",
    "hr policies":      "https://www.shrm.org/resourcesandtools/",
    "recruitment":      "https://www.linkedin.com/learning/topics/recruiting",
    "seo":              "https://developers.google.com/search/docs/beginner/seo-starter-guide",
    "google ads":       "https://skillshop.withgoogle.com/",
    "financial modeling":"https://corporatefinanceinstitute.com/resources/excel/financial-modeling/",
    "accounting":       "https://www.coursera.org/learn/wharton-accounting",
    "dbt":              "https://courses.getdbt.com/",
    "airflow":          "https://airflow.apache.org/docs/apache-airflow/stable/tutorial/",
    "spark":            "https://spark.apache.org/docs/latest/quick-start.html",
}

# ── Score thresholds ───────────────────────────────────────────────────
STRONG_MATCH    = 0.70
MODERATE_MATCH  = 0.40

# ── Gmail SMTP — OTP Email Verification ───────────────────────────────
# Secrets are loaded from .env file (never committed to Git)
# To set up: create a .env file with GMAIL_SENDER, GMAIL_APP_PWD, GROQ_API_KEY
GMAIL_SENDER  = os.environ.get("GMAIL_SENDER", "")
GMAIL_APP_PWD = os.environ.get("GMAIL_APP_PWD", "")
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")

