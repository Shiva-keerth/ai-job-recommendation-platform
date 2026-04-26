import streamlit as st
from modules.chatbot import render_chatbot
import pandas as pd
from streamlit_option_menu import option_menu
from collections import Counter
import re
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CSV_USERS, JOBS_CSV
from modules.db import get_conn
from modules.auth import get_all_users, delete_user, update_user_role
from modules.applications_store import get_all_applications
from modules.theme import (
    topbar, page_header, section_header, render_stat_row,
    empty_state, skill_chips, badge, card,
    MUTED, SUCCESS, WARNING, INFO, PRIMARY, SURFACE, CARD_BORDER,
    T, render_theme_toggle,
)

PURPLE = "#a78bfa"


def _col_rename(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    return df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})


def admin_dashboard(admin_email: str):
    name = admin_email.split("@")[0].replace(".", " ").title()

    # ── Sidebar ──────────────────────────────────────────────────────────
    with st.sidebar:
        p = T()
        render_theme_toggle()
        st.markdown("<hr style='margin:8px 0'>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="padding:4px 0 16px">
            <div style="font-size:11px;color:{p['MUTED']};text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px">Admin Panel</div>
            <div style="font-size:15px;font-weight:700;color:{p['TEXT_HEADING']}">{name}</div>
            <div style="font-size:11px;color:{p['MUTED']}">{admin_email}</div>
        </div>""", unsafe_allow_html=True)

        selected = option_menu(
            menu_title="Navigation",
            options=["Overview","Users","Jobs","Applications","Skill Demand","Activity Log"],
            icons=["bar-chart-fill","people-fill","briefcase-fill",
                   "clipboard-data-fill","graph-up-arrow","clock-history"],
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

    topbar("admin", name, selected)
    render_chatbot(role="admin")

    # ── Shared data ───────────────────────────────────────────────────────
    conn     = get_conn()
    users_df = pd.read_sql_query("SELECT id, email, role FROM users ORDER BY id DESC", conn)
    conn.close()
    all_apps = get_all_applications()

    # ══════════════════════════════════════════════════════════════════════
    # OVERVIEW
    # ══════════════════════════════════════════════════════════════════════
    if selected == "Overview":
        page_header("Platform Overview", "Real-time platform health and activity metrics", "📊")

        total_users = len(users_df)
        candidates  = int((users_df["role"] == "candidate").sum())
        employers   = int((users_df["role"] == "employer").sum())
        admins      = int((users_df["role"] == "admin").sum())

        conn2    = get_conn()
        jobs_cnt = pd.read_sql_query("SELECT COUNT(*) as c FROM jobs", conn2).iloc[0, 0]
        open_cnt = pd.read_sql_query("SELECT COUNT(*) as c FROM jobs WHERE status='open'", conn2).iloc[0, 0]
        conn2.close()

        shortlisted = sum(1 for a in all_apps if a[6] == "Shortlisted")

        render_stat_row([
            {"label": "Total Users",        "value": total_users, "color": INFO},
            {"label": "Candidates",         "value": candidates,  "color": SUCCESS},
            {"label": "Employers",          "value": employers,   "color": WARNING},
            {"label": "Total Applications", "value": len(all_apps), "color": PURPLE},
        ])
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        render_stat_row([
            {"label": "Jobs Posted",  "value": int(jobs_cnt),  "color": INFO},
            {"label": "Open Jobs",    "value": int(open_cnt),  "color": SUCCESS},
            {"label": "Shortlisted",  "value": shortlisted,    "color": WARNING},
            {"label": "Admins",       "value": admins,          "color": PURPLE},
        ])

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        col_l, col_r = st.columns(2)

        with col_l:
            section_header("👥 Role Distribution")
            role_counts = users_df["role"].value_counts()
            role_df     = pd.DataFrame({"Role": role_counts.index, "Count": role_counts.values})
            st.bar_chart(role_df.set_index("Role"), use_container_width=True)

        with col_r:
            section_header("📋 Application Status Distribution")
            if all_apps:
                statuses  = [a[6] for a in all_apps]
                status_df = pd.DataFrame(Counter(statuses).items(), columns=["Status","Count"])
                st.bar_chart(status_df.set_index("Status"), use_container_width=True)
            else:
                empty_state("📭", "No applications yet", "Applications will appear here once candidates start applying.")

        section_header("📈 Applications Over Time")
        if all_apps:
            dates   = [str(a[7])[:10] for a in all_apps if a[7]]
            date_df = pd.DataFrame(Counter(dates).items(), columns=["Date","Count"])
            date_df = date_df.sort_values("Date")
            st.line_chart(date_df.set_index("Date"), use_container_width=True)
        else:
            empty_state("📈", "No data yet", "Application trends will show here over time.")

    # ══════════════════════════════════════════════════════════════════════
    # USERS
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Users":
        page_header("User Management", "View, edit, and manage all platform users", "👥")

        col1, col2 = st.columns([1, 2])
        with col1:
            role_filter = st.selectbox("Filter by role", ["All","candidate","employer","admin"])
        with col2:
            search_q = st.text_input("Search by email", placeholder="Search...")

        filtered = users_df.copy()
        if role_filter != "All": filtered = filtered[filtered["role"] == role_filter]
        if search_q.strip():     filtered = filtered[filtered["email"].str.contains(search_q.strip(), case=False)]

        render_stat_row([
            {"label": "Showing",    "value": len(filtered),  "color": INFO},
            {"label": "Candidates", "value": int((filtered["role"]=="candidate").sum()), "color": SUCCESS},
            {"label": "Employers",  "value": int((filtered["role"]=="employer").sum()),  "color": WARNING},
            {"label": "Admins",     "value": int((filtered["role"]=="admin").sum()),     "color": PURPLE},
        ])

        display = _col_rename(filtered, {"id":"ID","email":"Email","role":"Role"})
        st.dataframe(display, use_container_width=True, hide_index=True)

        # ── Edit user ──
        st.divider()
        section_header("✏️ Edit User", "Change role or delete a user account")

        if not filtered.empty:
            user_opts = {f"{r['email']} ({r['role']})": r for _, r in filtered.iterrows()}
            sel_label = st.selectbox("Select user", list(user_opts.keys()))
            sel_user  = user_opts[sel_label]

            col_a, col_b = st.columns(2)
            with col_a:
                roles    = ["candidate","employer","admin"]
                new_role = st.selectbox("New role",  roles,
                    index=roles.index(sel_user["role"]) if sel_user["role"] in roles else 0)
                if st.button("💾 Update Role", use_container_width=True, type="primary"):
                    update_user_role(int(sel_user["id"]), new_role)
                    st.success(f"✅ Role updated to **{new_role}**"); st.rerun()
            with col_b:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if sel_user["email"] != admin_email:
                    if st.button("🗑️ Delete User", use_container_width=True):
                        if delete_user(int(sel_user["id"])):
                            st.success("✅ User deleted."); st.rerun()
                else:
                    st.warning("You cannot delete your own account.")

        # ── Create user ──
        st.divider()
        section_header("➕ Create New User")
        with st.form("create_user_form"):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1: new_email    = st.text_input("Email", placeholder="user@example.com")
            with c2: new_password = st.text_input("Password", type="password")
            with c3: new_role_sel = st.selectbox("Role", ["candidate","employer","admin"])
            submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            if submit:
                from modules.auth import register_user
                ok, msg = register_user(new_email, new_password, role=new_role_sel)
                st.success(msg) if ok else st.error(msg)
                if ok: st.rerun()

        if CSV_USERS.exists():
            st.divider()
            section_header("📄 User Export (CSV)")
            csv_df = pd.read_csv(CSV_USERS)
            st.dataframe(csv_df, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════════════
    # JOBS
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Jobs":
        page_header("All Jobs", "Monitor all jobs posted by employers on the platform", "💼")

        conn3   = get_conn()
        jobs_df = pd.read_sql_query("""
            SELECT job_id, employer_email, job_title, category, industry,
                   location, work_mode, experience_level, salary_range, status, created_at
            FROM jobs ORDER BY created_at DESC
        """, conn3)
        conn3.close()

        col1, col2 = st.columns([1, 2])
        with col1: status_f = st.selectbox("Filter status", ["All","open","closed"])
        with col2: search_j = st.text_input("Search job title", placeholder="Search...")

        if status_f != "All": jobs_df = jobs_df[jobs_df["status"] == status_f]
        if search_j.strip():  jobs_df = jobs_df[jobs_df["job_title"].str.contains(search_j.strip(), case=False)]

        open_n   = int((jobs_df["status"] == "open").sum())
        closed_n = int((jobs_df["status"] == "closed").sum())
        render_stat_row([
            {"label": "Total Showing", "value": len(jobs_df), "color": INFO},
            {"label": "Open",          "value": open_n,       "color": SUCCESS},
            {"label": "Closed",        "value": closed_n,     "color": "#ef4444"},
            {"label": "Employers",     "value": jobs_df["employer_email"].nunique() if len(jobs_df) else 0, "color": WARNING},
        ])

        # Human-readable column names
        display = _col_rename(jobs_df, {
            "job_id":"ID","employer_email":"Employer","job_title":"Job Title",
            "category":"Category","industry":"Industry","location":"Location",
            "work_mode":"Mode","experience_level":"Level","salary_range":"Salary",
            "status":"Status","created_at":"Posted",
        })
        st.dataframe(display, use_container_width=True, hide_index=True)

        # Toggle status
        st.divider()
        section_header("🔧 Toggle Job Status")
        if not jobs_df.empty:
            jid_opts = {f"#{r['job_id']} · {r['job_title']} [{r['status'].upper()}]": r
                        for _, r in jobs_df.iterrows()}
            sel_jlbl = st.selectbox("Select job", list(jid_opts.keys()))
            sel_jrow = jid_opts[sel_jlbl]
            new_st   = "closed" if sel_jrow["status"] == "open" else "open"
            btn_col, _ = st.columns([1, 2])
            with btn_col:
                if st.button(f"Set to '{new_st}'", use_container_width=True,
                             type="primary" if new_st == "open" else "secondary"):
                    c = get_conn()
                    c.execute("UPDATE jobs SET status=? WHERE job_id=?", (new_st, int(sel_jrow["job_id"])))
                    c.commit(); c.close()
                    st.success(f"✅ Job status updated to **{new_st}**"); st.rerun()

        try:
            csv_jobs = pd.read_csv(JOBS_CSV)
            st.markdown(f"""
            <div style="background:{T()['SURFACE']};border:1px solid {T()['CARD_BORDER']};border-radius:10px;
                        padding:12px 16px;margin-top:12px">
                <span style="font-size:12px;color:{T()['MUTED']}">
                    📂 CSV Dataset: <strong style="color:{T()['TEXT_HEADING']}">{len(csv_jobs)}</strong> jobs ·
                    <strong style="color:{T()['TEXT_HEADING']}">{csv_jobs['category'].nunique()}</strong> categories ·
                    <strong style="color:{T()['TEXT_HEADING']}">{csv_jobs['company_size'].nunique() if 'company_size' in csv_jobs.columns else 3}</strong> company sizes
                </span>
            </div>""", unsafe_allow_html=True)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════
    # APPLICATIONS
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Applications":
        page_header("All Applications", "Platform-wide application data with filtering", "📋")

        if not all_apps:
            empty_state("📭", "No applications yet", "Applications will appear here once candidates start applying."); return

        df = pd.DataFrame(all_apps, columns=[
            "App ID","Candidate","Job ID","Job Title","Company",
            "Score","Status","Applied At","Job Source","Employer",
        ])
        df["Score"] = pd.to_numeric(df["Score"], errors="coerce").fillna(0.0)

        c1, c2, c3 = st.columns([1, 1, 2])
        with c1: st_f  = st.selectbox("Status", ["All","Applied","Shortlisted","Interview","Selected","Rejected"])
        with c2: src_f = st.selectbox("Source", ["All","csv","db"])
        with c3: q_app = st.text_input("Search candidate email", placeholder="Search...")

        fdf = df.copy()
        if st_f  != "All": fdf = fdf[fdf["Status"] == st_f]
        if src_f != "All": fdf = fdf[fdf["Job Source"] == src_f]
        if q_app.strip():  fdf = fdf[fdf["Candidate"].str.contains(q_app.strip(), case=False)]
        fdf = fdf.sort_values("Score", ascending=False)

        render_stat_row([
            {"label": "Total",          "value": len(fdf),                                      "color": INFO},
            {"label": "Avg Score",      "value": f"{round(fdf['Score'].mean()*100,1)}%",        "color": WARNING},
            {"label": "Strong (≥70%)",  "value": int((fdf["Score"] >= 0.70).sum()),             "color": SUCCESS},
            {"label": "Selected",       "value": int((fdf["Status"] == "Selected").sum()),      "color": PURPLE},
        ])

        view = fdf.copy()
        view["Score"] = (view["Score"]*100).round(1).astype(str) + "%"
        display = _col_rename(view, {
            "App ID":"ID","Candidate":"Candidate","Job ID":"Job ID",
            "Job Title":"Job Title","Score":"Score","Status":"Status",
            "Applied At":"Applied At","Job Source":"Source",
        })
        st.dataframe(display[["ID","Candidate","Job Title","Score","Status","Applied At","Source"]],
                     use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════════════
    # SKILL DEMAND
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Skill Demand":
        page_header("Live Skill Demand Analytics", "Based on all employer postings + 1200-job CSV dataset", "📈")

        conn5      = get_conn()
        db_skills  = conn5.execute("SELECT skills FROM jobs WHERE status='open'").fetchall()
        conn5.close()

        skill_counter = Counter()
        for (st_,) in db_skills:
            for s in re.split(r"[,\|;/\n]+", str(st_).lower()):
                s = s.strip()
                if s and len(s) > 2: skill_counter[s] += 1

        try:
            csv_jobs = pd.read_csv(JOBS_CSV).fillna("")
            for skills_text in csv_jobs["skills"]:
                for s in re.split(r"[,\|;/\n]+", str(skills_text).lower()):
                    s = s.strip()
                    if s and len(s) > 2: skill_counter[s] += 1
        except Exception: pass

        if not skill_counter:
            empty_state("📊", "No skill data yet", "Skill analytics will populate as jobs are posted."); return

        top_n      = st.slider("Show top N skills", 10, 50, 20)
        top_skills = skill_counter.most_common(top_n)
        skill_df   = pd.DataFrame(top_skills, columns=["Skill","Job Count"])

        section_header(f"🔥 Top {top_n} In-Demand Skills", "Across all jobs in the platform + CSV dataset")
        st.bar_chart(skill_df.set_index("Skill"), use_container_width=True)

        st.divider()
        section_header("🧠 Skills by Category", "Filter by job category to see domain-specific demand")
        try:
            csv_j    = pd.read_csv(JOBS_CSV).fillna("")
            cat_sel  = st.selectbox("Select category", ["All"] + sorted(csv_j["category"].unique().tolist()))
            subset   = csv_j if cat_sel == "All" else csv_j[csv_j["category"] == cat_sel]
            cat_ctr  = Counter()
            for st_ in subset["skills"]:
                for s in re.split(r"[,\|;/\n]+", str(st_).lower()):
                    s = s.strip()
                    if s and len(s) > 2: cat_ctr[s] += 1
            cat_df = pd.DataFrame(cat_ctr.most_common(15), columns=["Skill","Count"])
            st.bar_chart(cat_df.set_index("Skill"), use_container_width=True)
        except Exception as e:
            st.warning(f"CSV data error: {e}")

        st.divider()
        full_df = pd.DataFrame(skill_counter.most_common(), columns=["Skill","Count"])
        st.download_button(
            "⬇️ Download Full Skill Demand CSV",
            full_df.to_csv(index=False),
            file_name="skill_demand.csv",
            mime="text/csv",
        )

    # ══════════════════════════════════════════════════════════════════════
    # ACTIVITY LOG
    # ══════════════════════════════════════════════════════════════════════
    elif selected == "Activity Log":
        page_header("System Activity Log", "Audit trail of all platform events", "🕐")

        conn6 = get_conn()
        try:
            log_df = pd.read_sql_query("""
                SELECT event_type, actor_email, detail, created_at
                FROM activity_log ORDER BY created_at DESC LIMIT 200
            """, conn6)
            conn6.close()
        except Exception:
            conn6.close()
            empty_state("📋", "No activity logged yet", "Events will appear here as users interact with the platform.")
            return

        if log_df.empty:
            empty_state("📋", "No activity logged yet", "Events will appear here as users interact with the platform.")
            return

        event_types = ["All"] + sorted(log_df["event_type"].unique().tolist())
        col1, col2  = st.columns([1, 2])
        with col1:
            ev_f = st.selectbox("Filter by event", event_types)
        with col2:
            q_log = st.text_input("Search by email", placeholder="Search...")

        if ev_f  != "All":   log_df = log_df[log_df["event_type"] == ev_f]
        if q_log.strip():    log_df = log_df[log_df["actor_email"].str.contains(q_log.strip(), case=False, na=False)]

        render_stat_row([
            {"label": "Events Shown", "value": len(log_df), "color": INFO},
            {"label": "Unique Users", "value": log_df["actor_email"].nunique(), "color": SUCCESS},
            {"label": "Event Types",  "value": log_df["event_type"].nunique(),  "color": WARNING},
        ])

        display = _col_rename(log_df, {
            "event_type":"Event","actor_email":"User","detail":"Detail","created_at":"Time",
        })
        st.dataframe(display, use_container_width=True, hide_index=True)