"""
modules/profile_strength.py
────────────────────────────
Profile Strength Meter — purely visual, no AI or API needed.
Shows candidate how complete and strong their profile is across 6 dimensions,
with actionable tips to improve each section.
"""

import streamlit as st
import math
from modules.theme import T


# ── Dimension definitions ──────────────────────────────────────────────────────
DIMENSIONS = [
    {
        "key":   "skills",
        "label": "Skills Coverage",
        "icon":  "🧠",
        "max":   30,
        "desc":  "More relevant skills = better matches.",
        "tips": [
            "Add at least 15–20 skills for strong coverage.",
            "Include both hard skills (Python, SQL) and soft skills (communication).",
            "Look at job descriptions in Recommendations to find missing keywords.",
        ],
    },
    {
        "key":   "resume_length",
        "label": "Resume Depth",
        "icon":  "📄",
        "max":   25,
        "desc":  "Longer, richer resumes give the AI more to work with.",
        "tips": [
            "Aim for at least 400 words in your resume text.",
            "Describe each project with impact metrics (e.g. '1M+ records processed').",
            "Include education, certifications, and a professional summary.",
        ],
    },
    {
        "key":   "category",
        "label": "Category & Specialization",
        "icon":  "🎯",
        "max":   15,
        "desc":  "A detected category (10pts) + subcategory specialization (15pts) gives the best matches.",
        "tips": [
            "Use specific job-role keywords so the system detects your exact specialization.",
            "e.g. 'Clinical Research Associate' → detects Healthcare › Clinical Research & Trials.",
            "Avoid generic summaries — name your domain and role clearly in your resume.",
            "A detected subcategory scores 15/15; category-only scores 10/15; undetected scores 5/15.",
        ],
    },
    {
        "key":   "applications",
        "label": "Application Activity",
        "icon":  "📬",
        "max":   15,
        "desc":  "Active candidates get better visibility.",
        "tips": [
            "Apply to at least 5 roles to establish activity.",
            "Target strong matches (green) first.",
            "Re-upload your resume after adding new skills to get fresh matches.",
        ],
    },
    {
        "key":   "skill_variety",
        "label": "Skill Variety",
        "icon":  "🎨",
        "max":   10,
        "desc":  "A mix of hard and soft skills boosts all 3 score types.",
        "tips": [
            "Add at least 2–3 soft skills (communication, leadership, etc.).",
            "Mix tools (Power BI, Streamlit) with methods (EDA, regression).",
            "Cloud skills (AWS, GCP) add variety and are highly valued.",
        ],
    },
    {
        "key":   "resume_freshness",
        "label": "Resume Freshness",
        "icon":  "🔄",
        "max":   5,
        "desc":  "Recently uploaded resumes get priority.",
        "tips": [
            "Re-upload your resume every few weeks to stay current.",
            "Update your resume whenever you learn a new skill.",
            "Keep your skills list synchronized with what you actually know.",
        ],
    },
]

TOTAL_MAX = sum(d["max"] for d in DIMENSIONS)  # 100


# ── Scoring logic ──────────────────────────────────────────────────────────────

def _score_skills(skills: list) -> tuple[int, str]:
    n = len(skills)
    if n >= 25:  return 30, "Excellent"
    if n >= 18:  return 24, "Good"
    if n >= 12:  return 17, "Fair"
    if n >= 6:   return 10, "Weak"
    return 3, "Very Weak"


def _score_resume_length(resume_text: str) -> tuple[int, str]:
    words = len(resume_text.split()) if resume_text else 0
    if words >= 500: return 25, "Excellent"
    if words >= 350: return 20, "Good"
    if words >= 200: return 13, "Fair"
    if words >= 80:  return 7,  "Weak"
    return 2, "Very Weak"


def _score_category(category: str, subcategory: str = "") -> tuple[int, str]:
    if not category or category == "General":
        return 5, "Not Detected"
    if subcategory:
        return 15, f"{subcategory[:28]}{'…' if len(subcategory) > 28 else ''}"
    return 10, "Category Detected"


def _score_applications(user_email: str) -> tuple[int, str]:
    try:
        from modules.db import get_conn
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM applications WHERE user_email=?", (user_email,))
        n = cur.fetchone()[0]
        conn.close()
    except Exception:
        n = 0
    if n >= 10: return 15, f"{n} apps"
    if n >= 5:  return 10, f"{n} apps"
    if n >= 2:  return 6,  f"{n} apps"
    if n >= 1:  return 3,  f"{n} apps"
    return 0, "0 apps"


