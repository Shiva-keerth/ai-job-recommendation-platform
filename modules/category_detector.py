# -*- coding: utf-8 -*-
"""
modules/category_detector.py
─────────────────────────────
Two-level category detection:
  Level 1 → Parent category  (e.g. "Healthcare")
  Level 2 → Subcategory      (e.g. "Clinical Research & Trials")

Public API:
  detect_category(text)          → parent category string  (backward-compatible)
  detect_subcategory(text)       → subcategory string
  detect_full_category(text)     → {"parent": ..., "sub": ..., "label": ...}
  get_subcategories_for_parent() → list of subcategory names
  get_all_subcategories()        → dict of parent → [subcategories]
"""

import re
from collections import defaultdict


# ══════════════════════════════════════════════════════════════════════
# LEVEL 1 — PARENT CATEGORIES  (unchanged, stays compatible)
# ══════════════════════════════════════════════════════════════════════

CATEGORY_KEYWORDS = {
    "Software Engineering": [
        "software", "developer", "engineer", "devops", "cloud", "aws", "azure", "gcp",
        "backend", "frontend", "full stack", "api", "java", "react", "python",
        "docker", "kubernetes", "microservices", "node", "typescript", "golang",
        "ml engineer", "ai engineer", "site reliability", "platform engineer",
        "blockchain", "mobile app", "android", "ios", "flutter",
    ],
    "Data & Analytics": [
        "data analyst", "data analytics", "data scientist", "business intelligence",
        "bi developer", "analytics", "sql", "power bi", "tableau", "excel",
        "pandas", "numpy", "dashboard", "eda", "statistics", "machine learning",
        "deep learning", "mlops", "data engineer", "reporting analyst",
        "product analyst", "research analyst", "forecasting", "dbt", "spark",
    ],
    "Finance & Accounting": [
        "accounting", "finance", "audit", "tax", "gst", "tally", "financial modeling",
        "investment", "banking", "risk", "financial analyst", "accountant",
        "bookkeeping", "compliance", "budgeting", "treasury", "fp&a",
        "credit analyst", "cost accountant", "ifrs", "ind as",
    ],
    "Marketing & Sales": [
        "marketing", "seo", "sem", "google ads", "meta ads", "content", "brand",
        "growth", "social media", "campaign", "crm", "sales", "digital marketing",
        "email marketing", "performance marketing", "influencer", "copywriting",
        "lead generation", "market research", "product marketing",
    ],
    "Human Resources": [
        "human resources", "hr", "recruitment", "talent acquisition", "payroll",
        "hrbp", "hr generalist", "hr analyst", "onboarding", "learning development",
        "compensation", "employee relations", "hr operations", "diversity",
        "hr business partner", "people analytics", "workforce",
    ],
    "Healthcare": [
        "clinical", "hospital", "medical", "pharma", "patient", "healthcare",
        "pharmacovigilance", "lab technician", "health informatics",
        "clinical research", "medical billing", "medical coding",
        "public health", "telemedicine", "ehr", "hipaa",
    ],
    "Operations & Supply Chain": [
        "operations", "process improvement", "supply chain", "logistics",
        "procurement", "inventory", "warehouse", "production", "vendor",
        "demand planning", "fleet", "import export", "quality control",
        "erp", "lean", "six sigma", "supply chain analyst",
    ],
    "Mechanical & Manufacturing": [
        "mechanical", "manufacturing", "cad", "solidworks", "catia", "autocad",
        "ansys", "production engineer", "process engineer", "quality engineer",
        "maintenance engineer", "industrial engineer", "automation",
        "cnc", "plc", "3d printing", "gd&t", "fmea",
    ],
    "General": [],
}


# ══════════════════════════════════════════════════════════════════════
# LEVEL 2 — SUBCATEGORIES
# Format: subcategory_name → (parent_category, [detection_keywords])
# ══════════════════════════════════════════════════════════════════════

