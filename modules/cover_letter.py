"""
modules/cover_letter.py
────────────────────────
Cover Letter Generator — uses Groq API (llama-3.3-70b-versatile).
Generates a personalized, professional cover letter based on:
  • Candidate's resume text + extracted skills
  • Target job title + company name
  • Tone preference
  • Key points to highlight
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GROQ_API_KEY


GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


# ── Groq API call ──────────────────────────────────────────────────────────────

def _call_groq(prompt: str, system: str, max_tokens: int = 900) -> str:
    import requests, json

    if not GROQ_API_KEY or GROQ_API_KEY.strip() == "":
        raise ValueError("GROQ_API_KEY is not set in config.py")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system",  "content": system},
            {"role": "user",    "content": prompt},
        ],
        "max_tokens":  max_tokens,
        "temperature": 0.7,
    }
    resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


# ── Prompt builder ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert career coach and professional writer.
You write compelling, personalized cover letters that:
- Sound human, not robotic or generic
- Highlight specific skills and achievements from the resume
- Match the tone requested by the candidate
- Are concise (3–4 paragraphs, under 350 words)
- End with a confident call to action
Never use filler phrases like 'I am writing to express my interest'.
Output ONLY the cover letter text — no subject lines, no labels, no commentary."""


def _build_prompt(
    resume_text:   str,
    skills:        list,
    job_title:     str,
    company:       str,
    tone:          str,
    highlights:    str,
    candidate_name:str,
) -> str:
    skills_str = ", ".join(skills[:20]) if skills else "Not specified"
    highlights_block = f"\nKey points to emphasize:\n{highlights}" if highlights.strip() else ""

    return f"""Write a {tone.lower()} cover letter for:

Candidate: {candidate_name}
Applying for: {job_title} at {company}
Skills: {skills_str}
{highlights_block}

Resume summary (use this for specific details):
---
{resume_text[:1500]}
---

Write the cover letter now. Start directly with the opening line — no 'Dear Hiring Manager' needed unless it fits the tone."""


# ── Template fallback (if no Groq key) ────────────────────────────────────────

def _template_cover_letter(
    candidate_name: str,
    job_title:      str,
    company:        str,
    skills:         list,
    category:       str,
) -> str:
    top_skills = ", ".join(skills[:5]) if skills else "various technical skills"
    return f"""Dear Hiring Team at {company},

I am excited to apply for the {job_title} position. With a strong background in {category} and hands-on experience in {top_skills}, I am confident in my ability to contribute meaningfully to your team from day one.

Throughout my academic and project journey, I have built production-ready systems, worked with large-scale datasets, and developed a deep understanding of both the technical and analytical aspects of this domain. My projects demonstrate not just theoretical knowledge, but real-world problem-solving and delivery.

I am particularly drawn to {company} because of its reputation for innovation and impact. I would welcome the opportunity to bring my skills and enthusiasm to your team.

Thank you for considering my application. I look forward to the opportunity to discuss how I can contribute to {company}'s goals.

Warm regards,
{candidate_name}"""


# ── Main render ────────────────────────────────────────────────────────────────