def _score_skill_variety(skills: list) -> tuple[int, str]:
    SOFT = {
        "communication","teamwork","leadership","problem solving","critical thinking",
        "attention to detail","time management","adaptability","storytelling",
        "presentation","stakeholder management","empathy","creativity",
    }
    TOOLS = {"power bi","tableau","streamlit","jupyter","excel","git","docker","aws","gcp","azure"}
    has_soft  = any(s.lower() in SOFT  for s in skills)
    has_tools = any(s.lower() in TOOLS for s in skills)
    has_hard  = len(skills) >= 5
    score = (4 if has_hard else 0) + (4 if has_soft else 0) + (2 if has_tools else 0)
    label = "Balanced" if score >= 8 else ("Partial" if score >= 4 else "Limited")
    return score, label


def _score_freshness(user_email: str) -> tuple[int, str]:
    try:
        from modules.db import get_conn
        from datetime import datetime
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute(
            "SELECT uploaded_at FROM resume_history WHERE user_email=? ORDER BY uploaded_at DESC LIMIT 1",
            (user_email,)
        )
        row = cur.fetchone()
        conn.close()
        if not row or not row[0]:
            return 0, "Never uploaded"
        uploaded = datetime.strptime(str(row[0])[:19], "%Y-%m-%d %H:%M:%S")
        days_ago = (datetime.now() - uploaded).days
        if days_ago <= 7:   return 5, f"{days_ago}d ago"
        if days_ago <= 30:  return 3, f"{days_ago}d ago"
        return 1, f"{days_ago}d ago"
    except Exception:
        return 2, "Active"


def _compute_scores(user_email: str) -> dict:
    skills      = st.session_state.get("resume_skills",      []) or []
    resume_text = st.session_state.get("resume_text",        "") or ""
    category    = st.session_state.get("resume_category",    "") or ""
    subcategory = st.session_state.get("resume_subcategory", "") or ""

    s_skills,   l_skills   = _score_skills(skills)
    s_length,   l_length   = _score_resume_length(resume_text)
    s_category, l_category = _score_category(category, subcategory)
    s_apps,     l_apps     = _score_applications(user_email)
    s_variety,  l_variety  = _score_skill_variety(skills)
    s_fresh,    l_fresh    = _score_freshness(user_email)

    scores = {
        "skills":         (s_skills,   l_skills),
        "resume_length":  (s_length,   l_length),
        "category":       (s_category, l_category),
        "applications":   (s_apps,     l_apps),
        "skill_variety":  (s_variety,  l_variety),
        "resume_freshness": (s_fresh,  l_fresh),
    }
    total = sum(v[0] for v in scores.values())
    return scores, total


# ── Gauge HTML ─────────────────────────────────────────────────────────────────

def _gauge_html(score: int, total: int = 100) -> str:
    pct   = score / total
    angle = -90 + pct * 180          # –90° (left) to +90° (right)
    rad   = math.radians(angle)
    nx    = 150 + 110 * math.cos(rad)
    ny    = 150 + 110 * math.sin(rad)

    if pct >= 0.75:   color, label = "#22c55e", "Excellent"
    elif pct >= 0.55: color, label = "#3b82f6", "Good"
    elif pct >= 0.35: color, label = "#f59e0b", "Fair"
    else:             color, label = "#ef4444", "Needs Work"

    # arc segments
    def arc_seg(start_pct, end_pct, col):
        sa = math.radians(-90 + start_pct * 180)
        ea = math.radians(-90 + end_pct   * 180)
        x1, y1 = 150 + 120*math.cos(sa), 150 + 120*math.sin(sa)
        x2, y2 = 150 + 120*math.cos(ea), 150 + 120*math.sin(ea)
        xi, yi = 150 + 80 *math.cos(sa), 150 + 80 *math.sin(sa)
        xj, yj = 150 + 80 *math.cos(ea), 150 + 80 *math.sin(ea)
        laf = 1 if (end_pct - start_pct) > 0.5 else 0
        return (f'<path d="M {x1:.1f} {y1:.1f} A 120 120 0 {laf} 1 {x2:.1f} {y2:.1f} '
                f'L {xj:.1f} {yj:.1f} A 80 80 0 {laf} 0 {xi:.1f} {yi:.1f} Z" '
                f'fill="{col}" opacity="0.18"/>')

    segs = (arc_seg(0, 0.35, "#ef4444") +
            arc_seg(0.35, 0.55, "#f59e0b") +
            arc_seg(0.55, 0.75, "#3b82f6") +
            arc_seg(0.75, 1.0,  "#22c55e"))

    return f"""
    <div style="display:flex;flex-direction:column;align-items:center;margin:10px 0">
      <svg width="300" height="165" viewBox="0 0 300 165">
        {segs}
        <!-- track -->
        <path d="M 30 150 A 120 120 0 0 1 270 150" fill="none" stroke="#333" stroke-width="2" stroke-dasharray="4,3"/>
        <!-- active arc -->
        <path d="M 30 150 A 120 120 0 {'1' if pct>0.5 else '0'} 1 {nx:.1f} {ny:.1f}"
              fill="none" stroke="{color}" stroke-width="16" stroke-linecap="round" opacity="0.9"/>
        <!-- needle -->
        <line x1="150" y1="150" x2="{nx:.1f}" y2="{ny:.1f}"
              stroke="{color}" stroke-width="3" stroke-linecap="round"/>
        <circle cx="150" cy="150" r="7" fill="{color}"/>
        <!-- score text -->
        <text x="150" y="132" text-anchor="middle" font-size="36" font-weight="700" fill="{color}">{score}</text>
        <text x="150" y="152" text-anchor="middle" font-size="13" fill="#888">out of {total}</text>
        <text x="150" y="167" text-anchor="middle" font-size="13" font-weight="600" fill="{color}">{label}</text>
      </svg>
    </div>"""


