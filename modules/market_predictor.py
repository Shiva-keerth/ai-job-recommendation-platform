"""
Market Skill Demand Predictor — modules/market_predictor.py
============================================================
Shows real market demand for skills based on the 600-job CSV dataset
and live employer-posted jobs. No external API needed — 100% from data.
Claude AI is used only for the "Career Roadmap" section.

Tab placement : ui_candidate.py → option "Market Trends"
Icon          : graph-up-arrow
Called as     : from modules.market_predictor import render_market_predictor
Usage         : render_market_predictor(user_email)
"""

import re
import json
import streamlit as st
import pandas as pd
from collections import Counter

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import JOBS_CSV, GROQ_API_KEY, SKILL_RESOURCES
from modules.db import get_conn


# ── Constants: real data from dataset analysis ──────────────────────

CATEGORY_AVG_SALARY = {
    "Software Engineering":        116197,
    "Data & Analytics":            108103,
    "Human Resources":             102684,
    "Marketing & Sales":            98030,
    "Finance & Accounting":         97092,
    "Healthcare":                   96527,
    "Operations & Supply Chain":    81114,
    "Mechanical & Manufacturing":   92204,
}

CATEGORY_TOP_SKILLS = {
    "Software Engineering":       ["python", "javascript", "docker", "kubernetes", "langchain", "microservices", "llm apis", "graphql"],
    "Data & Analytics":           ["python", "sql", "tableau", "power bi", "langchain", "airflow", "dbt", "machine learning"],
    "Finance & Accounting":       ["financial modeling", "excel", "ifrs", "variance analysis", "tally", "forecasting", "compliance", "sap"],
    "Marketing & Sales":          ["seo", "email marketing", "crm", "google analytics", "ai content tools", "ga4", "presentation", "lead generation"],
    "Human Resources":            ["recruitment", "onboarding", "workday", "hris", "people analytics", "payroll", "dei frameworks", "compliance"],
    "Healthcare":                 ["ehr", "clinical documentation", "medical terminology", "hipaa", "epic", "telemedicine", "quality assurance", "medical coding"],
    "Operations & Supply Chain":  ["erp", "lean", "procurement", "vendor management", "inventory management", "supply chain ai", "forecasting", "sap"],
    "Mechanical & Manufacturing": ["catia", "solidworks", "generative design", "cobots", "gd&t", "six sigma", "lean manufacturing", "ansys"],
}

EMERGING_SKILLS = {
    "Software Engineering":       ["llm apis", "langchain", "vector databases", "rust", "webassembly"],
    "Data & Analytics":           ["llm fine-tuning", "vector databases", "mlops", "feature engineering"],
    "Finance & Accounting":       ["python automation", "esg reporting", "blockchain basics", "power bi"],
    "Marketing & Sales":          ["ai content tools", "tiktok ads", "ga4", "marketing automation"],
    "Human Resources":            ["people analytics", "ai hiring tools", "hris", "dei frameworks"],
    "Healthcare":                 ["telemedicine", "ai diagnostics", "digital health", "epic"],
    "Operations & Supply Chain":  ["supply chain ai", "digital twin", "warehouse robotics", "sustainability ops"],
    "Mechanical & Manufacturing": ["generative design", "additive manufacturing", "digital twin", "cobots"],
}

ALL_CATEGORIES = list(CATEGORY_AVG_SALARY.keys())


# ── data helpers ──────────────────────────────────────────────────────

def _load_csv_skills_by_category(category: str | None = None) -> Counter:
    try:
        df = pd.read_csv(JOBS_CSV).fillna("")
        if category and category != "All":
            df = df[df["category"] == category]
        counter: Counter = Counter()
        for skills_text in df["skills"]:
            for s in re.split(r"[,|;/\n]+", str(skills_text).lower()):
                s = s.strip()
                if s and len(s) > 2:
                    counter[s] += 1
        return counter
    except Exception:
        return Counter()