def render_cover_letter(user_email: str):
    st.subheader("✉️ Cover Letter Generator")
    st.caption("AI-powered personalized cover letters using Groq — generated in seconds.")

    resume_text = st.session_state.get("resume_text", "") or ""
    skills      = st.session_state.get("resume_skills",   []) or []
    category    = st.session_state.get("resume_category",    "") or "General"
    subcategory = st.session_state.get("resume_subcategory", "") or ""
    cat_display = f"{category} — {subcategory}" if subcategory else category

    if not resume_text.strip():
        st.warning("⚠️ Upload your resume first so the AI can personalize your cover letter.")
        return

    candidate_name = user_email.split("@")[0].replace(".", " ").title()

    # ── Form ──
    st.markdown("### 📝 Job Details")
    col1, col2 = st.columns(2)
    with col1:
        job_title = st.text_input("Job Title you're applying for", placeholder="e.g. Data Scientist")
    with col2:
        company = st.text_input("Company Name", placeholder="e.g. Google")

    tone = st.select_slider(
        "Tone",
        options=["Formal", "Professional", "Confident", "Enthusiastic", "Conversational"],
        value="Professional",
    )

    highlights = st.text_area(
        "Key points to highlight (optional)",
        placeholder="e.g. My YouTube analytics project with 1M+ records, Deloitte certification, Power BI dashboards...",
        height=90,
    )

    name_override = st.text_input("Your name (auto-detected, edit if needed)", value=candidate_name)

    st.divider()

    # ── Generate ──
    groq_available = bool(GROQ_API_KEY and GROQ_API_KEY.strip())

    if not groq_available:
        st.warning("⚠️ GROQ_API_KEY not set in config.py — will use a smart template instead.")

    col_btn, col_clear = st.columns([3, 1])
    with col_btn:
        generate = st.button("✨ Generate Cover Letter", type="primary", use_container_width=True,
                             disabled=not (job_title.strip() and company.strip()))
    with col_clear:
        if st.button("🗑️ Clear", use_container_width=True):
            if "cover_letter_output" in st.session_state:
                del st.session_state["cover_letter_output"]
            st.rerun()

    if not (job_title.strip() and company.strip()):
        st.caption("Fill in Job Title and Company Name to enable generation.")

    if generate and job_title.strip() and company.strip():
        with st.spinner("✍️ Writing your cover letter..."):
            try:
                if groq_available:
                    prompt = _build_prompt(
                        resume_text    = resume_text,
                        skills         = skills,
                        job_title      = job_title.strip(),
                        company        = company.strip(),
                        tone           = tone,
                        highlights     = highlights,
                        candidate_name = name_override or candidate_name,
                    )
                    letter = _call_groq(prompt, SYSTEM_PROMPT)
                    source = "groq"
                else:
                    letter = _template_cover_letter(
                        candidate_name = name_override or candidate_name,
                        job_title      = job_title.strip(),
                        company        = company.strip(),
                        skills         = skills,
                        category       = cat_display,
                    )
                    source = "template"

                st.session_state["cover_letter_output"] = {
                    "letter":    letter,
                    "job_title": job_title.strip(),
                    "company":   company.strip(),
                    "source":    source,
                }
            except Exception as e:
                st.error(f"❌ Generation failed: {e}")
                st.caption("Check your GROQ_API_KEY in config.py and internet connection.")

    # ── Output ──
    output = st.session_state.get("cover_letter_output")
    if output:
        st.divider()
        st.markdown(f"### 📄 Cover Letter — {output['job_title']} at {output['company']}")

        if output["source"] == "template":
            st.caption("⚡ Generated using smart template (add GROQ_API_KEY for AI-powered version)")
        else:
            st.caption("⚡ Generated by Groq AI (llama-3.3-70b-versatile)")

        # Editable output
        edited = st.text_area(
            "Your cover letter (edit freely before copying):",
            value=output["letter"],
            height=380,
            key="cover_letter_edit_area",
        )

        # Actions row
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                label="⬇️ Download as .txt",
                data=edited,
                file_name=f"cover_letter_{output['company'].replace(' ','_')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with c2:
            # Copy to clipboard via st.code
            if st.button("📋 View as plain text", use_container_width=True):
                st.code(edited, language=None)
        with c3:
            if st.button("🔄 Regenerate", use_container_width=True):
                if "cover_letter_output" in st.session_state:
                    del st.session_state["cover_letter_output"]
                st.rerun()

        # Tips
        st.divider()
        st.markdown("### 💡 Tips Before Sending")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **✅ Do:**
            - Customize the opening line for each company
            - Add specific numbers from your projects
            - Keep it under 1 page when printed
            """)
        with col2:
            st.markdown("""
            **❌ Avoid:**
            - Sending the same letter to every company
            - Repeating your resume bullet-by-bullet
            - Generic phrases like "team player" without proof
            """)