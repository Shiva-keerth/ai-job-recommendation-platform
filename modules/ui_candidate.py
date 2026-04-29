import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SKILL_RESOURCES, STRONG_MATCH, MODERATE_MATCH
from modules.chatbot          import render_chatbot
from modules.resume_scorecard import render_resume_scorecard
from modules.market_predictor import render_market_predictor
from modules.interview_prep   import render_interview_prep
from modules.profile_strength import render_profile_strength
from modules.salary_estimator import render_salary_estimator
from modules.cover_letter     import render_cover_letter
from modules.resume_builder   import render_resume_builder
from modules.theme import (
    topbar, page_header, section_header, render_stat_row,
    empty_state, skill_chips, score_bar_html, match_badge,
    badge, card, MUTED, SUCCESS, WARNING, INFO, PRIMARY,
    SURFACE, CARD_BORDER, T, render_theme_toggle,
)


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _save_resume_to_db(user_email, resume_text, skills, category):
    try:
        from modules.db import get_conn
        conn = get_conn(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO resume_history(user_email,resume_text,extracted_skills,detected_category,uploaded_at) VALUES(?,?,?,?,?)",
            (user_email, resume_text, ", ".join(skills), category, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ); conn.commit(); conn.close()
    except Exception: pass


def _load_latest_resume(user_email):
    try:
        from modules.db import get_conn
        conn = get_conn(); cur = conn.cursor()
        cur.execute(
            "SELECT resume_text,extracted_skills,detected_category FROM resume_history WHERE user_email=? ORDER BY uploaded_at DESC LIMIT 1",
            (user_email,)
        )
        row = cur.fetchone(); conn.close(); return row
    except Exception: return None


# ── Job card ───────────────────────────────────────────────────────────────────

def _render_job_card(row, idx, score, score_mode, user_email, resume_skills, resume_category, key_prefix):
    from modules.applications_store import save_application
    title     = row.get("job_title", "Unknown Role")
    company   = row.get("company",   "Company")
    location  = row.get("location",  "")
    work_mode = row.get("work_mode",  "")
    level     = row.get("experience_level", "")
    salary    = row.get("salary_range", "")
    category  = row.get("category", "")
    industry  = row.get("industry", "")
    posted    = row.get("posted_date", "")
    req_exp   = str(row.get("required_experience_years", "")).strip()
    matched   = row.get("matched_skills", [])
    missing   = row.get("missing_skills",  [])

    exp_label = f"{req_exp} yrs exp" if req_exp not in ["", "0"] else "Fresher"

    # Card container
    p = T()
    card_html = f"""
    <div style="background:{p['SURFACE']};border:1px solid {p['CARD_BORDER']};border-radius:14px;
                padding:22px 24px;margin-bottom:16px;
                border-left:3px solid {'#16a34a' if score>=STRONG_MATCH else ('#d97706' if score>=MODERATE_MATCH else '#ef4444')}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
            <div>
                <div style="font-size:18px;font-weight:700;color:{p['TEXT_HEADING']};margin-bottom:4px">{title}</div>
                <div style="font-size:13px;color:{p['MUTED']}">
                    🏢 <strong style="color:{p['TEXT_HEADING']}">{company}</strong>
                    {"&nbsp;·&nbsp;📍 " + location if location else ""}
                    {"&nbsp;·&nbsp;💰 " + salary if salary else ""}
                    {"&nbsp;·&nbsp;🗓️ " + posted if posted else ""}
                </div>
            </div>
            <div style="text-align:right">
                {match_badge(score)}
            </div>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px">
            {"".join(f'<span style="background:{p["TAG_BG"]};color:{p["MUTED"]};border:1px solid {p["TAG_BORDER"]};padding:2px 8px;border-radius:6px;font-size:11px">{t}</span>' for t in [category, industry, work_mode, level, exp_label] if t)}
        </div>
        {score_bar_html(score)}
    </div>"""
    st.html(card_html)

    # Skills row
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**✅ Matched Skills** ({len(matched)})")
        if matched:
            st.html(skill_chips(matched, color=SUCCESS))
        else:
            st.caption("_None matched_")
    with col2:
        st.markdown(f"**❌ Skills Missing** ({len(missing)})")
        if missing:
            st.html(skill_chips(missing[:12], color="#ef4444"))
            # Learning resource links
            res_links = []
            for m in missing[:12]:
                url = SKILL_RESOURCES.get(m.lower())
                if url:
                    res_links.append(f"[{m}]({url})")
            if res_links:
                st.caption("💡 Learn: " + "  ·  ".join(res_links))
        else:
            st.success("Perfect match — nothing missing!")

    apply_key = f"{key_prefix}_{row.get('job_id', idx)}_{idx}"
    if st.button("✅ Apply Now", key=apply_key, type="primary", use_container_width=True):
        ok, msg = save_application(
            user_email=user_email, job_id=str(row.get("job_id","")),
            job_title=title, company=company, score=float(score),
            job_source=str(row.get("job_source","csv")),
            employer_email=str(row.get("employer_email","")),
            resume_skills=resume_skills, resume_category=resume_category,
        )
        st.success(msg) if ok else st.warning(msg)
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


# ── Main ───────────────────────────────────────────────────────────────────────

def candidate_dashboard(user_email: str):
    name = user_email.split("@")[0].replace(".", " ").title()

    # ── Sidebar ──
    with st.sidebar:
        p = T()
        render_theme_toggle()
        st.markdown("<hr style='margin:8px 0'>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="padding:4px 0 16px">
            <div style="font-size:11px;color:{p['MUTED']};text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px">Candidate</div>
            <div style="font-size:15px;font-weight:700;color:{p['TEXT_HEADING']}">{name}</div>
            <div style="font-size:11px;color:{p['MUTED']}">{user_email}</div>
        </div>""", unsafe_allow_html=True)

        selected = option_menu(
            menu_title="Navigation",
            options=[
                "Home", "Resume Upload", "Recommendations",
                "Applications", "Skill Gap", "Resume Score",
                "Market Trends", "Interview Prep",
                "Profile Strength", "Salary Estimator",
                "Cover Letter", "Resume Builder",
            ],
            icons=[
                "house-fill", "file-earmark-arrow-up-fill", "bullseye",
                "briefcase-fill", "book-fill", "patch-check-fill",
                "graph-up-arrow", "mic-fill",
                "activity", "cash-coin",
                "envelope-paper-fill", "file-earmark-person-fill",
            ],
            default_index=0,
            styles={
                "container": {"padding": "6px 4px", "background": "transparent"},
                "icon":      {"font-size": "15px"},
                "nav-link":  {"font-size": "13px", "padding": "9px 12px",
                              "border-radius": "8px", "margin": "1px 0",
                              "color": "#8b949e"},
                "nav-link-selected": {
                    "background": "rgba(232,57,77,0.12)",
                    "color": "#E8394D", "font-weight": "600",
                },
            }
        )
        st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:20px'>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            for k in ["logged_in","user_email","role","auth_page","resume_text","resume_skills","resume_category","resume_subcategory"]:
                st.session_state[k] = None if k != "logged_in" else False
            st.session_state.auth_page = "Login"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Restore resume ──
    if "resume_text" not in st.session_state or not st.session_state.get("resume_text"):
        saved = _load_latest_resume(user_email)
        if saved:
            st.session_state["resume_text"]     = saved[0]
            st.session_state["resume_skills"]   = [s.strip() for s in saved[1].split(",") if s.strip()]
            st.session_state["resume_category"] = saved[2]

    # ── Topbar ──
    topbar("candidate", name, selected)

    # ── Chatbot ──
    _rs = st.session_state.get("resume_skills",   []) or []
    _rc = st.session_state.get("resume_category", "") or ""
    render_chatbot(user_email=user_email, role="candidate", skills=_rs, category=_rc)

    # ══════════════════════════════════════════════════════════════════════
    # HOME
    # ══════════════════════════════════════════════════════════════════════
    if selected == "Home":
        page_header("AI Job Recommendation", "Upload resume → get matched → apply in one click", "🚀")

        from modules.applications_store import get_user_applications
        apps    = get_user_applications(user_email) or []
        skills  = st.session_state.get("resume_skills", []) or []
        cat     = st.session_state.get("resume_category", "") or "Not detected"
        has_res = bool(st.session_state.get("resume_text", ""))

        render_stat_row([
            {"label": "Applications Sent",  "value": len(apps),
             "delta": "Total applied",       "color": INFO},
            {"label": "Shortlisted",         "value": sum(1 for a in apps if a[4]=="Shortlisted"),
             "delta": "",                    "color": SUCCESS},
            {"label": "Latest Status",       "value": apps[0][4] if apps else "—",
             "delta": apps[0][2] if apps else "", "color": WARNING},
            {"label": "Skills Detected",     "value": len(skills),
             "delta": cat,                   "color": "#a78bfa"},
        ])

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Feature cards — single markdown call avoids Streamlit columns HTML escaping bug
        section_header("Platform Features")
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:12px">
            <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-radius:14px;padding:20px 22px">
                <div style="font-size:24px;margin-bottom:8px">📄</div>
                <div style="font-size:14px;font-weight:700;color:{T()['TEXT_HEADING']};margin-bottom:4px">Resume Analysis</div>
                <div style="font-size:12px;color:{T()['MUTED']}">Automatic skill extraction from your PDF resume with category detection.</div>
            </div>
            <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-radius:14px;padding:20px 22px">
                <div style="font-size:24px;margin-bottom:8px">🎯</div>
                <div style="font-size:14px;font-weight:700;color:{T()['TEXT_HEADING']};margin-bottom:4px">Smart Matching</div>
                <div style="font-size:12px;color:{T()['MUTED']}">AI matches your skills to 1200+ jobs with explainable Recruiter, ATS & Optimistic scores.</div>
            </div>
            <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-radius:14px;padding:20px 22px">
                <div style="font-size:24px;margin-bottom:8px">📚</div>
                <div style="font-size:14px;font-weight:700;color:{T()['TEXT_HEADING']};margin-bottom:4px">Skill Gap</div>
                <div style="font-size:12px;color:{T()['MUTED']}">See missing skills across top matches and get free learning resources instantly.</div>
            </div>
        </div>""", unsafe_allow_html=True)

        if not has_res:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            empty_state("📄", "No resume uploaded yet",
                        "Upload your PDF resume to unlock all features — job matches, salary estimates, and more.",
                        "→ Go to Resume Upload to get started")

        # New features — single markdown grid to avoid Streamlit columns HTML bug
        section_header("New Features", "Recently added to your dashboard")
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:12px">
            <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-top:2px solid {T()['SUCCESS']};
                        border-radius:12px;padding:14px;text-align:center">
                <div style="font-size:20px;margin-bottom:6px">💪</div>
                <div style="font-size:13px;font-weight:700;color:{T()['TEXT_HEADING']};margin-bottom:4px">Profile Strength</div>
                <div style="font-size:11px;color:{T()['MUTED']}">See how competitive your profile is</div>
            </div>
            <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-top:2px solid {T()['WARNING']};
                        border-radius:12px;padding:14px;text-align:center">
                <div style="font-size:20px;margin-bottom:6px">💰</div>
                <div style="font-size:13px;font-weight:700;color:{T()['TEXT_HEADING']};margin-bottom:4px">Salary Estimator</div>
                <div style="font-size:11px;color:{T()['MUTED']}">Real salary bands from 1200+ jobs</div>
            </div>
            <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-top:2px solid {T()['INFO']};
                        border-radius:12px;padding:14px;text-align:center">
                <div style="font-size:20px;margin-bottom:6px">✉️</div>
                <div style="font-size:13px;font-weight:700;color:{T()['TEXT_HEADING']};margin-bottom:4px">Cover Letter</div>
                <div style="font-size:11px;color:{T()['MUTED']}">AI-generated in seconds via Groq</div>
            </div>
            <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-top:2px solid #a78bfa;
                        border-radius:12px;padding:14px;text-align:center">
                <div style="font-size:20px;margin-bottom:6px">📝</div>
                <div style="font-size:13px;font-weight:700;color:{T()['TEXT_HEADING']};margin-bottom:4px">Resume Builder</div>
                <div style="font-size:11px;color:{T()['MUTED']}">Build ATS-friendly resume, download as PDF</div>
            </div>
        </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # RESUME UPLOAD
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Resume Upload":
        page_header("Resume Upload", "Upload your PDF resume to unlock all features", "📄")

        uploaded = st.file_uploader("Drop your resume here (PDF only)", type=["pdf"])

        if uploaded is None:
            saved = _load_latest_resume(user_email)
            if saved:
                skills_saved = [s.strip() for s in saved[1].split(",") if s.strip()]
                st.markdown(f"""
                <div style="background:{T()['SURFACE']};border:1px solid {T()['SUCCESS']};border-radius:14px;padding:20px 22px;margin-bottom:12px">
                    <div style="display:flex;align-items:center;gap:12px">
                        <span style="font-size:28px">✅</span>
                        <div>
                            <div style="font-size:14px;font-weight:700;color:{T()['TEXT_HEADING']}">Resume on file</div>
                            <div style="font-size:12px;color:{T()['MUTED']}">Category: <strong style="color:{T()['TEXT_HEADING']}">{saved[2]}</strong> · {len(skills_saved)} skills detected</div>
                            <div style="font-size:12px;color:{T()['MUTED']};margin-top:2px">Upload a new one to refresh your matches.</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
                st.markdown(skill_chips(skills_saved), unsafe_allow_html=True)
            else:
                empty_state("📄", "No resume uploaded yet",
                            "Upload a PDF resume to get started with AI job matching.",
                            "Supports standard PDF resumes up to 200MB")
            return

        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(uploaded) as pdf:
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
            text = text.strip()
            if not text:
                st.error("❌ Could not extract text from this PDF. Try a different file.")
                return

            from modules.category_detector import detect_full_category
            from modules.skill_extractor import build_skill_vocab_from_jobs, extract_skills
            from config import JOBS_CSV
            vocab    = build_skill_vocab_from_jobs(str(JOBS_CSV))
            skills   = sorted(list(extract_skills(text, vocab)))
            full_cat = detect_full_category(text)
            category = full_cat["label"]

            st.session_state.update({
                "resume_text": text, "resume_skills": skills, "resume_category": category,
                "resume_subcategory": full_cat["sub"],
            })
            _save_resume_to_db(user_email, text, skills, category)

            st.markdown(f"""
            <div style="background:{T()['SURFACE']};border:1px solid {T()['SUCCESS']};border-radius:14px;padding:20px 22px;margin-bottom:12px">
                <div style="display:flex;align-items:center;gap:12px">
                    <span style="font-size:28px">🎉</span>
                    <div>
                        <div style="font-size:15px;font-weight:700;color:{T()['TEXT_HEADING']}">Resume uploaded successfully!</div>
                        <div style="font-size:13px;color:{T()['MUTED']}">
                            Category detected: <strong style="color:#16a34a">{category}</strong>
                            &nbsp;·&nbsp; <strong style="color:{T()['TEXT_HEADING']}">{len(skills)}</strong> skills extracted
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            st.markdown("**Extracted Skills**")
            st.markdown(skill_chips(skills, max_show=40), unsafe_allow_html=True)

            with st.expander("📋 View extracted text"):
                st.text_area("Raw text", text, height=250, label_visibility="collapsed")

        except Exception as e:
            st.error("❌ Resume extraction failed."); st.exception(e)

    # ══════════════════════════════════════════════════════════════════════
    # RECOMMENDATIONS
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Recommendations":
        page_header("Job Recommendations", "AI-matched roles based on your resume skills", "🎯")

        resume_text = st.session_state.get("resume_text", "")
        if not str(resume_text).strip():
            empty_state("📄", "Resume required",
                        "Upload your PDF resume first to see personalized job matches.",
                        "→ Go to Resume Upload"); st.stop()

        from modules.ai_matcher import match_resume_to_jobs
        import pandas as pd

        col_mode, col_info = st.columns([2, 1])
        with col_mode:
            score_mode = st.radio(
                "Scoring perspective",
                ["Recruiter (Realistic)", "Optimistic (Best case)", "ATS (Strict)"],
                horizontal=True, label_visibility="collapsed",
            )
        mode_key = {
            "Recruiter (Realistic)":  "match_recruiter",
            "Optimistic (Best case)": "match_optimistic",
            "ATS (Strict)":           "match_ats",
        }[score_mode]

        with st.spinner("🔍 Matching your profile to jobs..."):
            primary, other, resume_skills, resume_category, resume_subcategory, resume_cat_label = match_resume_to_jobs(resume_text)

        # Store subcategory so profile_strength, salary_estimator, etc. can use it
        st.session_state["resume_subcategory"] = resume_subcategory

        rp = T()
        st.markdown(f"""
        <div style="background:{rp['SURFACE']};border:1px solid {rp['CARD_BORDER']};border-radius:10px;
                    padding:12px 16px;margin-bottom:20px;display:flex;gap:16px;flex-wrap:wrap">
            <span style="font-size:12px;color:{rp['MUTED']}">🎯 Category: <strong style="color:{rp['TEXT_HEADING']}">{resume_cat_label}</strong></span>
            <span style="font-size:12px;color:{rp['MUTED']}">🧠 Skills: <strong style="color:{rp['TEXT_HEADING']}">{len(resume_skills)}</strong></span>
            <span style="font-size:12px;color:{rp['MUTED']}">📋 Mode: <strong style="color:#E8394D">{score_mode}</strong></span>
        </div>""", unsafe_allow_html=True)

        if primary is not None and len(primary) > 0 and mode_key in primary.columns:
            primary = primary.sort_values(mode_key, ascending=False).reset_index(drop=True)
        if other is not None and len(other) > 0 and mode_key in other.columns:
            other = other.sort_values(mode_key, ascending=False).reset_index(drop=True)

        # DB jobs — employer posted jobs
        from modules.jobs_store import get_open_jobs
        from modules.ai_matcher import _score_jobs, _extract_resume_experience_years
        from modules.skill_extractor import build_skill_vocab_from_jobs, extract_skills
        from config import JOBS_CSV
        try:
            db_rows = get_open_jobs()
            if db_rows:
                db_df = pd.DataFrame([dict(r) for r in db_rows]).fillna("")
                db_df["job_source"] = "db"
                if "employer_email" not in db_df.columns: db_df["employer_email"] = ""
                if "company" not in db_df.columns:        db_df["company"] = "Employer Posted"
                db_df["job_id"] = db_df["job_id"].astype(str).apply(lambda x: f"db_{x}")
                vocab     = build_skill_vocab_from_jobs(str(JOBS_CSV))
                res_s     = extract_skills(resume_text, vocab)
                res_years = _extract_resume_experience_years(resume_text)
                scored_db = _score_jobs(db_df, resume_text, res_s, res_years)
                meta = db_df[["job_id","employer_email"]].drop_duplicates("job_id")
                scored_db = scored_db.merge(meta, on="job_id", how="left")
                scored_db["employer_email"] = scored_db["employer_email"].fillna("")
                scored_db["job_source"] = "db"
                scored_db = scored_db.sort_values(mode_key, ascending=False).reset_index(drop=True)
                section_header("🏢 Employer Posted Jobs", "Live openings from employers on the platform")
                if len(scored_db) == 0:
                    empty_state("🏢", "No employer jobs yet", "Check back later for live postings.")
                else:
                    for k, row in scored_db.iterrows():
                        _render_job_card(row, k, float(row.get(mode_key,0)), score_mode,
                                         user_email, list(res_s), resume_category, "db")
            else:
                section_header("🏢 Employer Posted Jobs", "Live openings from employers on the platform")
                empty_state("🏢", "No employer jobs yet", "Employers haven't posted any openings yet.")
        except Exception as e:
            section_header("🏢 Employer Posted Jobs")
            st.warning(f"Could not load employer jobs: {e}")

        section_header("🔥 Primary Matches", f"Top jobs in your category: {resume_cat_label}")
        if primary is None or len(primary) == 0:
            empty_state("🔍", "No matches found", "Try uploading a more detailed resume.")
        else:
            csv_primary = primary[primary["job_source"]=="csv"] if "job_source" in primary.columns else primary
            for idx, row in csv_primary.iterrows():
                _render_job_card(row, idx, float(row.get(mode_key,0)), score_mode,
                                 user_email, resume_skills, resume_category, "primary")

        if other is not None and len(other) > 0:
            section_header("🌍 Cross-Industry Matches", "Roles outside your primary category that still fit your skills")
            csv_other = other[other["job_source"]=="csv"] if "job_source" in other.columns else other
            for jdx, row in csv_other.iterrows():
                _render_job_card(row, jdx, float(row.get(mode_key,0)), score_mode,
                                 user_email, resume_skills, resume_category, "other")

    # ══════════════════════════════════════════════════════════════════════
    # APPLICATIONS
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Applications":
        page_header("My Applications", "Track all your job applications and employer feedback", "📌")

        from modules.applications_store import get_user_applications
        import pandas as pd
        rows = get_user_applications(user_email)

        if not rows:
            empty_state("📭", "No applications yet",
                        "Go to Recommendations, find a strong match, and click Apply.",
                        "→ Your pipeline starts here"); return

        normalized = []
        for r in rows:
            r = list(r)
            while len(r) < 9: r.append("")
            normalized.append(r[:9])
        df = pd.DataFrame(normalized, columns=[
            "Job ID","Job Title","Company","Score","Status",
            "Applied At","Rating","Comment","Updated At"])
        df["Score"] = (df["Score"].astype(float)*100).round(1).astype(str) + "%"

        total      = len(df)
        shortlisted= int((df["Status"]=="Shortlisted").sum())
        interview  = int((df["Status"]=="Interview").sum())
        selected_c = int((df["Status"]=="Selected").sum())

        render_stat_row([
            {"label": "Total Applied",  "value": total,       "color": INFO},
            {"label": "Shortlisted",    "value": shortlisted, "color": WARNING},
            {"label": "Interview",      "value": interview,   "color": "#a78bfa"},
            {"label": "Selected",       "value": selected_c,  "color": SUCCESS},
        ])

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Table with colored status
        display_df = df[["Job Title","Company","Score","Status","Applied At"]].copy()
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        if df[["Rating","Comment"]].apply(lambda c: c.astype(str).str.strip().ne("")).any().any():
            with st.expander("📝 Employer Feedback"):
                st.dataframe(df[["Job Title","Status","Rating","Comment","Updated At"]],
                             use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════════════
    # SKILL GAP
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Skill Gap":
        page_header("Skill Gap Analysis", "Discover what skills you need to unlock more opportunities", "📚")

        resume_text = st.session_state.get("resume_text","")
        if not str(resume_text).strip():
            empty_state("📄", "Resume required",
                        "Upload your resume first to run skill gap analysis."); st.stop()

        from modules.ai_matcher import match_resume_to_jobs
        import pandas as pd
        with st.spinner("Analyzing skill gaps across top matches..."):
            primary, _, resume_skills, resume_category, resume_subcategory, resume_cat_label = match_resume_to_jobs(resume_text)

        st.session_state["resume_subcategory"] = resume_subcategory

        if primary is None or len(primary) == 0:
            empty_state("🔍", "No data", "No job matches found."); st.stop()

        st.markdown(f"""
        <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-radius:10px;padding:14px 18px;margin-bottom:20px">
            <div style="font-size:12px;color:{T()['MUTED']};margin-bottom:8px">YOUR PROFILE</div>
            <div style="font-size:13px;color:{T()['TEXT_HEADING']};margin-bottom:8px">
                Category: <strong style="color:#16a34a">{resume_cat_label}</strong>
                &nbsp;·&nbsp; {len(resume_skills)} skills
            </div>
            {skill_chips(resume_skills, max_show=30)}
        </div>""", unsafe_allow_html=True)

        from collections import Counter
        all_missing = Counter()
        for _, row in primary.iterrows():
            for s in row.get("missing_skills", []): all_missing[s] += 1

        if not all_missing:
            st.success("🎉 You match all required skills across your top job matches — excellent profile!"); st.stop()

        top_missing = all_missing.most_common(15)
        section_header("Most In-Demand Missing Skills",
                       "Skills appearing most frequently in your top matches — learn these first")

        chart_data = pd.DataFrame({"Skill": [s for s,_ in top_missing],
                                   "Jobs needing it": [c for _,c in top_missing]})
        st.bar_chart(chart_data.set_index("Skill"), use_container_width=True)

        section_header("Free Learning Resources")
        cols = st.columns(3)
        for i, (skill, count) in enumerate(top_missing):
            url = SKILL_RESOURCES.get(skill.lower())
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-radius:10px;
                            padding:12px 14px;margin-bottom:8px">
                    <div style="font-weight:600;font-size:13px;color:{T()['TEXT_HEADING']};margin-bottom:3px">{skill}</div>
                    <div style="font-size:11px;color:{T()['MUTED']};margin-bottom:6px">Needed in {count} job(s)</div>
                    {"<a href='"+url+"' target='_blank' style='font-size:12px;color:#3b82f6;text-decoration:none'>📚 Learn for free →</a>" if url else "<span style='font-size:11px;color:"+MUTED+"'>Search online to learn</span>"}
                </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # Delegate remaining pages
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Resume Score":
        page_header("Resume Score Card", "Score your resume against any job description", "📋")
        render_resume_scorecard(user_email)

    elif selected == "Market Trends":
        page_header("Market Trends", "Live skill demand from 1200+ jobs + employer postings", "📈")
        render_market_predictor(user_email)

    elif selected == "Interview Prep":
        page_header("Interview Prep", "AI-generated question banks and mock interviews", "🎤")
        render_interview_prep(user_email)

    elif selected == "Profile Strength":
        render_profile_strength(user_email)

    elif selected == "Salary Estimator":
        render_salary_estimator(user_email)

    elif selected == "Cover Letter":
        render_cover_letter(user_email)

    elif selected == "Resume Builder":
        render_resume_builder(user_email)