# ── Dimension card HTML ────────────────────────────────────────────────────────

def _dim_card(dim: dict, score: int, label: str) -> str:
    pct  = score / dim["max"]
    w    = round(pct * 100)
    if pct >= 0.8:   bar_color = "#22c55e"
    elif pct >= 0.5: bar_color = "#3b82f6"
    elif pct >= 0.3: bar_color = "#f59e0b"
    else:            bar_color = "#ef4444"

    p = T()
    return f"""
    <div style="border:1px solid {p['CARD_BORDER']};border-radius:12px;padding:14px 16px;margin-bottom:10px;background:{p['SURFACE']}">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span style="font-size:15px;font-weight:600;color:{p['TEXT_HEADING']}">{dim['icon']} {dim['label']}</span>
        <span style="font-size:13px;color:{p['MUTED']}">{score}/{dim['max']} &nbsp;·&nbsp; <span style="color:{bar_color}">{label}</span></span>
      </div>
      <div style="background:{p['PROGRESS_BG']};border-radius:6px;height:8px;overflow:hidden">
        <div style="width:{w}%;background:{bar_color};height:100%;border-radius:6px;
                    transition:width 0.6s ease"></div>
      </div>
      <div style="font-size:11px;color:{p['MUTED']};margin-top:6px">{dim['desc']}</div>
    </div>"""


# ── Main render ────────────────────────────────────────────────────────────────

def render_profile_strength(user_email: str):
    st.subheader("💪 Profile Strength Meter")
    st.caption("See how complete and competitive your profile is — and exactly how to improve it.")

    resume_text = st.session_state.get("resume_text", "") or ""
    if not resume_text.strip():
        st.warning("⚠️ Upload your resume first to get a profile strength score.")
        return

    scores, total = _compute_scores(user_email)

    # ── Gauge ──
    st.markdown(_gauge_html(total, TOTAL_MAX), unsafe_allow_html=True)
    st.divider()

    # ── Dimension breakdown ──
    st.markdown("### 📊 Score Breakdown")
    cols = st.columns(2)
    for i, dim in enumerate(DIMENSIONS):
        score, label = scores[dim["key"]]
        with cols[i % 2]:
            st.markdown(_dim_card(dim, score, label), unsafe_allow_html=True)

    st.divider()

    # ── Improvement tips — only show weak dims ──
    st.markdown("### 🚀 How to Improve")
    weak_dims = [
        (dim, scores[dim["key"]])
        for dim in DIMENSIONS
        if scores[dim["key"]][0] / dim["max"] < 0.75
    ]

    if not weak_dims:
        st.success("🎉 Your profile is in great shape! Keep it updated.")
    else:
        for dim, (score, label) in weak_dims:
            with st.expander(f"{dim['icon']} {dim['label']} — {label} ({score}/{dim['max']})"):
                for tip in dim["tips"]:
                    st.markdown(f"• {tip}")

    # ── Quick actions ──
    st.divider()
    st.markdown("### ⚡ Quick Actions")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**📄 Boost Resume Depth**\nAdd more project details and impact metrics to your resume PDF.")
    with c2:
        st.info("**🧠 Add Missing Skills**\nCheck Skill Gap tab to see which skills to learn next.")
    with c3:
        st.info("**📬 Apply to More Roles**\nGo to Recommendations and apply to at least 5 strong matches.")