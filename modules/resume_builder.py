"""
modules/resume_builder.py
──────────────────────────
Resume Builder — most impressive feature.
Lets candidates fill a form and generates a clean, ATS-friendly
resume as a downloadable HTML file (printable as PDF from browser).
No external API needed.
"""

import streamlit as st
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Resume HTML template ───────────────────────────────────────────────────────

def _build_resume_html(data: dict) -> str:
    name     = data.get("name", "")
    email    = data.get("email", "")
    phone    = data.get("phone", "")
    location = data.get("location", "")
    linkedin = data.get("linkedin", "")
    github   = data.get("github", "")
    summary  = data.get("summary", "")
    skills   = data.get("skills", "")
    projects = data.get("projects", [])
    exp      = data.get("experience", [])
    edu      = data.get("education", [])
    certs    = data.get("certifications", "")

    # ── Contact line ──
    contact_parts = [x for x in [email, phone, location] if x.strip()]
    links = []
    if linkedin.strip():
        links.append(f'<a href="{linkedin}" style="color:#1a73e8">{linkedin.replace("https://","")}</a>')
    if github.strip():
        links.append(f'<a href="{github}" style="color:#1a73e8">{github.replace("https://","")}</a>')

    contact_html = " · ".join(contact_parts)
    if links:
        contact_html += (" · " if contact_html else "") + " · ".join(links)

    # ── Projects ──
    proj_html = ""
    for p in projects:
        if not p.get("title", "").strip():
            continue
        bullets = "".join(
            f"<li>{b.strip()}</li>"
            for b in p.get("bullets", "").split("\n")
            if b.strip()
        )
        tech = f'<span style="font-size:11px;color:#555"> | {p["tech"]}</span>' if p.get("tech") else ""
        proj_html += f"""
        <div style="margin-bottom:14px">
          <div style="font-weight:600;font-size:14px">{p['title']}{tech}</div>
          <ul style="margin:4px 0 0 18px;padding:0;font-size:13px;color:#333">{bullets}</ul>
        </div>"""

    # ── Experience ──
    exp_html = ""
    for e in exp:
        if not e.get("role", "").strip():
            continue
        bullets = "".join(
            f"<li>{b.strip()}</li>"
            for b in e.get("bullets", "").split("\n")
            if b.strip()
        )
        exp_html += f"""
        <div style="margin-bottom:14px">
          <div style="display:flex;justify-content:space-between">
            <span style="font-weight:600;font-size:14px">{e['role']} — {e.get('company','')}</span>
            <span style="font-size:12px;color:#666">{e.get('duration','')}</span>
          </div>
          <ul style="margin:4px 0 0 18px;padding:0;font-size:13px;color:#333">{bullets}</ul>
        </div>"""

    # ── Education ──
    edu_html = ""
    for ed in education_list(edu):
        if not ed.get("degree", "").strip():
            continue
        cgpa = f" | CGPA: {ed['cgpa']}" if ed.get("cgpa") else ""
        edu_html += f"""
        <div style="margin-bottom:10px;display:flex;justify-content:space-between;align-items:baseline">
          <div>
            <span style="font-weight:600;font-size:14px">{ed['degree']}</span>
            <span style="font-size:13px;color:#555"> — {ed.get('institution','')}{cgpa}</span>
          </div>
          <span style="font-size:12px;color:#666">{ed.get('year','')}</span>
        </div>"""

    # ── Skills ──
    skill_tags = "".join(
        f'<span style="background:#e8f0fe;color:#1a56db;padding:3px 10px;border-radius:20px;'
        f'font-size:12px;margin:3px;display:inline-block">{s.strip()}</span>'
        for s in skills.split(",") if s.strip()
    )

    # ── Certifications ──
    cert_html = ""
    if certs.strip():
        cert_items = "".join(
            f"<li>{c.strip()}</li>"
            for c in certs.split("\n") if c.strip()
        )
        cert_html = f"""
        <div class="section">
          <div class="section-title">CERTIFICATIONS</div>
          <ul style="margin:4px 0 0 18px;padding:0;font-size:13px;color:#333">{cert_items}</ul>
        </div>"""

    def section(title, content):
        if not content.strip():
            return ""
        return f"""
        <div class="section">
          <div class="section-title">{title}</div>
          {content}
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} — Resume</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #1a1a1a;
    background: #fff;
    max-width: 820px;
    margin: 0 auto;
    padding: 36px 40px;
  }}
  h1 {{ font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }}
  .contact {{ font-size: 12.5px; color: #444; margin: 6px 0 0; }}
  .section {{ margin-top: 22px; }}
  .section-title {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #1a73e8;
    border-bottom: 1.5px solid #e8f0fe;
    padding-bottom: 4px;
    margin-bottom: 12px;
  }}
  .summary {{ font-size: 13px; color: #333; line-height: 1.6; }}
  @media print {{
    body {{ padding: 20px 24px; }}
    a {{ color: #1a73e8 !important; text-decoration: none; }}
  }}
</style>
</head>
<body>
  <h1>{name}</h1>
  <div class="contact">{contact_html}</div>

  {section("PROFESSIONAL SUMMARY", f'<div class="summary">{summary}</div>') if summary.strip() else ""}

  {section("TECHNICAL SKILLS", f'<div>{skill_tags}</div>') if skills.strip() else ""}

  {section("TECHNICAL PROJECTS", proj_html) if proj_html.strip() else ""}

  {section("EXPERIENCE", exp_html) if exp_html.strip() else ""}

  {section("EDUCATION", edu_html) if edu_html.strip() else ""}

  {cert_html}

  <div style="margin-top:28px;font-size:10px;color:#ccc;text-align:right">
    Generated by Skill Match AI · {datetime.now().strftime("%B %Y")}
  </div>
</body>
</html>"""


