"""
Employer Analytics — modules/employer_analytics.py
===================================================
Gives employers a deep-dive dashboard on their posted jobs, candidate
quality, skill demand, and hiring funnel — all driven from the live DB.

Tab placement : ui_employer.py → option "Analytics"
Icon          : graph-up
Called as     : from modules.employer_analytics import render_employer_analytics
Usage         : render_employer_analytics(employer_email)
"""

import re
import streamlit as st
import pandas as pd
from collections import Counter
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import STRONG_MATCH, MODERATE_MATCH, JOBS_CSV
from modules.db import get_conn


# ── data helpers ──────────────────────────────────────────────────────

def _get_employer_data(employer_email: str) -> dict:
    """Pull all jobs + applications for this employer in one go."""
    conn = get_conn()

    jobs_df = pd.read_sql_query(
        "SELECT * FROM jobs WHERE employer_email=? ORDER BY created_at DESC",
        conn, params=(employer_email,)
    )
    apps_df = pd.read_sql_query(
        """SELECT a.* FROM applications a
           WHERE a.employer_email=?
           ORDER BY a.applied_at DESC""",
        conn, params=(employer_email,)
    )
    conn.close()

    jobs_df = jobs_df.fillna("")
    apps_df = apps_df.fillna("")
    if "score" in apps_df.columns:
        apps_df["score"] = pd.to_numeric(apps_df["score"], errors="coerce").fillna(0.0)

    return {"jobs": jobs_df, "apps": apps_df}


def _safe_float(x, default=0.0):
    try: return float(x)
    except Exception: return default


def _badge(score: float) -> str:
    if score >= STRONG_MATCH:   return "🟢 Strong"
    if score >= MODERATE_MATCH: return "🟡 Moderate"
    return "🔴 Weak"


def _color_for_score(pct: float) -> str:
    if pct >= STRONG_MATCH:   return "#1D9E75"
    if pct >= MODERATE_MATCH: return "#BA7517"
    return "#A32D2D"


def _skill_counter_from_text(skills_text: str) -> list:
    return [s.strip().lower() for s in re.split(r"[,|;/\n]+", str(skills_text)) if s.strip()]


# ── KPI card helper ───────────────────────────────────────────────────

