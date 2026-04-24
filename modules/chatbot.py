import streamlit as st
import time

try:
    from config import ANTHROPIC_API_KEY
except ImportError:
    ANTHROPIC_API_KEY = ""


# ══════════════════════════════════════════════════════════════════════
# RULE-BASED RESPONSES
# ══════════════════════════════════════════════════════════════════════
def _rule_based(msg: str, ctx: dict):
    m    = msg.lower().strip()
    role = ctx.get("role", "")
    sk   = ctx.get("skills", [])
    cat  = ctx.get("category", "")
    sub  = ctx.get("subcategory", "")
    em   = ctx.get("email", "")
    name = em.split("@")[0].split(".")[0].capitalize() if em else "there"

    if any(w in m for w in ["hello","hi","hey","hii","namaste"]):
        return (f"Hey {name}! 👋 I'm your AI Career Assistant.\n\n"
                "I can help with:\n• Job matching & scores\n• Resume tips\n"
                "• Skill gaps & learning\n• Platform guidance\n\nWhat do you need?")

    if any(w in m for w in ["who are you","what are you","what can you do"]):
        return "I'm your AI Career Assistant 🤖\nPowered by rules + Claude AI.\nAsk me anything about your career or this platform!"

    if any(w in m for w in ["my skills","what skills","skills i have"]):
        if sk:
            return (f"Your detected skills:\n\n**{', '.join(sk[:15])}**"
                    + (f"\n_(+{len(sk)-15} more)_" if len(sk)>15 else "")
                    + f"\n\nTotal: **{len(sk)} skills** found.\n💡 Go to Recommendations tab!")
        return "No skills yet!\n\nGo to **Resume Upload** tab and upload your PDF resume first."

    if any(w in m for w in ["my category","which field","job category"]):
        if cat:
            sub_line = f"\n\n🏷️ **Specialization:** {sub}" if sub else ""
            return (f"Your job category:\n\n**🎯 {cat}**{sub_line}"
                    f"\n\nThe system prioritizes {cat} jobs for your primary matches.")
        return "No category detected yet. Upload your resume first!"

    if any(w in m for w in ["improve resume","resume tips","improve score","boost score","increase score"]):
        return ("Top resume improvement tips:\n\n"
                "1. Add more technical skills\n"
                "2. Use job description keywords\n"
                "3. Describe projects with tools used\n"
                "4. Quantify achievements (e.g. improved speed by 40%)\n"
                "5. Check **Skill Gap tab** — shows exact skills to add!")

    if any(w in m for w in ["skill gap","missing skills","what to learn","what should i learn"]):
        return ("To see your skill gaps:\n\n"
                "1. Upload resume ✅\n"
                "2. Go to **Skill Gap** tab\n"
                "3. See chart of missing skills\n"
                "4. Click free learning links 📚\n\n"
                "Learning these directly improves your match scores!")

    if any(w in m for w in ["how to apply","apply for job","submit application"]):
        return ("To apply to a job:\n\n"
                "1. Go to **Recommendations** tab\n"
                "2. Browse AI-matched jobs\n"
                "3. Click **Apply** on any job\n"
                "4. Track in **Applications** tab ✅")

    if any(w in m for w in ["match score","score calculated","recruiter","ats mode","optimistic","how is score"]):
        return ("3 scoring modes:\n\n"
                "🎯 **Recruiter** — Core×72% + Secondary×18% + Context×10%\n"
                "🚀 **Optimistic** — Recruiter score + 8% boost\n"
                "🤖 **ATS** — Strict penalty like real hiring systems\n\n"
                "Core skills = top 6 most important skills for the job\n"
                "Soft skills are de-weighted to 25%")

    if any(w in m for w in ["how to use","help","guide","get started"]):
        if role == "candidate":
            return ("Candidate quick start:\n\n"
                    "1. 📄 Resume Upload → Upload PDF\n"
                    "2. 🎯 Recommendations → See matched jobs\n"
                    "3. ✅ Apply to jobs you like\n"
                    "4. 📚 Skill Gap → Learn missing skills\n"
                    "5. 📋 Applications → Track status")
        elif role == "employer":
            return ("Employer quick start:\n\n"
                    "1. 📌 Post Job → Create listing\n"
                    "2. 📥 Applications → See applicants\n"
                    "3. 🏆 AI Leaderboard → Ranked candidates\n"
                    "4. ⚖️ Compare → Side by side view\n"
                    "5. ✅ Shortlist / Reject with one click")
        elif role == "admin":
            return ("Admin quick start:\n\n"
                    "1. 📊 Overview → Platform KPIs & charts\n"
                    "2. 👥 Users → Manage all accounts\n"
                    "3. 💼 Jobs → Control all job listings\n"
                    "4. 📋 Applications → All activity\n"
                    "5. 📈 Skill Demand → Market analytics")
        return "3 roles: 👤 Candidate | 🏢 Employer | 🛡️ Admin"

    if any(w in m for w in ["how to post","post job","create job","add job"]):
        return ("To post a job:\n\n"
                "1. Go to **Post Job** tab\n"
                "2. Fill title, company, required skills\n"
                "3. Add job description\n"
                "4. Click **Post Job** ✅\n\n"
                "Candidates will start matching immediately!")

    if any(w in m for w in ["leaderboard","rank candidates","best candidates"]):
        return ("The **AI Leaderboard** ranks ALL applicants.\n\n"
                "Each candidate shows:\n"
                "• Match score\n• Matched & missing skills\n"
                "• Badge (Strong/Moderate/Weak)\n\n"
                "Go to **AI Leaderboard** tab!")

    if any(w in m for w in ["salary","pay","ctc","package","lpa"]):
        return ("General salary ranges:\n\n"
                "📊 Data Science/ML — ₹6–20 LPA\n"
                "💻 Software Dev — ₹4–18 LPA\n"
                "☁️ Cloud/DevOps — ₹6–22 LPA\n"
                "📈 Data Analytics — ₹4–14 LPA\n"
                "🎨 UI/UX Design — ₹3–12 LPA")

    if any(w in m for w in ["tf-idf","tfidf","cosine","vectorizer"]):
        return ("**TF-IDF** converts text to numbers.\n"
                "**Cosine Similarity** measures similarity.\n\n"
                "Together = context score (10% of final match).\n"
                "Remaining 90% = direct skill matching.")

    if any(w in m for w in ["thank","thanks","great","awesome","good","nice"]):
        return "You're welcome! 😊 Ask me anything else!"

    if any(w in m for w in ["bye","goodbye","see you"]):
        return f"Goodbye {name}! 👋 Best of luck! 🚀"

    return None