def education_list(edu):
    """Return education list, filtering empty entries."""
    return [e for e in edu if isinstance(e, dict) and e.get("degree","").strip()]


# ── Session state helpers ──────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "rb_projects":    [{"title":"","tech":"","bullets":""} for _ in range(3)],
        "rb_experience":  [{"role":"","company":"","duration":"","bullets":""}],
        "rb_education":   [{"degree":"","institution":"","year":"","cgpa":""}],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Main render ────────────────────────────────────────────────────────────────

def render_resume_builder(user_email: str):
    st.subheader("📝 Resume Builder")
    st.caption("Fill the form below and download a clean, ATS-friendly resume as HTML (print to PDF from your browser).")

    _init_state()

    skills   = st.session_state.get("resume_skills",   []) or []
    category = st.session_state.get("resume_category", "") or ""
    auto_name = user_email.split("@")[0].replace(".", " ").title()

    # ════════════ PERSONAL INFO ════════════
    st.markdown("### 👤 Personal Information")
    c1, c2 = st.columns(2)
    with c1:
        name     = st.text_input("Full Name *", value=auto_name)
        email    = st.text_input("Email *",     value=user_email)
        phone    = st.text_input("Phone",       placeholder="+91 9876543210")
    with c2:
        location = st.text_input("Location",   placeholder="Ahmedabad, India")
        linkedin = st.text_input("LinkedIn URL", placeholder="https://linkedin.com/in/yourname")
        github   = st.text_input("GitHub URL",   placeholder="https://github.com/yourname")

    # ════════════ SUMMARY ════════════
    st.divider()
    st.markdown("### 📋 Professional Summary")
    summary = st.text_area(
        "Summary",
        height=100,
        placeholder="Highly analytical Data Science enthusiast with expertise in Python, SQL, and ML model deployment...",
        label_visibility="collapsed",
    )

    # ════════════ SKILLS ════════════
    st.divider()
    st.markdown("### 🧠 Technical Skills")
    auto_skills = ", ".join(skills) if skills else ""
    skills_input = st.text_area(
        "Skills (comma separated)",
        value=auto_skills,
        height=80,
        help="Auto-filled from your uploaded resume. Edit as needed.",
    )

    # ════════════ PROJECTS ════════════
    st.divider()
    st.markdown("### 💻 Technical Projects")
    st.caption("Add up to 5 projects. Most impactful ones first.")

    c_add, c_remove = st.columns([1, 1])
    with c_add:
        if st.button("➕ Add Project", use_container_width=True) and len(st.session_state.rb_projects) < 5:
            st.session_state.rb_projects.append({"title":"","tech":"","bullets":""})
    with c_remove:
        if st.button("➖ Remove Last", use_container_width=True) and len(st.session_state.rb_projects) > 1:
            st.session_state.rb_projects.pop()

    for i, proj in enumerate(st.session_state.rb_projects):
        with st.expander(f"Project {i+1}: {proj['title'] or 'Untitled'}", expanded=(i == 0)):
            pc1, pc2 = st.columns([2, 1])
            with pc1:
                st.session_state.rb_projects[i]["title"] = st.text_input(
                    "Project Title", value=proj["title"], key=f"ptitle_{i}",
                    placeholder="End-to-End Real Estate Valuation App")
            with pc2:
                st.session_state.rb_projects[i]["tech"] = st.text_input(
                    "Tech Stack", value=proj["tech"], key=f"ptech_{i}",
                    placeholder="Python · Scikit-learn · Streamlit")
            st.session_state.rb_projects[i]["bullets"] = st.text_area(
                "Bullet points (one per line)", value=proj["bullets"], key=f"pbullets_{i}",
                height=100,
                placeholder="Built Random Forest model with R² = 0.91 on 12 engineered features\nDeployed Streamlit UI with real-time inference and 5 analytical dashboards")

    # ════════════ EXPERIENCE ════════════
    st.divider()
    st.markdown("### 💼 Work Experience")
    st.caption("Leave blank if you have no work experience — projects will carry your profile.")

    c_add2, c_rem2 = st.columns([1, 1])
    with c_add2:
        if st.button("➕ Add Experience", use_container_width=True) and len(st.session_state.rb_experience) < 4:
            st.session_state.rb_experience.append({"role":"","company":"","duration":"","bullets":""})
    with c_rem2:
        if st.button("➖ Remove Last ", use_container_width=True) and len(st.session_state.rb_experience) > 1:
            st.session_state.rb_experience.pop()

    for i, exp in enumerate(st.session_state.rb_experience):
        with st.expander(f"Experience {i+1}: {exp['role'] or 'Untitled'}", expanded=(i == 0)):
            ec1, ec2, ec3 = st.columns([2, 2, 1])
            with ec1:
                st.session_state.rb_experience[i]["role"] = st.text_input(
                    "Role / Title", value=exp["role"], key=f"erole_{i}",
                    placeholder="Data Science Intern")
            with ec2:
                st.session_state.rb_experience[i]["company"] = st.text_input(
                    "Company", value=exp["company"], key=f"ecomp_{i}",
                    placeholder="Infolabz Pvt Ltd")
            with ec3:
                st.session_state.rb_experience[i]["duration"] = st.text_input(
                    "Duration", value=exp["duration"], key=f"edur_{i}",
                    placeholder="Jun–Aug 2024")
            st.session_state.rb_experience[i]["bullets"] = st.text_area(
                "Bullet points (one per line)", value=exp["bullets"], key=f"ebullets_{i}",
                height=90,
                placeholder="Built ML pipeline reducing model training time by 40%\nPresented EDA findings to senior stakeholders")

    # ════════════ EDUCATION ════════════
    st.divider()
    st.markdown("### 🎓 Education")

    for i, ed in enumerate(st.session_state.rb_education):
        ec1, ec2, ec3, ec4 = st.columns([3, 3, 1, 1])
        with ec1:
            st.session_state.rb_education[i]["degree"] = st.text_input(
                "Degree *", value=ed["degree"], key=f"eddeg_{i}",
                placeholder="B.Tech in Information Technology")
        with ec2:
            st.session_state.rb_education[i]["institution"] = st.text_input(
                "Institution", value=ed.get("institution",""), key=f"edinst_{i}",
                placeholder="Indus University, Ahmedabad")
        with ec3:
            st.session_state.rb_education[i]["year"] = st.text_input(
                "Year", value=ed.get("year",""), key=f"edyr_{i}",
                placeholder="2026")
        with ec4:
            st.session_state.rb_education[i]["cgpa"] = st.text_input(
                "CGPA", value=ed.get("cgpa",""), key=f"edcgpa_{i}",
                placeholder="9.24")

    # ════════════ CERTIFICATIONS ════════════
    st.divider()
    st.markdown("### 🏆 Certifications")
    certs = st.text_area(
        "Certifications (one per line)",
        height=90,
        placeholder="Data Analytics Job Simulation — Deloitte (Virtual)\nAI & Machine Learning Certification — Infolabz Pvt Ltd",
        label_visibility="collapsed",
    )

    # ════════════ PREVIEW & DOWNLOAD ════════════
    st.divider()
    st.markdown("### 📥 Generate Resume")

    if not name.strip() or not email.strip():
        st.warning("Fill in at least your Name and Email to generate.")
    else:
        col_prev, col_dl = st.columns(2)
        with col_prev:
            preview = st.button("👁️ Preview Resume", type="secondary", use_container_width=True)
        with col_dl:
            generate = st.button("⬇️ Download Resume (HTML)", type="primary", use_container_width=True)

        resume_data = {
            "name":           name,
            "email":          email,
            "phone":          phone,
            "location":       location,
            "linkedin":       linkedin,
            "github":         github,
            "summary":        summary,
            "skills":         skills_input,
            "projects":       st.session_state.rb_projects,
            "experience":     st.session_state.rb_experience,
            "education":      st.session_state.rb_education,
            "certifications": certs,
        }

        html = _build_resume_html(resume_data)

        if preview:
            st.markdown("---")
            st.markdown("#### 👁️ Preview (approximate)")
            st.components.v1.html(html, height=900, scrolling=True)

        if generate:
            fname = f"{name.replace(' ','_')}_Resume.html"
            st.download_button(
                label      = f"📄 Click to download: {fname}",
                data       = html,
                file_name  = fname,
                mime       = "text/html",
                use_container_width=True,
            )
            st.success("✅ Resume generated! Open the downloaded HTML file in your browser and press Ctrl+P → Save as PDF.")
            st.info("💡 Tip: In the print dialog, set margins to 'Minimum' and enable 'Background graphics' for best results.")