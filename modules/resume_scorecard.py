"""
Resume Score Card — modules/resume_scorecard.py
================================================
Analyses a candidate's resume against a specific job description using
Claude AI and the existing skill-extraction pipeline.

Tab placement : ui_candidate.py → option "Resume Score"
Icon          : patch-check
Called as     : from modules.resume_scorecard import render_resume_scorecard
Usage         : render_resume_scorecard(user_email)
"""

import json
import re
import streamlit as st
from collections import Counter

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GROQ_API_KEY, JOBS_CSV, SKILL_RESOURCES
from modules.skill_extractor import build_skill_vocab_from_jobs, extract_skills
from modules.category_detector import detect_category, detect_full_category
from modules.db import get_conn
from modules.theme import T


# ── helpers ───────────────────────────────────────────────────────────

def _load_latest_resume(user_email: str):
    """Return (resume_text, skills_csv, category) or None."""
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            SELECT resume_text, extracted_skills, detected_category
            FROM resume_history WHERE user_email=?
            ORDER BY uploaded_at DESC LIMIT 1
        """, (user_email,))
        row = cur.fetchone()
        conn.close()
        return row
    except Exception:
        return None


def _score_bar(pct: int, color: str = "#185FA5") -> str:
    """Returns an HTML progress bar."""
    safe = max(0, min(100, pct))
    p = T()
    bg = p.get('SCORE_BAR_BG', '#e9ecef')
    return (
        f'<div style="height:10px;background:{bg};border-radius:6px;margin:4px 0 8px">'
        f'<div style="width:{safe}%;height:100%;background:{color};border-radius:6px;'
        f'transition:width 0.6s ease"></div></div>'
    )


def _color_for_score(pct: int) -> str:
    if pct >= 75: return "#1D9E75"   # green
    if pct >= 50: return "#BA7517"   # amber
    return "#A32D2D"                 # red


def _label_for_score(pct: int) -> str:
    if pct >= 75: return "Strong"
    if pct >= 50: return "Moderate"
    return "Needs Work"


def _call_claude(system_prompt: str, user_prompt: str) -> str:
    """Calls Groq LLM and returns the response text."""
    try:
        import groq
        client = groq.Groq(api_key=GROQ_API_KEY)
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=800,
            temperature=0.3,
        )
        return r.choices[0].message.content.strip()
    except ImportError:
        return "__ERROR__: groq not installed. Run: pip install groq --user"
    except Exception as e:
        return f"__ERROR__: {e}"


# ── main scorer ───────────────────────────────────────────────────────

def _analyse_resume(resume_text: str, job_desc: str, resume_skills: list) -> tuple[dict | None, str]:
    """
    Calls Claude to score the resume against the job description.
    Returns (result_dict, error_message) — one will always be None.
    """
    system = """You are a professional resume reviewer and ATS expert.