def _kpi(label: str, value, subtitle: str = "", color: str = ""):
    color_style = f"color:{color};" if color else ""
    st.markdown(
        f'<div style="background:var(--color-background-secondary);'
        f'border-radius:10px;padding:14px 16px;text-align:center">'
        f'<div style="font-size:12px;color:var(--color-text-secondary);margin-bottom:4px">{label}</div>'
        f'<div style="font-size:26px;font-weight:500;{color_style}">{value}</div>'
        f'<div style="font-size:11px;color:var(--color-text-secondary)">{subtitle}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── main UI ───────────────────────────────────────────────────────────

def render_employer_analytics(employer_email: str):
    st.subheader("📊 Employer Analytics")
    st.caption("Real-time insights from your posted jobs and received applications.")

    data     = _get_employer_data(employer_email)
    jobs_df  = data["jobs"]
    apps_df  = data["apps"]

    if jobs_df.empty:
        st.info("📌 Post at least one job to see analytics.")
        return

    # ════════════════════════ OVERVIEW KPIs ══════════════════════════
    st.markdown("### 🏠 Overview")

    total_jobs  = len(jobs_df)
    open_jobs   = int((jobs_df["status"] == "open").sum()) if "status" in jobs_df.columns else 0
    total_apps  = len(apps_df)
    strong_apps = int((apps_df["score"] >= STRONG_MATCH).sum()) if not apps_df.empty else 0
    shortlisted = int((apps_df["status"] == "Shortlisted").sum()) if not apps_df.empty and "status" in apps_df.columns else 0
    avg_score   = round(apps_df["score"].mean() * 100, 1) if not apps_df.empty else 0.0
    selected_cnt= int((apps_df["status"] == "Selected").sum()) if not apps_df.empty and "status" in apps_df.columns else 0
    rejected_cnt= int((apps_df["status"] == "Rejected").sum()) if not apps_df.empty and "status" in apps_df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: _kpi("Total Jobs",     total_jobs,  f"{open_jobs} open")
    with c2: _kpi("Applications",   total_apps,  f"avg score {avg_score}%")
    with c3: _kpi("Strong Matches", strong_apps, f"≥{int(STRONG_MATCH*100)}% score",  color="#1D9E75")
    with c4: _kpi("Shortlisted",    shortlisted, f"{selected_cnt} selected")

    st.markdown("---")

    # ════════════════════════ FUNNEL ══════════════════════════════════
    if not apps_df.empty and "status" in apps_df.columns:
        st.markdown("### 🔽 Hiring Funnel")

        funnel_order  = ["Applied", "Shortlisted", "Interview", "Selected", "Rejected"]
        status_counts = apps_df["status"].value_counts().to_dict()

        funnel_rows = []
        for stage in funnel_order:
            cnt = status_counts.get(stage, 0)
            pct = round(cnt / max(total_apps, 1) * 100, 1)
            funnel_rows.append({"Stage": stage, "Count": cnt, "Pct": pct})

        max_cnt = max((r["Count"] for r in funnel_rows), default=1)
        stage_colors = {
            "Applied":    "#185FA5",
            "Shortlisted":"#1D9E75",
            "Interview":  "#BA7517",
            "Selected":   "#0F6E56",
            "Rejected":   "#A32D2D",
        }
        for row in funnel_rows:
            bar_w = int(row["Count"] / max(max_cnt, 1) * 100)
            color = stage_colors.get(row["Stage"], "#888")
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">'
                f'<div style="width:110px;font-size:13px;font-weight:500">{row["Stage"]}</div>'
                f'<div style="flex:1;height:22px;background:var(--color-background-secondary);border-radius:4px;overflow:hidden">'
                f'<div style="width:{bar_w}%;height:100%;background:{color};border-radius:4px"></div></div>'
                f'<div style="width:60px;font-size:13px;text-align:right">{row["Count"]} ({row["Pct"]}%)</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

    # ════════════════════════ PER-JOB BREAKDOWN ══════════════════════
    st.markdown("### 💼 Per-Job Performance")

    if not apps_df.empty and "job_id" in apps_df.columns and "job_id" in jobs_df.columns:
        job_stats = []
        for _, jrow in jobs_df.iterrows():
            jid  = str(jrow["job_id"])
            j_apps = apps_df[apps_df["job_id"].astype(str) == f"db_{jid}"]
            if j_apps.empty:
                j_apps = apps_df[apps_df["job_id"].astype(str).str.endswith(jid)]
            n     = len(j_apps)
            avg   = round(j_apps["score"].mean() * 100, 1) if n > 0 else 0.0
            strong= int((j_apps["score"] >= STRONG_MATCH).sum()) if n > 0 else 0
            short = int((j_apps["status"] == "Shortlisted").sum()) if n > 0 else 0
            job_stats.append({
                "Job Title": jrow.get("job_title", ""),
                "Status":    jrow.get("status", ""),
                "Category":  jrow.get("category", ""),
                "Applications": n,
                "Avg Score %":  avg,
                "Strong":    strong,
                "Shortlisted": short,
            })

        stats_df = pd.DataFrame(job_stats)
        if not stats_df.empty:
            st.dataframe(
                stats_df.sort_values("Applications", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("No applications received yet.")

    st.markdown("---")

    # ════════════════════════ SCORE DISTRIBUTION ══════════════════════
    if not apps_df.empty:
        st.markdown("### 📈 Candidate Score Distribution")

        bins   = [0, 0.20, 0.40, 0.60, 0.70, 0.85, 1.01]
        labels = ["0-20%", "20-40%", "40-60%", "60-70%", "70-85%", "85-100%"]
        counts = [0] * len(labels)
        for sc in apps_df["score"]:
            for i in range(len(bins) - 1):
                if bins[i] <= _safe_float(sc) < bins[i + 1]:
                    counts[i] += 1
                    break

        dist_df = pd.DataFrame({"Score Range": labels, "Candidates": counts})
        st.bar_chart(dist_df.set_index("Score Range"))

        # Badge summary
        b1, b2, b3 = st.columns(3)
        w_strong   = int((apps_df["score"] >= STRONG_MATCH).sum())
        w_moderate = int(((apps_df["score"] >= MODERATE_MATCH) & (apps_df["score"] < STRONG_MATCH)).sum())
        w_weak     = int((apps_df["score"] < MODERATE_MATCH).sum())
        with b1:
            st.markdown(
                f'<div style="background:#E1F5EE;border-radius:10px;padding:10px;text-align:center">'
                f'<div style="font-size:20px;font-weight:500;color:#085041">{w_strong}</div>'
                f'<div style="font-size:12px;color:#0F6E56">🟢 Strong Match</div></div>',
                unsafe_allow_html=True)
        with b2:
            st.markdown(
                f'<div style="background:#FAEEDA;border-radius:10px;padding:10px;text-align:center">'
                f'<div style="font-size:20px;font-weight:500;color:#633806">{w_moderate}</div>'
                f'<div style="font-size:12px;color:#854F0B">🟡 Moderate Match</div></div>',
                unsafe_allow_html=True)
        with b3:
            st.markdown(
                f'<div style="background:#FCEBEB;border-radius:10px;padding:10px;text-align:center">'
                f'<div style="font-size:20px;font-weight:500;color:#501313">{w_weak}</div>'
                f'<div style="font-size:12px;color:#A32D2D">🔴 Weak Match</div></div>',
                unsafe_allow_html=True)

        st.markdown("---")

    # ════════════════════════ SKILLS DEMANDED ════════════════════════
    st.markdown("### 🔧 Skills You're Demanding")
    st.caption("Aggregated from required skills across all your posted jobs.")

    jd_skill_counter: Counter = Counter()
    for _, jrow in jobs_df.iterrows():
        for s in _skill_counter_from_text(jrow.get("skills", "")):
            if s:
                jd_skill_counter[s] += 1

    if jd_skill_counter:
        top_n    = st.slider("Show top N skills", 5, 30, 10, key="ea_skill_slider")
        top_skills = jd_skill_counter.most_common(top_n)
        sd_df    = pd.DataFrame(top_skills, columns=["Skill", "Jobs requiring it"])
        st.bar_chart(sd_df.set_index("Skill"))
    else:
        st.info("Add skills when posting jobs to see this chart.")

    st.markdown("---")

    # ════════════════════════ CANDIDATE SKILL SUPPLY ═════════════════
    if not apps_df.empty and "resume_skills" in apps_df.columns:
        st.markdown("### 🧠 Skills Candidates Are Bringing")
        st.caption("What your applicants actually have — useful for calibrating JD requirements.")

        cand_skill_counter: Counter = Counter()
        for rs in apps_df["resume_skills"].dropna():
            for s in _skill_counter_from_text(str(rs)):
                if s:
                    cand_skill_counter[s] += 1

        if cand_skill_counter:
            top_cand = cand_skill_counter.most_common(10)
            cs_df    = pd.DataFrame(top_cand, columns=["Skill", "Candidates with it"])
            st.bar_chart(cs_df.set_index("Skill"))

            # Gap analysis
            demanded = set(jd_skill_counter.keys())
            supplied = set(cand_skill_counter.keys())
            gap      = demanded - supplied

            if gap:
                st.markdown("**⚠️ Skills you demand but applicants rarely have:**")
                st.write("  ".join([f"`{s}`" for s in sorted(gap)[:20]]))
                st.caption("Consider either lowering the bar on these or broadening your outreach.")
            else:
                st.success("✅ All your required skills are well covered by applicants.")

        st.markdown("---")

    # ════════════════════════ APPLICATIONS OVER TIME ═════════════════
    if not apps_df.empty and "applied_at" in apps_df.columns:
        st.markdown("### 📅 Applications Over Time")
        dates = [str(d)[:10] for d in apps_df["applied_at"] if d]
        if dates:
            date_df = pd.DataFrame(Counter(dates).items(), columns=["Date", "Applications"])
            date_df = date_df.sort_values("Date")
            st.line_chart(date_df.set_index("Date"))

    st.markdown("---")

    # ════════════════════════ CSV EXPORT ═════════════════════════════
    st.markdown("### 📥 Export Data")
    if not apps_df.empty:
        export_cols = [c for c in ["user_email","job_title","company","score","status","applied_at"]
                       if c in apps_df.columns]
        export_df   = apps_df[export_cols].copy()
        if "score" in export_df.columns:
            export_df["score"] = (export_df["score"] * 100).round(1).astype(str) + "%"
        st.download_button(
            "⬇️ Download Applications CSV",
            export_df.to_csv(index=False),
            file_name=f"applications_{employer_email.split('@')[0]}.csv",
            mime="text/csv",
            use_container_width=True,
        )