# ══════════════════════════════════════════════════════════════════════
# CLAUDE AI RESPONSE
# ══════════════════════════════════════════════════════════════════════
def _claude_ai(message: str, history: list, ctx: dict) -> str:
    if not ANTHROPIC_API_KEY or "YOUR" in ANTHROPIC_API_KEY:
        return ("I can answer common questions!\n\nTry asking:\n"
                "• My skills\n• How to improve score\n"
                "• Skill gap\n• How to use platform")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        system = f"""You are an AI Career Assistant in the Skill Match AI platform.
User: {ctx.get('email','').split('@')[0]} | Role: {ctx.get('role','user')}
Category: {ctx.get('category','unknown')} | Specialization: {ctx.get('subcategory','unknown')}
Skills: {', '.join(ctx.get('skills',[])[:15]) or 'none yet'}
Platform: Resume upload, AI job matching (Recruiter/Optimistic/ATS modes),
Skill Gap tab, Employer Leaderboard, Admin Dashboard.
Be helpful, concise, friendly. Max 100 words. Use bullet points."""

        msgs = []
        for t in history[-4:]:
            msgs.append({"role":"user",      "content": t["user"]})
            msgs.append({"role":"assistant", "content": t["assistant"]})
        msgs.append({"role":"user","content": message})

        r = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=250, system=system, messages=msgs
        )
        return r.content[0].text
    except Exception as e:
        return f"AI unavailable right now. Try again!\n_(Error: {str(e)[:50]})_"


def get_response(message: str, history: list, ctx: dict) -> str:
    rule = _rule_based(message, ctx)
    return rule if rule else _claude_ai(message, history, ctx)