Return ONLY a single valid JSON object — no markdown, no explanation.
Schema:
{
  "overall": <int 0-100>,
  "ats": <int 0-100>,
  "sections": {
    "skills_match":  {"score":<int>,"feedback":"<str>","matched":["..."],"missing":["..."]},
    "experience":    {"score":<int>,"feedback":"<str>"},
    "education":     {"score":<int>,"feedback":"<str>"},
    "formatting":    {"score":<int>,"feedback":"<str>"},
    "keywords":      {"score":<int>,"feedback":"<str>","found":["..."],"missing":["..."]}
  },
  "strengths":    ["<str>","<str>","<str>"],
  "improvements": ["<str>","<str>","<str>"],
  "verdict": "<one sentence summary>"
}"""

    user = (
        f"Job Description:\n{job_desc[:2000]}\n\n"
        f"Resume:\n{resume_text[:3000]}\n\n"
        f"Detected resume skills: {', '.join(resume_skills[:30])}"
    )

    raw = _call_claude(system, user)
    if raw.startswith("__ERROR__"):
        return None, raw[len("__ERROR__: "):]

    # Strip possible markdown fences
    clean = re.sub(r"^```[a-z]*\n?", "", raw.strip())
    clean = re.sub(r"```$", "", clean.strip())
    try:
        return json.loads(clean), ""
    except json.JSONDecodeError:
        return None, f"AI returned invalid JSON. Raw response:\n\n{raw[:300]}"


# ── UI ─────────────────────────────────────────────────────────────────

def render_resume_scorecard(user_email: str):
    st.subheader("📋 Resume Score Card")
    st.caption("Score your resume against any job description — get ATS rating, skill gaps, and improvement tips.")

    # ── Step 1: Resume source ─────────────────────────────────────────
    st.markdown("#### Step 1 — Resume")

    resume_text = st.session_state.get("resume_text", "") or ""

    saved = _load_latest_resume(user_email) if not resume_text.strip() else None
    if saved and not resume_text.strip():
        resume_text = saved[0]
        if not st.session_state.get("resume_text"):
            st.session_state["resume_text"]     = saved[0]
            st.session_state["resume_skills"]   = [s.strip() for s in saved[1].split(",") if s.strip()]
            st.session_state["resume_category"] = saved[2]
            _fc = detect_full_category(saved[0])
            st.session_state["resume_subcategory"] = _fc["sub"]
            st.session_state["resume_cat_label"]   = _fc["label"]

    col_src1, col_src2 = st.columns([3, 1])
    with col_src1:
        if resume_text.strip():
            st.success(f"✅ Resume loaded ({len(resume_text.split())} words, "
                       f"{len(st.session_state.get('resume_skills', []))} skills detected)")
        else:
            st.warning("⚠️ No resume on file. Upload one in the **Resume Upload** tab, or paste text below.")

    with col_src2:
        use_paste = st.checkbox("Paste resume instead", value=not bool(resume_text.strip()))

    if use_paste:
        resume_text = st.text_area(
            "Paste resume text",
            height=180,
            placeholder="Copy-paste your full resume text here…",
            key="sc_resume_paste",
        )

    # ── Step 2: Job description ───────────────────────────────────────
    st.markdown("#### Step 2 — Job Description")
    job_desc = st.text_area(
        "Paste the job description you want to target",
        height=180,
        placeholder="Paste the full JD here — the more detail the better…",
        key="sc_job_desc",
    )

    # ── Analyse button ────────────────────────────────────────────────
    st.markdown("---")
    can_run = bool(resume_text.strip()) and bool(job_desc.strip())
    if not can_run:
        st.info("Fill in both resume and job description above, then click Analyse.")

    if st.button("🔍 Analyse Resume", use_container_width=True,
                 disabled=not can_run, key="sc_run_btn"):
        # Extract skills from current resume text
        with st.spinner("Extracting skills & running AI analysis…"):
            try:
                vocab = build_skill_vocab_from_jobs(str(JOBS_CSV))
                r_skills = sorted(list(extract_skills(resume_text, vocab)))
            except Exception:
                r_skills = st.session_state.get("resume_skills", []) or []

            result, err_msg = _analyse_resume(resume_text, job_desc, r_skills)

        if result is None:
            st.error(f"❌ AI analysis failed: {err_msg}")
            st.stop()

        st.session_state["sc_result"]      = result
        st.session_state["sc_resume_skills"] = r_skills

    # ── Results ───────────────────────────────────────────────────────
    result = st.session_state.get("sc_result")
    if not result:
        return

    r_skills = st.session_state.get("sc_resume_skills", [])
    st.markdown("---")
    st.markdown("### 📊 Analysis Results")

    # ── Top KPI row ───────────────────────────────────────────────────
    overall = int(result.get("overall", 0))
    ats     = int(result.get("ats", 0))
    sections_data = result.get("sections", {})
    avg_sec = int(sum(v.get("score", 0) for v in sections_data.values()) / max(len(sections_data), 1))

    k1, k2, k3 = st.columns(3)
    for col, label, val in [(k1, "Overall Score", overall),
                             (k2, "ATS Score",     ats),
                             (k3, "Section Avg",   avg_sec)]:
        c = _color_for_score(val)
        with col:
            st.markdown(
                f'<div style="border:0.5px solid {c}33;border-radius:12px;padding:14px;text-align:center">'
                f'<div style="font-size:12px;color:var(--color-text-secondary)">{label}</div>'
                f'<div style="font-size:32px;font-weight:500;color:{c}">{val}</div>'
                f'<div style="font-size:12px;color:{c}">{_label_for_score(val)}</div>'
                f'</div>', unsafe_allow_html=True
            )

    # verdict
    if result.get("verdict"):
        st.info(f"💡 {result['verdict']}")

    st.markdown("---")

    # ── Section breakdown ─────────────────────────────────────────────
    st.markdown("#### Section Breakdown")
    section_labels = {
        "skills_match": "Skills Match",
        "experience":   "Experience",
        "education":    "Education",
        "formatting":   "Formatting",
        "keywords":     "Keywords",
    }

    for key, label in section_labels.items():
        sec = sections_data.get(key, {})
        if not sec:
            continue
        score   = int(sec.get("score", 0))
        color   = _color_for_score(score)
        feedback= sec.get("feedback", "")

        with st.expander(f"{label} — {score}/100", expanded=(score < 60)):
            st.markdown(_score_bar(score, color), unsafe_allow_html=True)
            st.caption(feedback)

            matched = sec.get("matched", []) or sec.get("found", [])
            missing = sec.get("missing", [])

            if matched:
                st.markdown("**✅ Matched**")
                p = T()
                bg_color = p['TAG_BG']
                text_color = p['TEXT']
                pills = " ".join(
                    f'<span style="background:{bg_color};color:{text_color};font-size:11px;'
                    f'padding:2px 8px;border-radius:99px;margin:2px;display:inline-block;border:1px solid {p["TAG_BORDER"]}">{s}</span>'
                    for s in matched[:15]
                )
                st.markdown(pills, unsafe_allow_html=True)

            if missing:
                st.markdown("**⚠️ Missing**")
                p = T()
                miss_pills = []
                for s in missing[:12]:
                    url = SKILL_RESOURCES.get(s.lower())
                    link = f'<a href="{url}" target="_blank" style="text-decoration:none">' if url else ""
                    end  = "</a>" if url else ""
                    miss_pills.append(
                        f'{link}<span style="background:rgba(239, 68, 68, 0.1);color:#ef4444;font-size:11px;'
                        f'padding:2px 8px;border-radius:99px;margin:2px;display:inline-block;border:1px solid rgba(239,68,68,0.2)">{s}</span>{end}'
                    )
                st.markdown(" ".join(miss_pills), unsafe_allow_html=True)
                if url:
                    st.caption("💡 Click a red skill to find a free learning resource")

    st.markdown("---")

    # ── Strengths & Improvements ──────────────────────────────────────
    col_s, col_i = st.columns(2)
    with col_s:
        st.markdown("#### ✅ Strengths")
        for s in result.get("strengths", []):
            st.markdown(
                f'<div style="border-left:3px solid #1D9E75;padding:6px 10px;'
                f'margin-bottom:6px;border-radius:0 6px 6px 0;'
                f'background:var(--color-background-secondary);font-size:13px">{s}</div>',
                unsafe_allow_html=True
            )

    with col_i:
        st.markdown("#### 🔧 Improvements")
        for imp in result.get("improvements", []):
            st.markdown(
                f'<div style="border-left:3px solid #BA7517;padding:6px 10px;'
                f'margin-bottom:6px;border-radius:0 6px 6px 0;'
                f'background:var(--color-background-secondary);font-size:13px">{imp}</div>',
                unsafe_allow_html=True
            )

    st.markdown("---")

    # ── Skill overlap visualisation ───────────────────────────────────
    st.markdown("#### 🎯 Your Skills vs Job Requirements")

    # Extract job skills naively for overlap view
    try:
        vocab    = build_skill_vocab_from_jobs(str(JOBS_CSV))
        jd_skills= sorted(list(extract_skills(job_desc, vocab)))
    except Exception:
        jd_skills = []

    resume_set = set(r_skills)
    jd_set     = set(jd_skills)
    matched_set = resume_set & jd_set
    missing_set = jd_set - resume_set
    extra_set   = resume_set - jd_set

    c1, c2, c3 = st.columns(3)
    c1.metric("Matched",  len(matched_set))
    c2.metric("Missing from JD", len(missing_set))
    c3.metric("Extra (bonus)", len(extra_set))

    if matched_set:
        st.markdown("**✅ You have these required skills:**")
        st.write(" ".join([f"`{s}`" for s in sorted(matched_set)[:20]]))
    if missing_set:
        st.markdown("**⚠️ JD requires, you're missing:**")
        links = []
        for s in sorted(missing_set)[:15]:
            url = SKILL_RESOURCES.get(s.lower())
            links.append(f"[`{s}`]({url})" if url else f"`{s}`")
        st.markdown("  ".join(links))
        st.caption("Click a skill for a free learning resource")

    # ── Reset button ──────────────────────────────────────────────────
    st.markdown("---")
    if st.button("🔄 Analyse a different JD", key="sc_reset", use_container_width=False):
        st.session_state.pop("sc_result", None)
        st.session_state.pop("sc_resume_skills", None)
        st.rerun()