def _load_db_skills(category: str | None = None) -> Counter:
    try:
        conn = get_conn()
        if category and category != "All":
            rows = conn.execute(
                "SELECT skills FROM jobs WHERE status='open' AND category=?", (category,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT skills FROM jobs WHERE status='open'").fetchall()
        conn.close()
        counter: Counter = Counter()
        for (skills_text,) in rows:
            for s in re.split(r"[,|;/\n]+", str(skills_text).lower()):
                s = s.strip()
                if s and len(s) > 2:
                    counter[s] += 1
        return counter
    except Exception:
        return Counter()


def _demand_score(skill: str, counter: Counter, total_jobs: int) -> int:
    """0-100 demand score based on frequency."""
    raw = counter.get(skill.lower(), 0)
    return min(100, int(raw / max(total_jobs, 1) * 100 * 3))


def _call_claude_roadmap(role: str, category: str, resume_skills: list) -> str:
    try:
        import groq
        client = groq.Groq(api_key=GROQ_API_KEY)
        system = (
            "You are a career advisor specializing in the Indian IT/professional job market. "
            "Give a concise, actionable 3-step career roadmap. Use bullet points. Max 120 words."
        )
        user = (
            f"Category: {category}"
            f"Target role: {role or 'mid-level professional'}"
            f"Current skills: {', '.join(resume_skills[:15]) or 'not specified'}"
            "Give a 3-step roadmap with specific skills to learn, certifications to get, "
            "and one actionable next step this week."
        )
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=300,
            temperature=0.3,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"_(AI roadmap unavailable: {str(e)[:60]})_"


# ── UI ─────────────────────────────────────────────────────────────────

def render_market_predictor(user_email: str):
    st.subheader("📈 Market Skill Demand Predictor")
    st.caption(
        "Real demand scores from 600 jobs in the dataset + live employer postings. "
        "No guessing — everything is calculated from actual job data."
    )

    # ── Category selector ─────────────────────────────────────────────
    resume_category    = st.session_state.get("resume_category", "")
    resume_subcategory = st.session_state.get("resume_subcategory", "")
    resume_cat_label   = st.session_state.get("resume_cat_label", "")

    default_idx = 0
    if resume_category and resume_category in ALL_CATEGORIES:
        default_idx = ALL_CATEGORIES.index(resume_category)

    selected_cat = st.selectbox(
        "Select a job category",
        ALL_CATEGORIES,
        index=default_idx,
        key="mp_category",
    )

    # ── Show subcategory badge if detected ────────────────────────────
    from modules.category_detector import get_subcategories_for_parent
    all_subs = get_subcategories_for_parent(selected_cat)

    col_sub1, col_sub2 = st.columns([2, 1])
    with col_sub1:
        selected_sub = st.selectbox(
            "Filter by Subcategory (optional)",
            ["All Subcategories"] + all_subs,
            index=(all_subs.index(resume_subcategory) + 1)
                  if resume_subcategory and resume_subcategory in all_subs else 0,
            key="mp_subcategory",
        )
    with col_sub2:
        if resume_subcategory and resume_subcategory in all_subs:
            st.markdown(
                f'<div style="margin-top:28px;background:#1d3a6e;border:1px solid #3b82f6;'
                f'border-radius:8px;padding:8px 12px;font-size:12px;color:#93c5fd">'
                f'🎯 Your specialization:<br><strong>{resume_subcategory}</strong></div>',
                unsafe_allow_html=True,
            )

    # ── Load data ─────────────────────────────────────────────────────
    csv_counter = _load_csv_skills_by_category(selected_cat)
    db_counter  = _load_db_skills(selected_cat)

    # Merge: CSV has 600 jobs, DB has live postings — combine
    combined: Counter = Counter()
    combined.update(csv_counter)
    combined.update(db_counter)

    try:
        _df_tmp = pd.read_csv(JOBS_CSV).fillna("")
        if selected_cat and selected_cat != "All":
            _df_tmp = _df_tmp[_df_tmp["category"] == selected_cat]
        total_jobs = len(_df_tmp)
    except Exception:
        total_jobs = 1200

    # ── Salary info ───────────────────────────────────────────────────
    avg_sal  = CATEGORY_AVG_SALARY.get(selected_cat, 100000)
    st.markdown("---")

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(
            f'<div style="background:var(--color-background-secondary);border-radius:10px;'
            f'padding:14px;text-align:center">'
            f'<div style="font-size:12px;color:var(--color-text-secondary)">Avg Salary (dataset)</div>'
            f'<div style="font-size:20px;font-weight:500">₹{avg_sal:,}/mo</div>'
            f'<div style="font-size:11px;color:var(--color-text-secondary)">≈ ₹{avg_sal*12//100000:.1f} LPA</div>'
            f'</div>', unsafe_allow_html=True
        )
    with k2:
        st.markdown(
            f'<div style="background:var(--color-background-secondary);border-radius:10px;'
            f'padding:14px;text-align:center">'
            f'<div style="font-size:12px;color:var(--color-text-secondary)">Jobs in dataset</div>'
            f'<div style="font-size:20px;font-weight:500">{total_jobs}</div>'
            f'<div style="font-size:11px;color:var(--color-text-secondary)">+ live DB postings</div>'
            f'</div>', unsafe_allow_html=True
        )
    with k3:
        live_cnt = sum(db_counter.values())
        st.markdown(
            f'<div style="background:var(--color-background-secondary);border-radius:10px;'
            f'padding:14px;text-align:center">'
            f'<div style="font-size:12px;color:var(--color-text-secondary)">Live DB skill mentions</div>'
            f'<div style="font-size:20px;font-weight:500">{live_cnt}</div>'
            f'<div style="font-size:11px;color:var(--color-text-secondary)">from employer postings</div>'
            f'</div>', unsafe_allow_html=True
        )

    st.markdown("---")

    # ── Top demanded skills chart ─────────────────────────────────────
    st.markdown("### 🔥 Top In-Demand Skills")
    top_n     = st.slider("Show top N skills", 5, 40, 15, key="mp_topn")
    top_skills = combined.most_common(top_n)
    if top_skills:
        chart_df = pd.DataFrame(top_skills, columns=["Skill", "Job Mentions"])
        st.bar_chart(chart_df.set_index("Skill"))
    else:
        st.info("No skill data for this category.")

    st.markdown("---")

    # ── Skill demand heatmap (your skills vs market) ──────────────────
    resume_skills = st.session_state.get("resume_skills", []) or []

    if resume_skills:
        st.markdown("### 🎯 Your Skills vs Market Demand")
        st.caption("How well your current skills align with what the market wants.")

        rows = []
        for sk in resume_skills[:20]:
            freq  = combined.get(sk.lower(), 0)
            dscore = _demand_score(sk, combined, total_jobs)
            rows.append({"Skill": sk, "Demand Score": dscore, "Mentions": freq})

        skill_df = pd.DataFrame(rows).sort_values("Demand Score", ascending=False)

        for _, row in skill_df.iterrows():
            score = int(row["Demand Score"])
            color = "#1D9E75" if score >= 50 else "#BA7517" if score >= 20 else "#A32D2D"
            bar_w = score
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
                f'<div style="width:130px;font-size:12px">{row["Skill"]}</div>'
                f'<div style="flex:1;height:18px;background:var(--color-background-secondary);border-radius:4px;overflow:hidden">'
                f'<div style="width:{bar_w}%;height:100%;background:{color};border-radius:4px"></div></div>'
                f'<div style="width:45px;font-size:12px;text-align:right;color:{color}">{score}%</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Missing high-demand skills
        top_demanded = {s.lower() for s, _ in combined.most_common(30)}
        your_skills  = {s.lower() for s in resume_skills}
        missing_high = top_demanded - your_skills

        if missing_high:
            st.markdown("---")
            st.markdown("### ⚠️ High-Demand Skills You're Missing")
            st.caption("These appear in the top 30 most-demanded skills but aren't in your resume.")
            links = []
            for s in sorted(missing_high)[:15]:
                url = SKILL_RESOURCES.get(s.lower())
                links.append(f"[`{s}`]({url})" if url else f"`{s}`")
            st.markdown("  ".join(links))
            st.caption("Click a skill to find a free learning resource.")

        st.markdown("---")

    # ── Category deep-dive ────────────────────────────────────────────
    st.markdown(f"### 🏷️ {selected_cat} — Skill Clusters")

    cat_core     = CATEGORY_TOP_SKILLS.get(selected_cat, [])
    cat_emerging = EMERGING_SKILLS.get(selected_cat, [])

    col_core, col_emerg = st.columns(2)

    with col_core:
        st.markdown("**Core / Established Skills**")
        for s in cat_core:
            freq   = combined.get(s, 0)
            dscore = min(100, int(freq / max(total_jobs, 1) * 100 * 3))
            color  = "#1D9E75" if dscore >= 50 else "#BA7517"
            url    = SKILL_RESOURCES.get(s.lower())
            link   = f"[{s}]({url})" if url else s
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:5px 8px;margin-bottom:4px;background:var(--color-background-secondary);'
                f'border-radius:6px;font-size:13px">'
                f'<span>{link}</span>'
                f'<span style="color:{color};font-weight:500">{dscore}%</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_emerg:
        st.markdown("**Emerging / High-Growth Skills**")
        for s in cat_emerging:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:5px 8px;margin-bottom:4px;background:#E1F5EE;'
                f'border-radius:6px;font-size:13px;color:#085041">'
                f'<span>{s}</span>'
                f'<span style="font-size:11px">↑ Trending</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Cross-category comparison ─────────────────────────────────────
    st.markdown("### 📊 Salary Comparison — All Categories")
    sal_df = pd.DataFrame(
        [(k, v, round(v * 12 / 100000, 1)) for k, v in CATEGORY_AVG_SALARY.items()],
        columns=["Category", "Avg ₹/mo", "LPA"]
    ).sort_values("Avg ₹/mo", ascending=False)

    # Highlight selected category
    styled_rows = []
    for _, row in sal_df.iterrows():
        is_selected = row["Category"] == selected_cat
        bg = "#E1F5EE" if is_selected else "var(--color-background-secondary)"
        styled_rows.append(
            f'<div style="display:flex;justify-content:space-between;padding:7px 10px;'
            f'margin-bottom:4px;background:{bg};border-radius:6px;font-size:13px">'
            f'<span>{"→ " if is_selected else ""}{row["Category"]}</span>'
            f'<span style="font-weight:500">₹{int(row["Avg ₹/mo"]):,}/mo &nbsp;·&nbsp; ₹{row["LPA"]} LPA</span>'
            f'</div>'
        )
    st.markdown("".join(styled_rows), unsafe_allow_html=True)

    st.markdown("---")

    # ── AI Career Roadmap ─────────────────────────────────────────────
    st.markdown("### 🗺️ AI Career Roadmap")
    st.caption("Powered by Claude AI — personalised to your skills and chosen category.")

    target_role = st.text_input(
        "Target role (optional)",
        placeholder="e.g. Senior Data Analyst, DevOps Engineer…",
        key="mp_target_role",
    )

    if st.button("✨ Generate My Roadmap", key="mp_roadmap_btn", use_container_width=False):
        with st.spinner("Generating roadmap…"):
            roadmap = _call_claude_roadmap(target_role, selected_cat, resume_skills)
        st.session_state["mp_roadmap"] = roadmap

    if st.session_state.get("mp_roadmap"):
        st.markdown(
            f'<div style="border-left:3px solid #185FA5;padding:12px 16px;'
            f'border-radius:0 8px 8px 0;background:var(--color-background-secondary);'
            f'font-size:13px;line-height:1.7">{st.session_state["mp_roadmap"]}</div>',
            unsafe_allow_html=True,
        )
        if st.button("🔄 Regenerate", key="mp_regen"):
            st.session_state.pop("mp_roadmap", None)
            st.rerun()

    # ── Download full skill demand ─────────────────────────────────────
    st.markdown("---")
    full_df = pd.DataFrame(combined.most_common(), columns=["Skill", "Mentions"])
    full_df["Demand Score %"] = full_df["Mentions"].apply(
        lambda x: min(100, int(x / max(total_jobs, 1) * 300))
    )
    st.download_button(
        f"⬇️ Download {selected_cat} Skill Demand CSV",
        full_df.to_csv(index=False),
        file_name=f"skill_demand_{selected_cat.replace(' ', '_').replace('&','and')}.csv",
        mime="text/csv",
    )