SUBCATEGORY_MAP: dict[str, tuple[str, list]] = {

    # ── Software Engineering ──────────────────────────────────────────
    "AI & ML Engineering": (
        "Software Engineering",
        ["ml engineer", "ai engineer", "machine learning engineer", "llm",
         "langchain", "vector database", "llm apis", "model deployment",
         "fine tuning", "transformer", "generative ai"],
    ),
    "Backend Development": (
        "Software Engineering",
        ["backend", "backend developer", "django", "flask", "fastapi",
         "spring boot", "rest api", "graphql", "microservices", "golang",
         "java developer", "python backend"],
    ),
    "Frontend Development": (
        "Software Engineering",
        ["frontend", "frontend developer", "react", "angular", "vue",
         "javascript developer", "typescript developer", "ui developer",
         "web developer", "next.js", "html css"],
    ),
    "Full Stack Development": (
        "Software Engineering",
        ["full stack", "fullstack", "mern", "mean", "full-stack developer",
         "full stack developer"],
    ),
    "DevOps & Cloud Engineering": (
        "Software Engineering",
        ["devops", "cloud engineer", "aws engineer", "azure engineer",
         "docker", "kubernetes", "terraform", "ansible", "jenkins",
         "ci/cd", "site reliability", "sre", "platform engineer",
         "infrastructure engineer", "github actions"],
    ),
    "Mobile App Development": (
        "Software Engineering",
        ["mobile app", "android developer", "ios developer", "flutter developer",
         "react native", "swift", "kotlin", "mobile developer"],
    ),
    "Blockchain Development": (
        "Software Engineering",
        ["blockchain", "web3", "solidity", "smart contract", "ethereum",
         "blockchain developer", "defi", "nft"],
    ),
    "Security Engineering": (
        "Software Engineering",
        ["security engineer", "cybersecurity", "penetration testing",
         "ethical hacking", "soc analyst", "network security",
         "information security", "devsecops", "appsec"],
    ),
    "Embedded & Systems Engineering": (
        "Software Engineering",
        ["embedded", "embedded systems", "firmware", "rtos", "microcontroller",
         "iot firmware", "embedded engineer", "systems programmer"],
    ),
    "QA & Testing": (
        "Software Engineering",
        ["qa engineer", "quality assurance engineer", "test automation",
         "selenium", "manual testing", "qa analyst", "software testing",
         "playwright", "testing engineer"],
    ),

    # ── Data & Analytics ─────────────────────────────────────────────
    "Data Science & Machine Learning": (
        "Data & Analytics",
        ["data scientist", "machine learning", "deep learning", "nlp",
         "neural network", "predictive modeling", "scikit learn",
         "tensorflow", "pytorch", "feature engineering", "computer vision",
         "model building"],
    ),
    "Data Engineering": (
        "Data & Analytics",
        ["data engineer", "etl", "data pipeline", "airflow", "spark",
         "kafka", "dbt", "snowflake", "bigquery", "data warehouse",
         "data lake", "databricks", "hadoop"],
    ),
    "Business Intelligence & Reporting": (
        "Data & Analytics",
        ["bi developer", "business intelligence", "tableau", "power bi",
         "looker", "metabase", "reporting analyst", "dashboard developer",
         "data visualization analyst", "bi analyst"],
    ),
    "Business & Product Analytics": (
        "Data & Analytics",
        ["business analyst", "product analyst", "ab testing", "product metrics",
         "user analytics", "funnel analysis", "cohort analysis",
         "growth analytics", "market research analyst", "research analyst"],
    ),
    "MLOps & AI Infrastructure": (
        "Data & Analytics",
        ["mlops", "mlops engineer", "model monitoring", "model deployment",
         "feature store", "kubeflow", "ml pipeline", "analytics engineer",
         "llm fine-tuning", "vector databases"],
    ),
    "Risk & Quantitative Analytics": (
        "Data & Analytics",
        ["risk analyst data", "quantitative analyst", "risk modeling",
         "credit scoring", "fraud detection", "statistical modeling",
         "forecasting analyst", "quant analyst"],
    ),

    # ── Finance & Accounting ─────────────────────────────────────────
    "Financial Planning & Analysis": (
        "Finance & Accounting",
        ["fp&a", "financial planning", "budgeting", "forecasting finance",
         "variance analysis", "financial modeling", "p&l management",
         "fp&a analyst", "finance manager"],
    ),
    "Investment & Wealth Management": (
        "Finance & Accounting",
        ["investment analyst", "portfolio management", "equity research",
         "asset management", "wealth management", "bloomberg terminal",
         "investment banking", "capital markets"],
    ),
    "Accounting & Bookkeeping": (
        "Finance & Accounting",
        ["accountant", "bookkeeping", "accounts payable", "accounts receivable",
         "tally", "general ledger", "cost accountant", "management accounting",
         "financial accountant"],
    ),
    "Audit & Compliance": (
        "Finance & Accounting",
        ["audit associate", "internal audit", "compliance analyst",
         "regulatory compliance finance", "risk compliance", "sox",
         "ifrs", "ind as", "statutory audit"],
    ),
    "Tax & Treasury": (
        "Finance & Accounting",
        ["tax analyst", "taxation", "gst specialist", "direct tax",
         "indirect tax", "treasury analyst", "cash flow management",
         "liquidity management", "tax manager"],
    ),
    "Credit & Risk Management": (
        "Finance & Accounting",
        ["credit analyst", "risk management", "credit risk", "market risk",
         "operational risk", "risk assessment", "underwriting",
         "credit manager"],
    ),

    # ── Marketing & Sales ────────────────────────────────────────────
    "Digital Marketing": (
        "Marketing & Sales",
        ["digital marketing specialist", "seo specialist", "sem specialist",
         "google ads specialist", "meta ads", "ppc manager",
         "paid marketing", "search engine marketing", "search engine optimization"],
    ),
    "Content & Brand Marketing": (
        "Marketing & Sales",
        ["content strategist", "brand manager", "content marketing",
         "copywriting", "brand marketing", "storytelling marketer",
         "content creator", "influencer marketing"],
    ),
    "Performance & Growth Marketing": (
        "Marketing & Sales",
        ["performance marketing manager", "growth marketer", "growth hacking",
         "conversion optimization", "retention marketing",
         "tiktok ads manager", "performance manager"],
    ),
    "Social Media Marketing": (
        "Marketing & Sales",
        ["social media manager", "social media marketing", "instagram marketing",
         "facebook marketing", "linkedin marketing", "community management"],
    ),
    "CRM & Marketing Automation": (
        "Marketing & Sales",
        ["crm specialist", "hubspot", "salesforce marketing", "marketing automation",
         "email marketing specialist", "email campaigns", "ga4 specialist",
         "marketing operations"],
    ),
    "Sales & Business Development": (
        "Marketing & Sales",
        ["sales executive", "business development", "lead generation specialist",
         "b2b sales", "account management", "sales manager",
         "inside sales", "field sales", "bdm"],
    ),
    "Market Research & Product Marketing": (
        "Marketing & Sales",
        ["market research analyst", "product marketing manager",
         "competitive analysis", "consumer insights", "go-to-market",
         "product launch", "market analysis"],
    ),

    # ── Human Resources ──────────────────────────────────────────────
    "Talent Acquisition & Recruitment": (
        "Human Resources",
        ["talent acquisition specialist", "recruiter", "talent acquisition",
         "sourcing specialist", "linkedin recruiter", "campus hiring",
         "headhunting", "screening", "hiring manager"],
    ),
    "HR Operations & Payroll": (
        "Human Resources",
        ["hr operations manager", "payroll specialist", "payroll processing",
         "hris administrator", "workday", "sap successfactors",
         "hr admin", "employee lifecycle"],
    ),
    "HR Business Partnership": (
        "Human Resources",
        ["hr business partner", "hrbp", "hr generalist", "employee relations specialist",
         "stakeholder hr", "hr consulting"],
    ),
    "Learning & Development": (
        "Human Resources",
        ["learning development associate", "l&d", "training specialist",
         "instructional design", "upskilling", "e-learning developer",
         "corporate training"],
    ),
    "Compensation & Benefits": (
        "Human Resources",
        ["compensation analyst", "benefits analyst", "total rewards",
         "salary benchmarking", "compensation planning",
         "labour law specialist", "compensation manager"],
    ),
    "HR Analytics & DEI": (
        "Human Resources",
        ["hr data analyst", "hr analyst", "people analytics",
         "workforce analytics", "diversity inclusion specialist",
         "dei frameworks", "diversity specialist", "dei manager"],
    ),

    # ── Healthcare ───────────────────────────────────────────────────
    "Clinical Research & Trials": (
        "Healthcare",
        ["clinical research associate", "clinical trials", "cra",
         "clinical data coordinator", "gcp guidelines", "clinical protocol",
         "investigator site", "clinical study manager"],
    ),
    "Medical Coding & Billing": (
        "Healthcare",
        ["medical coder", "medical coding", "medical billing specialist",
         "icd-10 coding", "cpt codes", "hcc coding", "revenue cycle",
         "billing specialist"],
    ),
    "Health Informatics & Data": (
        "Healthcare",
        ["health informatics specialist", "healthcare data analyst",
         "ehr specialist", "epic systems", "cerner specialist",
         "healthcare analytics", "clinical data analyst", "health data"],
    ),
    "Pharmacovigilance & Drug Safety": (
        "Healthcare",
        ["pharmacovigilance associate", "drug safety specialist",
         "adverse event reporting", "signal detection", "icsr",
         "pv specialist", "pharmacovigilance"],
    ),
    "Hospital & Healthcare Administration": (
        "Healthcare",
        ["healthcare administrator", "hospital operations manager",
         "hospital administration", "healthcare operations",
         "patient coordination", "healthcare compliance"],
    ),
    "Public Health & Telemedicine": (
        "Healthcare",
        ["public health analyst", "telemedicine coordinator",
         "community health", "epidemiology", "digital health specialist",
         "telehealth coordinator", "public health"],
    ),
    "Lab & Diagnostics": (
        "Healthcare",
        ["lab technician", "laboratory technician", "diagnostics",
         "pathology lab", "lab management", "medical laboratory",
         "clinical lab technician"],
    ),

    # ── Operations & Supply Chain ────────────────────────────────────
    "Procurement & Vendor Management": (
        "Operations & Supply Chain",
        ["procurement specialist", "vendor manager", "strategic sourcing",
         "supplier management", "purchasing manager", "procurement officer",
         "vendor negotiation"],
    ),
    "Logistics & Distribution": (
        "Operations & Supply Chain",
        ["logistics coordinator", "fleet manager", "transportation manager",
         "distribution manager", "last mile delivery", "freight management",
         "import export specialist", "customs specialist"],
    ),
    "Inventory & Warehouse Management": (
        "Operations & Supply Chain",
        ["inventory planner", "warehouse supervisor", "warehouse management",
         "stock management", "inventory control", "warehouse operations",
         "inventory analyst"],
    ),
    "Demand Planning & Forecasting": (
        "Operations & Supply Chain",
        ["demand planning analyst", "demand forecasting", "supply planning",
         "s&op planning", "sales and operations planning", "demand planner"],
    ),
    "Process & Quality Improvement": (
        "Operations & Supply Chain",
        ["process improvement analyst", "quality control analyst",
         "lean six sigma", "process excellence", "continuous improvement",
         "kaizen", "operational efficiency analyst"],
    ),
    "Supply Chain Analytics": (
        "Operations & Supply Chain",
        ["supply chain analyst", "operations analyst", "supply chain analytics",
         "supply chain ai", "erp analyst", "sap scm", "oracle scm",
         "supply chain data analyst"],
    ),

    # ── Mechanical & Manufacturing ───────────────────────────────────
    "Product & CAD Design": (
        "Mechanical & Manufacturing",
        ["product design engineer", "cad designer", "solidworks designer",
         "catia designer", "autocad draftsman", "3d modeling engineer",
         "generative design engineer", "design engineer"],
    ),
    "Manufacturing & Production Engineering": (
        "Mechanical & Manufacturing",
        ["manufacturing engineer", "production engineer", "process engineer",
         "lean manufacturing engineer", "production planning",
         "cnc programmer", "additive manufacturing engineer"],
    ),
    "Quality Engineering": (
        "Mechanical & Manufacturing",
        ["quality engineer", "quality control engineer", "fmea specialist",
         "gd&t engineer", "six sigma quality", "iso quality",
         "quality assurance engineer", "inspection engineer",
         "root cause analysis engineer"],
    ),
    "Automation & Robotics": (
        "Mechanical & Manufacturing",
        ["automation engineer", "robotics engineer", "plc programmer",
         "scada engineer", "cobots specialist", "industrial automation",
         "robot programming", "iot manufacturing"],
    ),
    "Structural & Thermal Engineering": (
        "Mechanical & Manufacturing",
        ["structural engineer", "thermal engineer", "ansys analyst",
         "fea engineer", "finite element analyst", "stress analysis engineer",
         "thermal analysis engineer", "simulation engineer"],
    ),
    "Maintenance & Industrial Engineering": (
        "Mechanical & Manufacturing",
        ["maintenance engineer", "industrial engineer", "predictive maintenance",
         "preventive maintenance", "reliability engineer",
         "plant maintenance engineer", "digital twin specialist"],
    ),
}


