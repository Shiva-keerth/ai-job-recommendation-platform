import re
import streamlit as st
from modules.chatbot import render_chatbot
from streamlit_option_menu import option_menu
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import STRONG_MATCH, MODERATE_MATCH
from modules.employer_analytics import render_employer_analytics
from modules.jobs_store import init_jobs_table, save_job, get_employer_jobs
from modules.applications_store import (
    ensure_feedback_columns, get_employer_applications,
    get_applications_for_job, update_application_status,
)
from modules.theme import (
    topbar, page_header, section_header, render_stat_row,
    empty_state, skill_chips, badge, card, score_bar_html, match_badge,
    MUTED, SUCCESS, WARNING, INFO, PRIMARY, SURFACE, CARD_BORDER, TEXT,
    T, render_theme_toggle,
)


def _safe_float(x, default=0.0):
    try: return float(x)
    except Exception: return float(default)


def _match_badge(score):
    if score >= STRONG_MATCH:   return badge("Strong",   "selected")
    if score >= MODERATE_MATCH: return badge("Moderate", "shortlisted")
    return badge("Weak", "rejected")


def _score_color(score):
    if score >= STRONG_MATCH:   return SUCCESS
    if score >= MODERATE_MATCH: return WARNING
    return "#ef4444"


def employer_dashboard():
    init_jobs_table()
    ensure_feedback_columns()

    employer_email = st.session_state.get("user_email", "")
    if not employer_email:
        st.error("❌ Please login as Employer."); return

    name = employer_email.split("@")[0].replace(".", " ").title()

    # ── Sidebar ──────────────────────────────────────────────────────────
    with st.sidebar:
        p = T()
        render_theme_toggle()
        st.markdown("<hr style='margin:8px 0'>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="padding:4px 0 16px">
            <div style="font-size:11px;color:{p['MUTED']};text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px">Employer</div>
            <div style="font-size:15px;font-weight:700;color:{p['TEXT_HEADING']}">{name}</div>
            <div style="font-size:11px;color:{p['MUTED']}">{employer_email}</div>
        </div>""", unsafe_allow_html=True)

        selected = option_menu(
            menu_title="Navigation",
            options=["Home","Post Job","My Jobs","Applications",
                     "AI Leaderboard","Compare","Analytics"],
            icons=["house-fill","plus-circle-fill","briefcase-fill","inbox-fill",
                   "trophy-fill","bar-chart-fill","graph-up"],
            default_index=0,
            styles={
                "container": {"padding":"6px 4px","background":"transparent"},
                "icon":      {"font-size":"15px"},
                "nav-link":  {"font-size":"13px","padding":"9px 12px",
                              "border-radius":"8px","margin":"1px 0","color":"#8b949e"},
                "nav-link-selected": {"background":"rgba(232,57,77,0.12)",
                                      "color":"#E8394D","font-weight":"600"},
            }
        )
        st.markdown("<div style='margin-top:20px'>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            for k in ["logged_in","user_email","role","auth_page"]:
                st.session_state[k] = None if k != "logged_in" else False
            st.session_state.auth_page = "Login"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    topbar("employer", name, selected)
    render_chatbot(role="employer")

    jobs = get_employer_jobs(employer_email)
    apps = get_employer_applications(employer_email)

    # ══════════════════════════════════════════════════════════════════════
    # HOME
    # ══════════════════════════════════════════════════════════════════════
    if selected == "Home":
        page_header("Employer Dashboard", "Post jobs · Track applications · Shortlist with AI", "🏢")

        total_jobs = len(jobs)
        open_jobs  = sum(1 for j in jobs if str(j[11]).lower() == "open")
        total_apps = len(apps)
        strong     = sum(1 for a in apps if _safe_float(a[5]) >= STRONG_MATCH)

        render_stat_row([
            {"label": "Total Jobs",           "value": total_jobs, "color": INFO},
            {"label": "Open Jobs",            "value": open_jobs,  "color": SUCCESS},
            {"label": "Applications",         "value": total_apps, "color": WARNING},
            {"label": "Strong Matches ≥70%",  "value": strong,     "color": "#a78bfa"},
        ])

        section_header("Quick Actions")
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px">
            <div style="background:{T()['SURFACE']};border:1px solid {T()['INFO']};border-radius:14px;padding:20px 22px">
                <div style="font-size:22px;margin-bottom:8px">📌</div>
                <div style="font-size:14px;font-weight:700;color:{T()['TEXT_HEADING']};margin-bottom:4px">Post a Job</div>
                <div style="font-size:12px;color:{T()['MUTED']}">Publish a new opening and start receiving AI-matched candidates instantly.</div>
            </div>
            <div style="background:{T()['SURFACE']};border:1px solid {T()['WARNING']};border-radius:14px;padding:20px 22px">
                <div style="font-size:22px;margin-bottom:8px">📥</div>
                <div style="font-size:14px;font-weight:700;color:{T()['TEXT_HEADING']};margin-bottom:4px">Review Applications</div>
                <div style="font-size:12px;color:{T()['MUTED']}">View AI scores, update statuses, and send feedback to candidates.</div>
            </div>
            <div style="background:{T()['SURFACE']};border:1px solid #a78bfa;border-radius:14px;padding:20px 22px">
                <div style="font-size:22px;margin-bottom:8px">🏆</div>
                <div style="font-size:14px;font-weight:700;color:{T()['TEXT_HEADING']};margin-bottom:4px">AI Leaderboard</div>
                <div style="font-size:12px;color:{T()['MUTED']}">AI-ranked candidates per job with skill match breakdown.</div>
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        col_l, col_r = st.columns(2)

        with col_l:
            section_header("Recent Jobs")
            if not jobs:
                empty_state("📋", "No jobs posted yet", "Use Post Job to publish your first opening.")
            else:
                for j in jobs[:5]:
                    status_color = SUCCESS if str(j[11]).lower() == "open" else "#ef4444"
                    st.markdown(f"""
                    <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-radius:10px;
                                padding:12px 14px;margin-bottom:8px;
                                display:flex;justify-content:space-between;align-items:center">
                        <div>
                            <div style="font-size:13px;font-weight:600;color:{T()['TEXT_HEADING']}">{j[2]}</div>
                            <div style="font-size:11px;color:{T()['MUTED']}">{j[3]} · {j[8]}</div>
                        </div>
                        <span style="background:{status_color}22;color:{status_color};
                                     border:1px solid {status_color}44;padding:2px 8px;
                                     border-radius:99px;font-size:10px;font-weight:700">
                            {str(j[11]).upper()}
                        </span>
                    </div>""", unsafe_allow_html=True)

        with col_r:
            section_header("Recent Applications")
            if not apps:
                empty_state("📭", "No applications yet", "Applications will appear here once candidates apply.")
            else:
                for a in apps[:5]:
                    score_f = _safe_float(a[5])
                    sc = _score_color(score_f)
                    st.markdown(f"""
                    <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-radius:10px;
                                padding:12px 14px;margin-bottom:8px;
                                display:flex;justify-content:space-between;align-items:center">
                        <div>
                            <div style="font-size:13px;font-weight:600;color:{T()['TEXT_HEADING']}">{str(a[1]).split('@')[0]}</div>
                            <div style="font-size:11px;color:{T()['MUTED']}">{a[3]}</div>
                        </div>
                        <div style="text-align:right">
                            <div style="font-size:15px;font-weight:700;color:{sc}">{round(score_f*100,1)}%</div>
                            <div style="font-size:10px;color:{T()['MUTED']}">{a[6]}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # POST JOB
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Post Job":
        page_header("Post a New Job", "Fill in the details to publish your opening", "📌")

        with st.form("post_job_form", clear_on_submit=True):
            section_header("Basic Details")
            c1, c2 = st.columns(2)
            with c1:
                job_title = st.text_input("Job Title *", placeholder="e.g. Data Scientist")
                industry  = st.text_input("Industry", placeholder="e.g. IT, Finance, Healthcare")
                location  = st.text_input("Location", placeholder="e.g. Bangalore, India")
            with c2:
                category = st.selectbox("Category *", [
                    # Software Engineering
                    "Backend & Full Stack",
                    "Frontend & Mobile",
                    "DevOps & Cloud",
                    "AI & ML Engineering",
                    # Data & Analytics
                    "Data Science & ML",
                    "Data Engineering & BI",
                    "Business & Product Analytics",
                    # Finance & Accounting
                    "Accounting & Audit",
                    "Financial Planning & Risk",
                    "Treasury & Compliance",
                    # Marketing & Sales
                    "Digital Marketing",
                    "Brand & Content",
                    "Sales & CRM",
                    # Human Resources
                    "Talent & Recruitment",
                    "HR Operations & Analytics",
                    "HR Business Partnering",
                    # Healthcare
                    "Clinical & Medical",
                    "Pharma & Life Sciences",
                    "Health IT & Informatics",
                    "Public Health & Administration",
                    # Operations & Supply Chain
                    "Logistics & Warehousing",
                    "Supply Chain & Procurement",
                    "Operations & Quality",
                    # Mechanical & Manufacturing
                    "Mechanical Design & CAD",
                    "Manufacturing & Production",
                    "Quality & Maintenance",
                    "Automation & Robotics",
                ])
                work_mode = st.selectbox("Work Mode", ["Onsite","Hybrid","Remote"])
                exp_level = st.selectbox("Experience Level", ["Fresher","Junior","Mid","Senior","Intern"])

            section_header("Skills & Compensation")
            skills_raw = st.text_area(
                "Required Skills * (comma-separated)",
                placeholder="e.g. python, sql, pandas, machine learning, power bi",
                height=90,
            )
            salary = st.text_input("Salary Range (optional)", placeholder="e.g. ₹8,00,000 – ₹14,00,000 per year")

            section_header("Job Description")
            description = st.text_area(
                "Describe the role, responsibilities, and requirements",
                height=130,
                placeholder="We are looking for a skilled data professional to join our analytics team...",
            )

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🚀 Publish Job", type="primary", use_container_width=True)

            if submitted:
                if not job_title.strip() or not skills_raw.strip():
                    st.warning("⚠️ Job Title and Skills are required.")
                else:
                    norm_skills = ", ".join([
                        s.strip().lower()
                        for s in re.split(r"[,\|;/\n]+", skills_raw)
                        if s.strip()
                    ])
                    ok, msg = save_job(employer_email, dict(
                        job_title=job_title.strip(), category=category, industry=industry.strip(),
                        skills=norm_skills, location=location.strip(), work_mode=work_mode,
                        experience_level=exp_level, salary_range=salary.strip(),
                        description=description.strip(),
                    ))
                    st.success(msg) if ok else st.error(msg)

    # ══════════════════════════════════════════════════════════════════════
    # MY JOBS
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "My Jobs":
        page_header("My Posted Jobs", "Manage your active and closed job listings", "📂")

        if not jobs:
            empty_state("📋", "No jobs posted yet",
                        "Click Post Job in the sidebar to publish your first opening.",
                        "→ Post your first job"); return

        open_j   = [j for j in jobs if str(j[11]).lower() == "open"]
        closed_j = [j for j in jobs if str(j[11]).lower() != "open"]

        tab1, tab2 = st.tabs([f"🟢 Open ({len(open_j)})", f"🔴 Closed ({len(closed_j)})"])

        def _job_card(j):
            st.markdown(f"""
            <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-radius:12px;
                        padding:18px 20px;margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                        <div style="font-size:16px;font-weight:700;color:{T()['TEXT_HEADING']};margin-bottom:4px">
                            {j[2]}
                        </div>
                        <div style="font-size:12px;color:{T()['MUTED']}">
                            🆔 db_{j[0]} &nbsp;·&nbsp; 📂 {j[3]} &nbsp;·&nbsp; 🏭 {j[4] or '—'}
                            &nbsp;·&nbsp; 📍 {j[6] or '—'} &nbsp;·&nbsp; {j[7]} &nbsp;·&nbsp; {j[8]}
                        </div>
                    </div>
                    <div style="font-size:11px;color:{T()['MUTED']};margin-top:2px">Posted: {str(j[12])[:10]}</div>
                </div>
                <div style="margin-top:10px;font-size:12px;color:{T()['MUTED']}">
                    <strong style="color:#8b949e">Skills:</strong> {j[5][:120]}{'...' if len(str(j[5]))>120 else ''}
                </div>
                {"<div style='margin-top:6px;font-size:12px;color:"+MUTED+"'>💰 "+str(j[9])+"</div>" if j[9] else ""}
            </div>""", unsafe_allow_html=True)

        with tab1:
            if not open_j:
                empty_state("🟢", "No open jobs", "All your jobs are closed.")
            for j in open_j: _job_card(j)

        with tab2:
            if not closed_j:
                empty_state("🔴", "No closed jobs", "All your jobs are still open.")
            for j in closed_j: _job_card(j)

    # ══════════════════════════════════════════════════════════════════════
    # APPLICATIONS
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Applications":
        page_header("Applications Received", "Review candidates, update statuses, send feedback", "📥")

        if not apps:
            empty_state("📭", "No applications yet",
                        "Applications appear here once candidates apply to your posted jobs."); return

        df = pd.DataFrame(apps, columns=[
            "App ID","Candidate","Job ID","Job Title","Company",
            "Score","Status","Applied At","Rating","Comment","Updated At",
            "Job Source","Employer Email",
        ])
        df["Score"] = pd.to_numeric(df["Score"], errors="coerce").fillna(0.0)

        # ── Filters ──
        fc1, fc2, fc3 = st.columns([1, 1, 2])
        with fc1:
            status_f = st.selectbox("Status", ["All","Applied","Shortlisted","Interview","Selected","Rejected"])
        with fc2:
            sort_by  = st.selectbox("Sort by", ["Score ↓","Newest First"])
        with fc3:
            q = st.text_input("Search candidate email", placeholder="Search...")

        fdf = df.copy()
        if status_f != "All": fdf = fdf[fdf["Status"] == status_f]
        if q.strip():         fdf = fdf[fdf["Candidate"].str.contains(q.strip(), case=False, na=False)]
        fdf = fdf.sort_values("Score" if sort_by == "Score ↓" else "Applied At", ascending=False)

        # ── Summary stats ──
        render_stat_row([
            {"label": "Showing",          "value": len(fdf),                                   "color": INFO},
            {"label": "Avg Score",        "value": f"{round(fdf['Score'].mean()*100,1)}%",     "color": WARNING},
            {"label": "Strong (≥70%)",    "value": int((fdf["Score"]>=0.70).sum()),             "color": SUCCESS},
            {"label": "Shortlisted",      "value": int((fdf["Status"]=="Shortlisted").sum()),   "color": "#a78bfa"},
        ])

        # ── Table ──
        view = fdf[["App ID","Candidate","Job Title","Score","Status","Applied At"]].copy()
        view["Score"] = (view["Score"]*100).round(1).astype(str) + "%"
        st.dataframe(view, use_container_width=True, hide_index=True)

        # ── Status update panel ──
        st.divider()
        section_header("Update Application Status", "Select an application to update its status and add feedback")

        app_map = {
            f"#{r['App ID']} · {r['Candidate']} · {r['Job Title']}": int(r["App ID"])
            for _, r in fdf.iterrows()
        }
        if not app_map:
            st.info("No applications match the current filters."); return

        sel_label = st.selectbox("Select application", list(app_map.keys()))
        sel_id    = app_map[sel_label]
        row       = df[df["App ID"] == sel_id].iloc[0]
        score_f   = _safe_float(row["Score"])

        st.markdown(f"""
        <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-left:3px solid {_score_color(score_f)};
                    border-radius:10px;padding:14px 18px;margin:12px 0">
            <div style="font-size:13px;color:{T()['MUTED']}">
                👤 <strong style="color:{T()['TEXT_HEADING']}">{row['Candidate']}</strong>
                &nbsp;·&nbsp; 💼 {row['Job Title']}
                &nbsp;·&nbsp; Score: <strong style="color:{_score_color(score_f)}">{round(score_f*100,1)}%</strong>
                &nbsp;·&nbsp; {_match_badge(score_f)}
            </div>
        </div>""", unsafe_allow_html=True)

        statuses = ["Applied","Shortlisted","Interview","Selected","Rejected"]
        col1, col2 = st.columns(2)
        with col1:
            new_status = st.selectbox("Set Status", statuses,
                index=statuses.index(row["Status"]) if row["Status"] in statuses else 0)
        with col2:
            ratings    = ["","1","2","3","4","5"]
            new_rating = st.selectbox("Rating (out of 5)", ratings,
                index=ratings.index(str(row["Rating"])) if str(row["Rating"]) in ratings else 0)

        new_comment = st.text_area("Feedback comment", value=str(row["Comment"] or ""),
                                   placeholder="Add notes or feedback for this candidate...")

        if st.button("💾 Save Update", type="primary", use_container_width=True):
            r_val = None if new_rating == "" else int(new_rating)
            ok, msg = update_application_status(sel_id, new_status, r_val, new_comment.strip())
            st.success(msg) if ok else st.error(msg)
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # AI LEADERBOARD
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "AI Leaderboard":
        page_header("AI Candidate Leaderboard", "Ranked candidates per job with skill match breakdown", "🏆")

        if not jobs:
            empty_state("📋", "No jobs posted", "Post a job first to see candidate rankings."); return

        job_options = {f"db_{j[0]} | {j[2]} — {str(j[11]).upper()}": j for j in jobs}
        sel_label   = st.selectbox("Select Job", list(job_options.keys()))
        job_row     = job_options[sel_label]
        db_job_id   = f"db_{job_row[0]}"
        job_title   = job_row[2]
        job_skills  = str(job_row[5] or "")
        required    = set(s.strip().lower() for s in re.split(r"[,\|;/\n]+", job_skills) if s.strip())

        st.markdown(f"""
        <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-radius:10px;padding:14px 18px;margin-bottom:20px">
            <div style="font-size:15px;font-weight:700;color:{T()['TEXT_HEADING']};margin-bottom:8px">📌 {job_title}</div>
            <div style="font-size:12px;color:{T()['MUTED']};margin-bottom:6px">REQUIRED SKILLS</div>
            {skill_chips(sorted(required), color=INFO)}
        </div>""", unsafe_allow_html=True)

        apps_for_job = get_applications_for_job(employer_email, db_job_id)
        if not apps_for_job:
            empty_state("👥", "No candidates yet", "Candidates who apply to this job will appear here."); return

        sort_by = st.radio("Sort by", ["Score ↓","Newest First"], horizontal=True)
        if sort_by == "Newest First":
            apps_for_job = sorted(apps_for_job, key=lambda x: str(x[7]), reverse=True)
        else:
            apps_for_job = sorted(apps_for_job, key=lambda x: _safe_float(x[5]), reverse=True)

        # Summary table
        lb_rows = []
        for rank, app in enumerate(apps_for_job, 1):
            (app_id, cand_email, job_id, a_title, company, score, status,
             applied_at, rating, comment, updated_at, resume_skills_str, resume_cat) = app
            score_f     = _safe_float(score)
            cand_skills = set(x.strip().lower() for x in str(resume_skills_str or "").split(",") if x.strip())
            matched     = sorted(required & cand_skills)
            missing     = sorted(required - cand_skills)
            lb_rows.append({
                "Rank": rank, "Candidate": cand_email,
                "Score": f"{round(score_f*100,1)}%",
                "Status": status,
                "Matched": len(matched), "Missing": len(missing),
            })

        st.dataframe(pd.DataFrame(lb_rows), use_container_width=True, hide_index=True)
        st.divider()

        # Detailed cards
        section_header("Detailed View")
        for app in apps_for_job:
            (app_id, cand_email, job_id, a_title, company, score, status,
             applied_at, rating, comment, updated_at, resume_skills_str, resume_cat) = app
            score_f     = _safe_float(score)
            cand_skills = set(x.strip().lower() for x in str(resume_skills_str or "").split(",") if x.strip())
            matched     = sorted(required & cand_skills)
            missing     = sorted(required - cand_skills)
            sc          = _score_color(score_f)

            with st.expander(f"{cand_email}  ·  {round(score_f*100,1)}%  ·  {status}"):
                st.markdown(score_bar_html(score_f), unsafe_allow_html=True)

                st.markdown(f"""
                <div style="font-size:12px;color:{T()['MUTED']};margin-bottom:12px">
                    Applied: {str(applied_at)[:16]} &nbsp;·&nbsp; Category: {resume_cat}
                </div>""", unsafe_allow_html=True)

                if score_f >= STRONG_MATCH:
                    st.success("✅ AI Recommendation: Shortlist this candidate")
                elif score_f >= MODERATE_MATCH:
                    st.info("💡 AI Recommendation: Review profile before deciding")
                else:
                    st.warning("⚠️ AI Recommendation: Weak match — consider putting on hold")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**✅ Matched Skills** ({len(matched)})")
                    st.markdown(skill_chips(matched, color=SUCCESS), unsafe_allow_html=True)
                with col2:
                    st.markdown(f"**⚠️ Missing Skills** ({len(missing)})")
                    st.markdown(skill_chips(missing, color="#ef4444"), unsafe_allow_html=True)

                qa1, qa2, qa3 = st.columns(3)
                with qa1:
                    if st.button("⭐ Shortlist", key=f"sl_{app_id}", use_container_width=True, type="primary"):
                        ok, msg = update_application_status(app_id, "Shortlisted", rating, str(comment or ""))
                        st.success(msg) if ok else st.error(msg); st.rerun()
                with qa2:
                    if st.button("📅 Interview", key=f"iv_{app_id}", use_container_width=True):
                        ok, msg = update_application_status(app_id, "Interview", rating, str(comment or ""))
                        st.success(msg) if ok else st.error(msg); st.rerun()
                with qa3:
                    if st.button("❌ Reject", key=f"rj_{app_id}", use_container_width=True):
                        ok, msg = update_application_status(app_id, "Rejected", rating, str(comment or ""))
                        st.success(msg) if ok else st.error(msg); st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # COMPARE
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Compare":
        page_header("Side-by-Side Candidate Comparison", "Compare up to 3 candidates for the same job", "⚖️")

        if not jobs:
            empty_state("📋", "No jobs posted", "Post a job first."); return

        job_options  = {f"db_{j[0]} | {j[2]}": j for j in jobs}
        sel_label    = st.selectbox("Select Job", list(job_options.keys()))
        job_row      = job_options[sel_label]
        db_job_id    = f"db_{job_row[0]}"
        required     = set(s.strip().lower() for s in re.split(r"[,\|;/\n]+", str(job_row[5] or "")) if s.strip())

        apps_for_job = get_applications_for_job(employer_email, db_job_id)
        if not apps_for_job:
            empty_state("👥", "No candidates yet", "Candidates who apply to this job will appear here."); return

        cand_options    = {a[1]: a for a in apps_for_job}
        selected_cands  = st.multiselect(
            "Select 2–3 candidates to compare",
            list(cand_options.keys()), max_selections=3
        )

        if len(selected_cands) < 2:
            st.info("ℹ️ Select at least 2 candidates to compare."); return

        cols = st.columns(len(selected_cands))
        for col, email in zip(cols, selected_cands):
            app = cand_options[email]
            (app_id, cand_email, job_id, a_title, company, score, status,
             applied_at, rating, comment, updated_at, resume_skills_str, resume_cat) = app
            score_f     = _safe_float(score)
            cand_skills = set(x.strip().lower() for x in str(resume_skills_str or "").split(",") if x.strip())
            matched     = sorted(required & cand_skills)
            missing     = sorted(required - cand_skills)
            sc          = _score_color(score_f)

            with col:
                st.markdown(f"""
                <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};
                            border-top:3px solid {sc};border-radius:14px;
                            padding:18px 16px;margin-bottom:12px">
                    <div style="font-size:13px;font-weight:600;color:{T()['TEXT_HEADING']};margin-bottom:4px">
                        {cand_email.split('@')[0]}
                    </div>
                    <div style="font-size:11px;color:{T()['MUTED']};margin-bottom:10px">{cand_email}</div>
                    <div style="font-size:28px;font-weight:800;color:{sc}">{round(score_f*100,1)}%</div>
                    <div style="margin:6px 0">{_match_badge(score_f)}</div>
                    <div style="font-size:11px;color:{T()['MUTED']};margin-top:8px">Status: <strong style="color:#e2e8f0">{status}</strong></div>
                    <div style="font-size:11px;color:{T()['MUTED']}">Category: {resume_cat}</div>
                    <div style="margin-top:10px">
                        <div style="background:#21262d;border-radius:99px;height:5px;overflow:hidden">
                            <div style="width:{round(score_f*100)}%;background:{sc};height:100%;border-radius:99px"></div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

                st.markdown(f"**✅ Matched ({len(matched)})**")
                st.markdown(skill_chips(matched, color=SUCCESS, max_show=10), unsafe_allow_html=True)

                st.markdown(f"**⚠️ Missing ({len(missing)})**")
                st.markdown(skill_chips(missing, color="#ef4444", max_show=10), unsafe_allow_html=True)

                if st.button(f"⭐ Shortlist", key=f"cmp_sl_{app_id}", use_container_width=True, type="primary"):
                    ok, msg = update_application_status(app_id, "Shortlisted", rating, str(comment or ""))
                    st.success(msg) if ok else st.error(msg)

    # ══════════════════════════════════════════════════════════════════════
    # ANALYTICS
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Analytics":
        page_header("Employer Analytics", "Performance insights for your posted jobs", "📊")
        render_employer_analytics(employer_email)