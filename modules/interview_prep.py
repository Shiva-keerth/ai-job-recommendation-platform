"""
Interview Prep — modules/interview_prep.py
==========================================
Two modes:
  1. Question Bank  — AI generates categorised questions for a role/company
  2. Mock Interview — Interactive Q&A with per-answer AI feedback

Tab placement : ui_candidate.py → option "Interview Prep"
Icon          : mic
Called as     : from modules.interview_prep import render_interview_prep
Usage         : render_interview_prep(user_email)
"""

import json
import re
import streamlit as st

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GROQ_API_KEY


# ── Claude helper ─────────────────────────────────────────────────────

def _call_claude(system: str, user: str, max_tokens: int = 900) -> str:
    """Calls Groq LLM and returns the response text."""
    try:
        import groq
        client = groq.Groq(api_key=GROQ_API_KEY)
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=800,
            temperature=0.3,
        )
        return r.choices[0].message.content.strip()
    except ImportError:
        return "__ERROR__: groq not installed. Run: pip install groq --user"
    except Exception as e:
        return f"__ERROR__: {e}"


def _parse_json(raw: str) -> dict | list | None:
    clean = re.sub(r"^```[a-z]*\n?", "", raw.strip())
    clean = re.sub(r"```$", "", clean.strip())
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


# ── Question Bank ─────────────────────────────────────────────────────

def _generate_question_bank(role: str, company: str, resume_skills: list, category: str) -> dict | None:
    system = """You are a senior technical interviewer with 15 years experience.
Return ONLY valid JSON — no markdown, no explanation.
Schema:
{
  "role": "<str>",
  "rounds": <int>,
  "categories": [
    {
      "name": "<str>",
      "questions": [
        {"q": "<str>", "difficulty": "Easy|Medium|Hard", "tip": "<str max 10 words>"}
      ]
    }
  ],
  "ask_interviewer": ["<str>","<str>","<str>"],
  "salary_tips":     ["<str>","<str>","<str>"]
}
Include 3 categories: Technical, Behavioral, HR/Culture. 3 questions each."""

    user = (
        f"Role: {role}\n"
        f"Company: {company or 'a product/service company'}\n"
        f"Category: {category or 'IT & Software'}\n"
        f"Candidate skills: {', '.join(resume_skills[:15]) or 'not specified'}\n"
        "Generate interview questions tailored to Indian job market."
    )

    raw = _call_claude(system, user, max_tokens=900)
    if raw.startswith("__ERROR__"):
        return None
    return _parse_json(raw)


# ── Mock interview ─────────────────────────────────────────────────────

def _generate_mock_questions(role: str, company: str, category: str) -> list | None:
    system = """You are an interviewer. Return ONLY valid JSON — no markdown.
Schema: {"questions": [{"q": "<str>", "type": "Technical|Behavioral|HR"}]}
Generate exactly 5 questions."""

    user = (
        f"Role: {role}\n"
        f"Company: {company or 'a product company'}\n"
        f"Category: {category or 'IT & Software'}"
    )

    raw = _call_claude(system, user, max_tokens=500)
    if raw.startswith("__ERROR__"):
        return None
    parsed = _parse_json(raw)
    if isinstance(parsed, dict):
        return parsed.get("questions", [])
    return None


def _evaluate_answers(qa_pairs: list, role: str) -> dict | None:
    system = """You are an interview coach. Return ONLY valid JSON — no markdown.
Schema:
{
  "overall_score": <int 0-100>,
  "recommendation": "Strong Hire|Hire|Maybe|No Hire",
  "summary": "<2 sentence summary>",
  "per_answer": [
    {"score":<int>,"strength":"<str>","improvement":"<str>"}
  ]
}"""

    qa_text = "\n\n".join(
        f"Q{i+1}: {pair['q']}\nA{i+1}: {pair['a']}"
        for i, pair in enumerate(qa_pairs)
    )
    user = f"Role: {role}\n\n{qa_text}"

    raw = _call_claude(system, user, max_tokens=800)
    if raw.startswith("__ERROR__"):
        return None
    return _parse_json(raw)


# ── Difficulty badge ──────────────────────────────────────────────────

def _diff_badge(difficulty: str) -> str:
    colors = {
        "Easy":   ("#EAF3DE", "#27500A"),
        "Medium": ("#FAEEDA", "#633806"),
        "Hard":   ("#FCEBEB", "#501313"),
    }
    bg, fg = colors.get(difficulty, ("#F1EFE8", "#444441"))
    return (
        f'<span style="background:{bg};color:{fg};font-size:11px;'
        f'padding:2px 8px;border-radius:99px;margin-left:6px">{difficulty}</span>'
    )


def _score_color(s: int) -> str:
    if s >= 75: return "#1D9E75"
    if s >= 50: return "#BA7517"
    return "#A32D2D"


# ── Main UI ────────────────────────────────────────────────────────────

