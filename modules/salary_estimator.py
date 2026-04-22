"""
modules/salary_estimator.py
────────────────────────────
Salary Estimator — uses the real jobs dataset, no AI needed.
Parses ₹/mo salary ranges from CSV, shows:
  • Estimated salary band for candidate based on their skills + category
  • Market comparison by role, experience level, and industry
  • Visual charts using st.bar_chart / st.line_chart
"""

import re
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import JOBS_CSV


# ── Salary parsing ─────────────────────────────────────────────────────────────

def _parse_salary(salary_str: str) -> tuple[float, float] | None:
    """Parse '₹22,800/mo - ₹70,000/mo' → (22800.0, 70000.0)"""
    if not salary_str or str(salary_str).strip() == "":
        return None
    nums = re.findall(r"[\d,]+", str(salary_str))
    nums = [float(n.replace(",", "")) for n in nums if n.replace(",", "").isdigit()]
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return nums[0], nums[0]
    return None


def _load_salary_df() -> pd.DataFrame:
    df = pd.read_csv(str(JOBS_CSV)).fillna("")
    parsed = df["salary_range"].apply(_parse_salary)
    df["sal_min"] = parsed.apply(lambda x: x[0] if x else None)
    df["sal_max"] = parsed.apply(lambda x: x[1] if x else None)
    df["sal_mid"] = (df["sal_min"] + df["sal_max"]) / 2
    df = df.dropna(subset=["sal_mid"])
    return df


def _annual(monthly: float) -> float:
    return round(monthly * 12 / 100_000, 2)   # in LPA


# ── Estimate for candidate ─────────────────────────────────────────────────────

def _estimate_for_candidate(df: pd.DataFrame, category: str, skills: list, exp_level: str) -> dict:
    """Return a salary estimate dict for this candidate."""
    # Filter by category
    cat_df = df[df["category"] == category] if category and category != "General" else df

    # Filter by experience level
    exp_df = cat_df[cat_df["experience_level"] == exp_level] if exp_level else cat_df
    if len(exp_df) < 3:
        exp_df = cat_df   # fallback to full category

    if len(exp_df) == 0:
        exp_df = df       # fallback to all

    # Skill-weighted: jobs where candidate has more matching skills get higher weight
    def skill_overlap(row):
        job_skills = set(s.strip().lower() for s in str(row.get("skills", "")).split(","))
        resume_set = set(s.lower() for s in skills)
        return len(job_skills & resume_set)

    exp_df = exp_df.copy()
    exp_df["overlap"] = exp_df.apply(skill_overlap, axis=1)

    # Weighted average (weight = overlap + 1 to avoid zero weights)
    weights = exp_df["overlap"] + 1
    w_min = (exp_df["sal_min"] * weights).sum() / weights.sum()
    w_max = (exp_df["sal_max"] * weights).sum() / weights.sum()
    w_mid = (w_min + w_max) / 2

    return {
        "min_mo":  round(w_min),
        "max_mo":  round(w_max),
        "mid_mo":  round(w_mid),
        "min_lpa": _annual(w_min),
        "max_lpa": _annual(w_max),
        "mid_lpa": _annual(w_mid),
        "n_jobs":  len(exp_df),
        "avg_overlap": round(exp_df["overlap"].mean(), 1),
    }


# ── Charts data ────────────────────────────────────────────────────────────────

def _by_role(df: pd.DataFrame, category: str) -> pd.DataFrame:
    cat_df = df[df["category"] == category] if category and category != "General" else df
    grp = cat_df.groupby("job_title")[["sal_min","sal_max","sal_mid"]].mean().round(0)
    grp["Min (LPA)"] = (grp["sal_min"] * 12 / 100_000).round(2)
    grp["Mid (LPA)"] = (grp["sal_mid"] * 12 / 100_000).round(2)
    grp["Max (LPA)"] = (grp["sal_max"] * 12 / 100_000).round(2)
    return grp[["Min (LPA)","Mid (LPA)","Max (LPA)"]].sort_values("Mid (LPA)", ascending=False)


def _by_experience(df: pd.DataFrame, category: str) -> pd.DataFrame:
    cat_df = df[df["category"] == category] if category and category != "General" else df
    order  = ["Intern","Fresher","Junior","Mid","Senior"]
    grp    = cat_df.groupby("experience_level")["sal_mid"].mean().round(0)
    grp    = grp.reindex([x for x in order if x in grp.index])
    result = pd.DataFrame({"Experience Level": grp.index, "Avg Mid Salary (LPA)": (grp.values * 12 / 100_000).round(2)})
    return result.set_index("Experience Level")


def _by_industry(df: pd.DataFrame) -> pd.DataFrame:
    grp = df.groupby("category")["sal_mid"].mean().round(0)
    result = pd.DataFrame({"Category": grp.index, "Avg Mid Salary (LPA)": (grp.values * 12 / 100_000).round(2)})
    return result.set_index("Category").sort_values("Avg Mid Salary (LPA)", ascending=False)


# ── Salary band card HTML ──────────────────────────────────────────────────────