# ══════════════════════════════════════════════════════════════════════
# CHATBOT UI
# ══════════════════════════════════════════════════════════════════════
def render_chatbot(user_email="", role="", skills=None, category="", subcategory=""):
    if skills is None:
        skills = []

    # ── Init session state ──────────────────────────────────────────
    open_key    = f"chat_open_{role}"
    history_key = f"chat_history_{role}"
    if open_key    not in st.session_state: st.session_state[open_key]    = False
    if history_key not in st.session_state: st.session_state[history_key] = []

    ctx  = {"email": user_email, "role": role, "skills": skills, "category": category, "subcategory": subcategory}
    name = user_email.split("@")[0].split(".")[0].capitalize() if user_email else "there"
    hist = st.session_state[history_key]

    # ── FAB toggle button ───────────────────────────────────────────
    st.markdown("---")
    fab_label = "✕ Close Chat" if st.session_state[open_key] else "💬 AI Assistant"
    if st.button(fab_label, key=f"chat_toggle_{role}_{len(hist)}",
                 use_container_width=False):
        st.session_state[open_key] = not st.session_state[open_key]
        st.rerun()

    if not st.session_state[open_key]:
        return

    # ── Chat header ─────────────────────────────────────────────────
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1E2761,#243070);
         padding:16px 20px;border-radius:16px 16px 0 0;
         display:flex;align-items:center;gap:12px;
         border:1.5px solid rgba(79,195,247,0.4);border-bottom:none;margin-top:8px'>
      <div style='width:42px;height:42px;background:linear-gradient(135deg,#4FC3F7,#1565C0);
           border-radius:50%;display:flex;align-items:center;
           justify-content:center;font-size:22px'>🤖</div>
      <div>
        <div style='font-weight:800;font-size:16px;color:#fff'>AI Career Assistant</div>
        <div style='font-size:12px;color:#4FC3F7'>Rule-based + Claude AI</div>
      </div>
      <div style='margin-left:auto;display:flex;align-items:center;gap:6px'>
        <div style='width:9px;height:9px;background:#00C896;border-radius:50%;
             box-shadow:0 0 8px #00C896'></div>
        <span style='font-size:11px;color:#00C896;font-weight:600'>Online</span>
      </div>
    </div>
    <div style='background:rgba(13,27,75,0.95);
         border:1.5px solid rgba(79,195,247,0.4);border-top:none;
         border-radius:0 0 16px 16px;padding:16px;margin-bottom:8px'>
    </div>
    """, unsafe_allow_html=True)

    # ── Welcome message ─────────────────────────────────────────────
    if not hist:
        st.info(f"👋 Hey {name}! Ask me about job matching, resume tips, skill gaps, or how to use this platform.")

    # ── Message history ─────────────────────────────────────────────
    for turn in hist:
        with st.chat_message("user"):
            st.write(turn["user"])
        with st.chat_message("assistant"):
            st.write(turn["assistant"])

    # ── Quick suggestion buttons ─────────────────────────────────────
    if not hist:
        sugs = {
            "candidate": ["What are my skills?",   "How to improve score?", "What should I learn?"],
            "employer":  ["How to post a job?",     "How does AI ranking work?", "How to compare candidates?"],
            "admin":     ["How to manage users?",   "What does skill demand show?", "How to close a job?"],
        }.get(role, ["How to use platform?", "What is match score?", "How to apply?"])

        st.markdown("**Quick questions:**")
        cols = st.columns(len(sugs))
        for i, (col, sug) in enumerate(zip(cols, sugs)):
            with col:
                if st.button(sug, key=f"sug_{role}_{i}", use_container_width=True):
                    with st.spinner("Thinking..."):
                        reply = get_response(sug, [], ctx)
                    hist.append({"user": sug, "assistant": reply})
                    st.session_state[history_key] = hist
                    st.rerun()

    # ── Input ────────────────────────────────────────────────────────
    user_input = st.chat_input(f"Ask me anything...", key=f"chat_input_{role}")
    if user_input and user_input.strip():
        with st.spinner("Thinking..."):
            reply = get_response(user_input.strip(), hist, ctx)
        hist.append({"user": user_input.strip(), "assistant": reply})
        st.session_state[history_key] = hist
        st.rerun()

    # ── Clear ────────────────────────────────────────────────────────
    if hist:
        if st.button("🗑️ Clear conversation", key=f"clr_{role}", use_container_width=True):
            st.session_state[history_key] = []
            st.rerun()