def render_interview_prep(user_email: str):
    st.subheader("🎯 Interview Prep")
    st.caption("Generate a question bank or do a full mock interview with AI feedback.")

    # ── Shared inputs ─────────────────────────────────────────────────
    col_r, col_c = st.columns(2)
    with col_r:
        role = st.text_input(
            "Target Role*",
            placeholder="e.g. Software Engineer, Data Analyst…",
            key="ip_role",
        )
    with col_c:
        company = st.text_input(
            "Company (optional)",
            placeholder="e.g. Infosys, Swiggy, TCS…",
            key="ip_company",
        )

    resume_skills   = st.session_state.get("resume_skills", []) or []
    resume_category = st.session_state.get("resume_category",    "") or "IT & Software"
    resume_subcategory = st.session_state.get("resume_subcategory", "") or ""
    # Use subcategory if available for more precise question generation
    resume_cat_label = (f"{resume_category} — {resume_subcategory}"
                        if resume_subcategory else resume_category)

    # ── Mode tabs ─────────────────────────────────────────────────────
    mode = st.radio(
        "Mode",
        ["📚 Question Bank", "🎙️ Mock Interview"],
        horizontal=True,
        key="ip_mode",
    )

    st.markdown("---")

    # ════════════════════ QUESTION BANK ══════════════════════════════
    if mode == "📚 Question Bank":
        if st.button("✨ Generate Questions", key="ip_gen_qbank",
                     disabled=not role.strip(), use_container_width=False):
            with st.spinner("Generating tailored questions…"):
                bank = _generate_question_bank(role, company, resume_skills, resume_cat_label)
            if bank is None:
                st.error("❌ AI generation failed. Check GROQ_API_KEY in config.py.")
            else:
                st.session_state["ip_qbank"] = bank

        if not role.strip():
            st.info("Enter a target role above to generate questions.")

        bank = st.session_state.get("ip_qbank")
        if not bank:
            return

        # Header info
        colh1, colh2 = st.columns([3, 1])
        with colh1:
            st.markdown(f"### Questions for: **{bank.get('role', role)}**")
        with colh2:
            st.markdown(
                f'<div style="background:var(--color-background-secondary);border-radius:8px;'
                f'padding:8px 12px;text-align:center;font-size:13px">'
                f'~{bank.get("rounds", 3)} rounds expected</div>',
                unsafe_allow_html=True,
            )

        # Categories
        for cat_block in bank.get("categories", []):
            cat_name = cat_block.get("name", "")
            questions = cat_block.get("questions", [])

            st.markdown(f"#### {cat_name}")
            for i, q in enumerate(questions):
                diff = q.get("difficulty", "Medium")
                tip  = q.get("tip", "")
                q_text = q.get("q", "")

                st.markdown(
                    f'<div style="border:0.5px solid var(--color-border-tertiary);'
                    f'border-radius:10px;padding:12px 14px;margin-bottom:8px">'
                    f'<div style="font-size:13px;font-weight:500;margin-bottom:6px">'
                    f'{i+1}. {q_text}{_diff_badge(diff)}</div>'
                    f'<div style="font-size:12px;color:var(--color-text-secondary)">'
                    f'💡 Tip: {tip}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # Ask the interviewer
        if bank.get("ask_interviewer"):
            st.markdown("---")
            st.markdown("#### ❓ Questions to Ask the Interviewer")
            for q in bank["ask_interviewer"]:
                st.markdown(f"→ {q}")

        # Salary tips
        if bank.get("salary_tips"):
            st.markdown("---")
            st.markdown("#### 💰 Salary Negotiation Tips")
            for tip in bank["salary_tips"]:
                st.markdown(
                    f'<div style="border-left:3px solid #1D9E75;padding:6px 10px;'
                    f'margin-bottom:6px;border-radius:0 6px 6px 0;'
                    f'background:var(--color-background-secondary);font-size:13px">✓ {tip}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        if st.button("🔄 Regenerate", key="ip_regen_bank"):
            st.session_state.pop("ip_qbank", None)
            st.rerun()

    # ════════════════════ MOCK INTERVIEW ══════════════════════════════
    else:
        mock = st.session_state.get("ip_mock", {
            "started": False, "questions": [], "answers": [],
            "q_index": 0, "feedback": None,
        })

        # ── Not started ────────────────────────────────────────────
        if not mock["started"]:
            st.info("You'll be asked 5 questions. Type your answer for each, then receive AI feedback at the end.")
            if st.button("▶ Start Mock Interview", key="ip_start_mock",
                         disabled=not role.strip(), use_container_width=False):
                with st.spinner("Preparing your interview…"):
                    qs = _generate_mock_questions(role, company, resume_cat_label)
                if not qs:
                    st.error("❌ Could not generate questions. Check GROQ_API_KEY in config.py.")
                else:
                    st.session_state["ip_mock"] = {
                        "started":   True,
                        "questions": qs,
                        "answers":   [],
                        "q_index":   0,
                        "feedback":  None,
                        "role":      role,
                    }
                    st.rerun()

            if not role.strip():
                st.warning("Enter a target role above first.")

        # ── In progress ────────────────────────────────────────────
        elif mock["started"] and mock["feedback"] is None:
            mock = st.session_state["ip_mock"]
            qs      = mock["questions"]
            q_idx   = mock["q_index"]
            total   = len(qs)

            # Progress bar
            progress = q_idx / total
            st.markdown(
                f'<div style="height:6px;background:var(--color-background-secondary);'
                f'border-radius:3px;margin-bottom:12px">'
                f'<div style="width:{int(progress*100)}%;height:100%;background:#185FA5;'
                f'border-radius:3px"></div></div>',
                unsafe_allow_html=True,
            )
            st.caption(f"Question {q_idx + 1} of {total} — {qs[q_idx].get('type', '')}")

            # Question card
            st.markdown(
                f'<div style="background:var(--color-background-secondary);border-radius:12px;'
                f'padding:16px 18px;font-size:15px;font-weight:500;margin-bottom:16px;'
                f'line-height:1.6">{qs[q_idx]["q"]}</div>',
                unsafe_allow_html=True,
            )

            answer = st.text_area(
                "Your answer",
                height=140,
                placeholder="Type your answer here…",
                key=f"ip_ans_{q_idx}",
            )

            col_next, col_skip = st.columns([4, 1])
            with col_next:
                btn_label = "Next Question →" if q_idx < total - 1 else "Finish & Get Feedback →"
                if st.button(btn_label, key=f"ip_next_{q_idx}",
                             disabled=not answer.strip(), use_container_width=True):
                    mock["answers"].append({"q": qs[q_idx]["q"], "a": answer.strip()})
                    if q_idx < total - 1:
                        mock["q_index"] += 1
                        st.session_state["ip_mock"] = mock
                        st.rerun()
                    else:
                        # All answered — evaluate
                        with st.spinner("Evaluating your answers…"):
                            fb = _evaluate_answers(mock["answers"], mock.get("role", role))
                        mock["feedback"] = fb
                        st.session_state["ip_mock"] = mock
                        st.rerun()
            with col_skip:
                if st.button("Skip", key=f"ip_skip_{q_idx}", use_container_width=True):
                    mock["answers"].append({"q": qs[q_idx]["q"], "a": "(skipped)"})
                    mock["q_index"] += 1 if q_idx < total - 1 else 0
                    st.session_state["ip_mock"] = mock
                    st.rerun()

        # ── Feedback ───────────────────────────────────────────────
        elif mock.get("feedback"):
            fb = mock["feedback"]
            st.markdown("### 📊 Interview Feedback")

            overall = int(fb.get("overall_score", 0))
            rec     = fb.get("recommendation", "")
            rec_colors = {
                "Strong Hire": "#1D9E75",
                "Hire":        "#0F6E56",
                "Maybe":       "#BA7517",
                "No Hire":     "#A32D2D",
            }
            rec_color = rec_colors.get(rec, "#888780")

            # Top KPIs
            k1, k2 = st.columns(2)
            with k1:
                st.markdown(
                    f'<div style="border:0.5px solid {_score_color(overall)}33;border-radius:12px;'
                    f'padding:14px;text-align:center">'
                    f'<div style="font-size:12px;color:var(--color-text-secondary)">Overall Score</div>'
                    f'<div style="font-size:36px;font-weight:500;color:{_score_color(overall)}">{overall}</div>'
                    f'</div>', unsafe_allow_html=True
                )
            with k2:
                st.markdown(
                    f'<div style="border:0.5px solid {rec_color}33;border-radius:12px;'
                    f'padding:14px;text-align:center">'
                    f'<div style="font-size:12px;color:var(--color-text-secondary)">AI Recommendation</div>'
                    f'<div style="font-size:20px;font-weight:500;color:{rec_color}">{rec}</div>'
                    f'</div>', unsafe_allow_html=True
                )

            if fb.get("summary"):
                st.info(fb["summary"])

            st.markdown("---")
            st.markdown("#### Per-Question Breakdown")

            per = fb.get("per_answer", [])
            for i, (qa, fb_item) in enumerate(zip(mock["answers"], per)):
                score = int(fb_item.get("score", 0))
                color = _score_color(score)
                with st.expander(f"Q{i+1}: {qa['q'][:70]}… — {score}/100", expanded=(score < 60)):
                    st.markdown(f"**Your answer:** {qa['a']}")
                    st.markdown("---")
                    col_s, col_i = st.columns(2)
                    with col_s:
                        st.markdown(
                            f'<div style="border-left:3px solid #1D9E75;padding:8px 10px;'
                            f'border-radius:0 6px 6px 0;background:var(--color-background-secondary);'
                            f'font-size:13px">✅ {fb_item.get("strength","")}</div>',
                            unsafe_allow_html=True,
                        )
                    with col_i:
                        st.markdown(
                            f'<div style="border-left:3px solid #BA7517;padding:8px 10px;'
                            f'border-radius:0 6px 6px 0;background:var(--color-background-secondary);'
                            f'font-size:13px">→ {fb_item.get("improvement","")}</div>',
                            unsafe_allow_html=True,
                        )

            st.markdown("---")
            if st.button("🔄 Try Again", key="ip_reset_mock", use_container_width=False):
                st.session_state["ip_mock"] = {
                    "started": False, "questions": [], "answers": [],
                    "q_index": 0, "feedback": None,
                }
                st.rerun()