# ── Parent → sorted list of its subcategories ─────────────────────────
PARENT_TO_SUBS: dict[str, list[str]] = defaultdict(list)
for _sub_name, (_parent, _) in SUBCATEGORY_MAP.items():
    PARENT_TO_SUBS[_parent].append(_sub_name)


# ══════════════════════════════════════════════════════════════════════
# DETECTION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def detect_category(text: str) -> str:
    """
    Level-1 detection — returns parent category string.
    Fully backward-compatible with all existing callers.
    """
    t = (text or "").lower()
    scores: dict[str, int] = defaultdict(int)

    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if re.search(r"\b" + re.escape(kw) + r"\b", t):
                scores[cat] += 1

    if not scores:
        return "General"
    return max(scores.items(), key=lambda x: x[1])[0]


def detect_subcategory(text: str, parent_category: str = None) -> str:
    """
    Level-2 detection — returns best matching subcategory name.
    Constrained to parent_category when provided (recommended).
    Returns empty string "" if no subcategory matched.
    """
    t = (text or "").lower()
    scores: dict[str, int] = defaultdict(int)

    for sub_name, (parent, kws) in SUBCATEGORY_MAP.items():
        if parent_category and parent_category != "General":
            if parent != parent_category:
                continue
        for kw in kws:
            if re.search(r"\b" + re.escape(kw) + r"\b", t):
                scores[sub_name] += 1

    if not scores:
        return ""

    best_sub, best_score = max(scores.items(), key=lambda x: x[1])
    return best_sub if best_score >= 1 else ""


def detect_full_category(text: str) -> dict:
    """
    Full two-level detection.
    Returns dict:
      {
        "parent": "Healthcare",
        "sub":    "Clinical Research & Trials",
        "label":  "Healthcare › Clinical Research & Trials"
      }
    If no subcategory found, sub="" and label=parent.
    """
    parent = detect_category(text)
    sub    = detect_subcategory(text, parent_category=parent)
    label  = f"{parent} > {sub}" if sub else parent

    return {
        "parent": parent,
        "sub":    sub,
        "label":  label,
    }


def get_subcategories_for_parent(parent: str) -> list[str]:
    """Returns all subcategory names for a given parent category, sorted."""
    return sorted(PARENT_TO_SUBS.get(parent, []))


def get_all_subcategories() -> dict[str, list[str]]:
    """Returns full mapping: parent → sorted list of subcategories."""
    return {k: sorted(v) for k, v in PARENT_TO_SUBS.items()}