def _band_card(est: dict, exp_level: str) -> str:
    return f"""
    <div style="background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);
                border-radius:16px;padding:28px 32px;margin:16px 0;color:white">
      <div style="font-size:13px;color:#94a3b8;margin-bottom:6px;text-transform:uppercase;letter-spacing:1px">
        Estimated Salary Band · {exp_level}
      </div>
      <div style="display:flex;align-items:flex-end;gap:20px;flex-wrap:wrap">
        <div>
          <div style="font-size:13px;color:#94a3b8">Minimum</div>
          <div style="font-size:22px;font-weight:700;color:#93c5fd">₹{est['min_lpa']} LPA</div>
          <div style="font-size:12px;color:#64748b">₹{est['min_mo']:,}/mo</div>
        </div>
        <div style="font-size:28px;color:#475569">→</div>
        <div>
          <div style="font-size:13px;color:#94a3b8">Expected</div>
          <div style="font-size:32px;font-weight:800;color:#34d399">₹{est['mid_lpa']} LPA</div>
          <div style="font-size:12px;color:#64748b">₹{est['mid_mo']:,}/mo</div>
        </div>
        <div style="font-size:28px;color:#475569">→</div>
        <div>
          <div style="font-size:13px;color:#94a3b8">Maximum</div>
          <div style="font-size:22px;font-weight:700;color:#f9a8d4">₹{est['max_lpa']} LPA</div>
          <div style="font-size:12px;color:#64748b">₹{est['max_mo']:,}/mo</div>
        </div>
      </div>
      <div style="margin-top:16px;font-size:12px;color:#64748b">
        Based on {est['n_jobs']} matching jobs · Avg skill overlap: {est['avg_overlap']} skills matched
      </div>
    </div>"""


# ── Main render ────────────────────────────────────────────────────────────────

def render_salary_estimator(user_email: str):
    st.subheader("💰 Salary Estimator")
    st.caption("Real salary data from your jobs dataset — no AI, just data.")

    resume_text = st.session_state.get("resume_text", "") or ""
    if not resume_text.strip():
        st.warning("⚠️ Upload your resume first to get a personalized salary estimate.")
        return

    skills         = st.session_state.get("resume_skills",      []) or []
    category       = st.session_state.get("resume_category",    "") or "General"
    subcategory    = st.session_state.get("resume_subcategory", "") or ""
    cat_label      = st.session_state.get("resume_cat_label",   "") or category

    # ── Show detected specialization ──
    if subcategory:
        st.markdown(
            f'<div style="background:#1d3a6e;border:1px solid #3b82f6;border-radius:10px;'
            f'padding:10px 16px;margin-bottom:12px;font-size:13px;color:#93c5fd">'
            f'🏷️ Detected Specialization: <strong style="color:#f0f6fc">{cat_label}</strong>'
            f'</div>',
            unsafe_allow_html=True,
        )

    try:
        df = _load_salary_df()
    except Exception as e:
        st.error(f"Could not load salary data: {e}")
        return

    # ── Controls ──
    col1, col2 = st.columns([2, 1])
    with col1:
        exp_level = st.selectbox(
            "Your experience level",
            ["Fresher", "Intern", "Junior", "Mid", "Senior"],
            index=0,
        )
    with col2:
        selected_category = st.selectbox(
            "Category",
            sorted(df["category"].unique().tolist()),
            index=sorted(df["category"].unique().tolist()).index(category)
                  if category in df["category"].unique() else 0,
        )

    # ── Estimate ──
    est = _estimate_for_candidate(df, selected_category, skills, exp_level)
    st.markdown(_band_card(est, exp_level), unsafe_allow_html=True)

    # ── Skill impact tip ──
    overlap = est["avg_overlap"]
    if overlap < 3:
        st.warning("💡 Your skill overlap with jobs in this category is low. Adding more relevant skills can push your salary band up significantly.")
    elif overlap < 6:
        st.info("💡 Moderate skill overlap. Adding 3–5 more domain skills can move you to the upper band.")
    else:
        st.success("✅ Strong skill overlap — you're well positioned for the upper salary range.")

    st.divider()

    # ── Charts ──
    tab1, tab2, tab3 = st.tabs(["📊 By Role", "📈 By Experience", "🌐 By Category"])

    with tab1:
        st.markdown(f"#### Salary by Job Title — {selected_category}")
        role_df = _by_role(df, selected_category)
        if len(role_df) > 0:
            st.bar_chart(role_df["Mid (LPA)"], use_container_width=True)
            with st.expander("📋 Full table"):
                st.dataframe(role_df, use_container_width=True)
        else:
            st.info("No data for this category.")

    with tab2:
        st.markdown(f"#### Avg Salary by Experience Level — {selected_category}")
        exp_df = _by_experience(df, selected_category)
        if len(exp_df) > 0:
            st.bar_chart(exp_df, use_container_width=True)
            st.caption("Salary progression from Intern → Senior in your target category.")
        else:
            st.info("No data available.")

    with tab3:
        st.markdown("#### Avg Mid Salary by Category (All Jobs)")
        ind_df = _by_industry(df)
        st.bar_chart(ind_df, use_container_width=True)
        st.caption("Compare average salaries across all 8 industries in the dataset.")

    st.divider()

    # ── Market insights ──
    st.markdown("### 📌 Market Insights")
    top_roles = _by_role(df, selected_category).head(3)
    if len(top_roles) > 0:
        st.markdown(f"**Top paying roles in {selected_category}:**")
        for title, row in top_roles.iterrows():
            st.markdown(f"- **{title}** → ₹{row['Mid (LPA)']} LPA (mid)")

    # Fresher vs Senior gap
    exp_data = _by_experience(df, selected_category)
    if "Fresher" in exp_data.index and "Senior" in exp_data.index:
        fresher_sal = exp_data.loc["Fresher", "Avg Mid Salary (LPA)"]
        senior_sal  = exp_data.loc["Senior",  "Avg Mid Salary (LPA)"]
        growth = round(((senior_sal - fresher_sal) / fresher_sal) * 100) if fresher_sal > 0 else 0
        st.markdown(f"**Salary growth potential:** Fresher (₹{fresher_sal} LPA) → Senior (₹{senior_sal} LPA) = **{growth}% growth**")