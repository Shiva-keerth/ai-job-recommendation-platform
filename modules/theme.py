import streamlit as st


# ── Dual palette system ────────────────────────────────────────────────────────

DARK_PALETTE = {
    "BG": "#0a0e17", "SURFACE": "#161b22", "CARD_BG": "#161b22",
    "CARD_BORDER": "#30363d", "SIDEBAR_BG": "#0d1117",
    "TEXT": "#f0f6fc", "TEXT_HEADING": "#f0f6fc", "MUTED": "#8b949e",
    "INPUT_BG": "#0d1117", "INPUT_BORDER": "#30363d", "INPUT_TEXT": "#f0f6fc",
    "TAG_BG": "#21262d", "TAG_BORDER": "#30363d",
    "TABLE_HEADER": "#161b22", "TABLE_BORDER": "#21262d",
    "TABLE_TEXT": "#f0f6fc", "TABLE_ROW": "#0d1117",
    "SCROLLBAR_TRACK": "#0d1117", "SCROLLBAR_THUMB": "#30363d",
    "HOVER_BG": "rgba(232,57,77,0.08)", "EXPANDER_BG": "#161b22",
    "FILE_UP_BG": "#0d1117", "FILE_UP_BORDER": "#30363d",
    "BTN_SEC_BG": "#161b22", "BTN_SEC_TEXT": "#f0f6fc", "BTN_SEC_BORDER": "#30363d",
    "PROGRESS_BG": "#21262d", "SCORE_BAR_BG": "#21262d",
    "NAV_HOVER": "#161b22", "NAV_SELECTED": "rgba(232,57,77,0.12)",
}

LIGHT_PALETTE = {
    "BG": "#ffffff", "SURFACE": "#f8f9fb", "CARD_BG": "#ffffff",
    "CARD_BORDER": "#e2e8f0", "SIDEBAR_BG": "#f1f5f9",
    "TEXT": "#1a1a2e", "TEXT_HEADING": "#1a1a2e", "MUTED": "#64748b",
    "INPUT_BG": "#ffffff", "INPUT_BORDER": "#cbd5e1", "INPUT_TEXT": "#1a1a2e",
    "TAG_BG": "#f1f5f9", "TAG_BORDER": "#e2e8f0",
    "TABLE_HEADER": "#f1f5f9", "TABLE_BORDER": "#e2e8f0",
    "TABLE_TEXT": "#1a1a2e", "TABLE_ROW": "#f1f5f9",
    "SCROLLBAR_TRACK": "#f1f5f9", "SCROLLBAR_THUMB": "#cbd5e1",
    "HOVER_BG": "rgba(232,57,77,0.05)", "EXPANDER_BG": "#f8f9fb",
    "FILE_UP_BG": "#f8f9fb", "FILE_UP_BORDER": "#cbd5e1",
    "BTN_SEC_BG": "#ffffff", "BTN_SEC_TEXT": "#1a1a2e", "BTN_SEC_BORDER": "#cbd5e1",
    "PROGRESS_BG": "#e2e8f0", "SCORE_BAR_BG": "#e2e8f0",
    "NAV_HOVER": "#f1f5f9", "NAV_SELECTED": "rgba(232,57,77,0.10)",
}

# Shared accent colors
PRIMARY = "#E8394D"
SUCCESS = "#16a34a"
WARNING = "#d97706"
INFO    = "#2563eb"
PURPLE  = "#7c3aed"


def get_theme() -> str:
    return st.session_state.get("theme", "dark")

def T() -> dict:
    return DARK_PALETTE if get_theme() == "dark" else LIGHT_PALETTE

def _t(key: str) -> str:
    return T()[key]

# Module-level tokens (synced on each inject)
MUTED = "#8b949e"
CARD_BG = "#161b22"
CARD_BORDER = "#30363d"
SURFACE = "#161b22"
TEXT = "#f0f6fc"
TEXT_DIM = "#8b949e"
SIDEBAR_BG = "#0d1117"

def _sync_tokens():
    global MUTED, CARD_BG, CARD_BORDER, SURFACE, TEXT, TEXT_DIM, SIDEBAR_BG
    p = T()
    MUTED = p["MUTED"]; CARD_BG = p["CARD_BG"]; CARD_BORDER = p["CARD_BORDER"]
    SURFACE = p["SURFACE"]; TEXT = p["TEXT"]; TEXT_DIM = p["MUTED"]; SIDEBAR_BG = p["SIDEBAR_BG"]


# ── Dynamic CSS ────────────────────────────────────────────────────────────────

def _build_css() -> str:
    p = T()
    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
*, *::before, *::after {{ box-sizing: border-box; }}
html, body, [data-testid="stAppViewContainer"] {{
    font-family: 'DM Sans', sans-serif !important;
    background-color: {p['BG']} !important; color: {p['TEXT']} !important;
}}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none !important; }}
[data-testid="stHeader"] {{ display: none !important; height: 0 !important; }}
[data-testid="stMain"] > div:first-child {{ padding: 0 !important; }}
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"] {{ background: {p['SIDEBAR_BG']} !important; border-right: 1px solid {p['CARD_BORDER']} !important; }}
[data-testid="stSidebar"] > div {{ padding: 20px 12px !important; }}
h1, h2, h3, h4 {{ font-family: 'DM Sans', sans-serif !important; color: {p['TEXT_HEADING']} !important; font-weight: 700 !important; letter-spacing: -0.3px !important; }}
.stMarkdown h1 {{ font-size: 22px !important; margin: 0 0 4px !important; }}
.stMarkdown h2 {{ font-size: 17px !important; margin: 20px 0 8px !important; }}
.stMarkdown h3 {{ font-size: 15px !important; margin: 16px 0 6px !important; }}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div, [data-testid="stMultiSelect"] > div > div {{
    background: {p['INPUT_BG']} !important; border: 1px solid {p['INPUT_BORDER']} !important;
    border-radius: 8px !important; color: {p['INPUT_TEXT']} !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 14px !important; transition: border-color 0.15s !important;
}}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {{
    border-color: #E8394D !important; box-shadow: 0 0 0 3px rgba(232,57,77,0.15) !important; outline: none !important;
}}
[data-testid="stTextInput"] label, [data-testid="stTextArea"] label, [data-testid="stSelectbox"] label {{
    color: {p['MUTED']} !important; font-size: 12px !important; font-weight: 500 !important;
    text-transform: uppercase !important; letter-spacing: 0.5px !important; margin-bottom: 4px !important;
}}
[data-testid="stButton"] > button[kind="primary"], .stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #E8394D, #c0392b) !important; color: white !important;
    border: none !important; border-radius: 8px !important; font-weight: 600 !important;
    font-size: 14px !important; padding: 10px 20px !important; transition: all 0.2s !important;
    box-shadow: 0 2px 8px rgba(232,57,77,0.3) !important;
}}
[data-testid="stButton"] > button[kind="primary"]:hover {{
    transform: translateY(-1px) !important; box-shadow: 0 4px 16px rgba(232,57,77,0.4) !important;
}}
[data-testid="stButton"] > button:not([kind="primary"]), .stButton > button:not([kind="primary"]) {{
    background: {p['BTN_SEC_BG']} !important; color: {p['BTN_SEC_TEXT']} !important;
    border: 1px solid {p['BTN_SEC_BORDER']} !important; border-radius: 8px !important;
    font-weight: 500 !important; font-size: 14px !important; padding: 10px 20px !important; transition: all 0.15s !important;
}}
[data-testid="stButton"] > button:not([kind="primary"]):hover {{
    border-color: #E8394D !important; color: #E8394D !important; background: {p['HOVER_BG']} !important;
}}
[data-testid="stProgress"] > div > div {{ background: {p['PROGRESS_BG']} !important; border-radius: 99px !important; height: 6px !important; }}
[data-testid="stProgress"] > div > div > div {{ border-radius: 99px !important; background: linear-gradient(90deg, #E8394D, #f97316) !important; }}
[data-testid="stMetric"] {{ background: {p['SURFACE']} !important; border: 1px solid {p['CARD_BORDER']} !important; border-radius: 12px !important; padding: 16px 20px !important; }}
[data-testid="stMetricLabel"] {{ color: {p['MUTED']} !important; font-size: 12px !important; font-weight: 500 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; }}
[data-testid="stMetricValue"] {{ color: {p['TEXT']} !important; font-size: 28px !important; font-weight: 700 !important; font-family: 'DM Sans' !important; }}
[data-testid="stAlert"] {{ border-radius: 10px !important; border-left-width: 3px !important; font-size: 13px !important; }}
[data-testid="stDataFrame"] {{ border-radius: 10px !important; overflow: hidden !important; border: 1px solid {p['TABLE_BORDER']} !important; }}
[data-testid="stDataFrame"] th {{ background: {p['TABLE_HEADER']} !important; color: {p['MUTED']} !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; border-bottom: 1px solid {p['TABLE_BORDER']} !important; }}
[data-testid="stDataFrame"] td {{ color: {p['TABLE_TEXT']} !important; font-size: 13px !important; border-bottom: 1px solid {p['TABLE_ROW']} !important; }}
[data-testid="stTabs"] [data-baseweb="tab-list"] {{ background: {p['BG']} !important; border-bottom: 1px solid {p['CARD_BORDER']} !important; gap: 4px !important; }}
[data-testid="stTabs"] [data-baseweb="tab"] {{ background: transparent !important; color: {p['MUTED']} !important; font-size: 13px !important; font-weight: 500 !important; border-radius: 6px 6px 0 0 !important; padding: 8px 16px !important; border-bottom: 2px solid transparent !important; }}
[data-testid="stTabs"] [aria-selected="true"] {{ color: #E8394D !important; border-bottom: 2px solid #E8394D !important; background: rgba(232,57,77,0.04) !important; }}
[data-testid="stExpander"] {{ background: {p['EXPANDER_BG']} !important; border: 1px solid {p['CARD_BORDER']} !important; border-radius: 10px !important; margin-bottom: 8px !important; }}
[data-testid="stExpander"] summary {{ color: {p['TEXT']} !important; font-size: 14px !important; font-weight: 500 !important; }}
hr {{ border-color: {p['CARD_BORDER']} !important; margin: 20px 0 !important; }}
[data-testid="stSpinner"] {{ color: #E8394D !important; }}
[data-testid="stFileUploader"] {{ background: {p['FILE_UP_BG']} !important; border: 2px dashed {p['FILE_UP_BORDER']} !important; border-radius: 12px !important; padding: 20px !important; transition: border-color 0.2s !important; }}
[data-testid="stFileUploader"]:hover {{ border-color: #E8394D !important; }}
[data-testid="stSelectbox"] svg {{ color: {p['MUTED']} !important; }}
[data-testid="stRadio"] label {{ color: {p['TEXT']} !important; font-size: 13px !important; }}
.nav-link {{ border-radius: 8px !important; }}
.nav-link:hover {{ background: {p['NAV_HOVER']} !important; }}
.nav-link-selected {{ background: {p['NAV_SELECTED']} !important; color: #E8394D !important; }}
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {p['SCROLLBAR_TRACK']}; }}
::-webkit-scrollbar-thumb {{ background: {p['SCROLLBAR_THUMB']}; border-radius: 99px; }}
::-webkit-scrollbar-thumb:hover {{ background: #E8394D; }}
[data-testid="stDownloadButton"] > button {{ background: linear-gradient(135deg, #E8394D, #c0392b) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }}
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {{ background: #E8394D !important; border-color: #E8394D !important; }}
.stCaptionContainer, [data-testid="stCaptionContainer"] {{ color: {p['MUTED']} !important; font-size: 12px !important; }}
[data-testid="stArrowVegaLiteChart"] canvas {{ border-radius: 8px; }}

/* ── Deep overrides for all Streamlit internals ── */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
[data-testid="stSidebar"] section {{ background: transparent !important; }}
[data-testid="stSidebar"] * {{ color: {p['TEXT']} !important; }}
[data-testid="stSidebar"] .nav-link {{ color: {p['MUTED']} !important; }}
[data-testid="stSidebar"] .nav-link-selected {{ color: #E8394D !important; }}

/* ── Form, column, block backgrounds ── */
[data-testid="stForm"] {{ background: {p['SURFACE']} !important; border: 1px solid {p['CARD_BORDER']} !important; border-radius: 10px !important; padding: 16px !important; }}
[data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"] {{ background: transparent !important; }}
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span {{ color: {p['TEXT']} !important; }}
.stMarkdown strong {{ color: {p['TEXT_HEADING']} !important; }}

/* ── Chart / graph containers ── */
[data-testid="stArrowVegaLiteChart"] {{ background: {p['SURFACE']} !important; border-radius: 10px !important; padding: 8px !important; }}
[data-testid="stVegaLiteChart"] {{ background: {p['SURFACE']} !important; border-radius: 10px !important; }}

/* ── Selectbox dropdown ── */
[data-baseweb="select"] {{ background: {p['INPUT_BG']} !important; }}
[data-baseweb="popover"] {{ background: {p['SURFACE']} !important; border: 1px solid {p['CARD_BORDER']} !important; }}
[data-baseweb="menu"] {{ background: {p['SURFACE']} !important; }}
[data-baseweb="menu"] li {{ color: {p['TEXT']} !important; }}
[data-baseweb="menu"] li:hover {{ background: {p['HOVER_BG']} !important; }}

/* ── Multiselect ── */
[data-baseweb="tag"] {{ background: {p['TAG_BG']} !important; color: {p['TEXT']} !important; }}

/* ── Checkbox / toggle ── */
[data-testid="stCheckbox"] label span {{ color: {p['TEXT']} !important; }}

/* ── Toast / status ── */
[data-testid="stToast"] {{ background: {p['SURFACE']} !important; color: {p['TEXT']} !important; border: 1px solid {p['CARD_BORDER']} !important; }}

/* ── Widget labels ── */
.stSelectbox label, .stMultiSelect label, .stSlider label,
.stRadio label, .stCheckbox label, .stNumberInput label,
.stTextInput label, .stTextArea label, .stDateInput label {{
    color: {p['MUTED']} !important;
}}

/* ── Markdown text in main area ── */
[data-testid="stMarkdownContainer"] {{ color: {p['TEXT']} !important; }}
[data-testid="stMarkdownContainer"] p {{ color: {p['TEXT']} !important; }}
[data-testid="stMarkdownContainer"] li {{ color: {p['TEXT']} !important; }}
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {{ color: {p['TEXT_HEADING']} !important; }}

/* ── File uploader internals ── */
[data-testid="stFileUploader"] label {{ color: {p['MUTED']} !important; }}
[data-testid="stFileUploader"] section {{ background: {p['FILE_UP_BG']} !important; }}
[data-testid="stFileUploader"] section > div {{ color: {p['TEXT']} !important; }}
[data-testid="stFileUploadDropzone"] {{ background: {p['FILE_UP_BG']} !important; color: {p['TEXT']} !important; }}

/* ── Success/warning/error/info boxes ── */
[data-testid="stAlert"] div {{ color: inherit !important; }}

/* ── Option menu sidebar override ── */
[data-testid="stSidebar"] .nav-item {{ color: {p['MUTED']} !important; }}

/* ── Divider ── */
[data-testid="stSidebar"] hr {{ border-color: {p['CARD_BORDER']} !important; }}
</style>"""


def inject_global_css():
    """Call this once in app.py before any rendering."""
    _sync_tokens()
    st.markdown(_build_css(), unsafe_allow_html=True)


# ── Theme toggle widget ───────────────────────────────────────────────────────

def render_theme_toggle():
    """Render a dark/light toggle in the sidebar."""
    current = get_theme()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("☀️ Light", use_container_width=True,
                      type="primary" if current == "light" else "secondary"):
            st.session_state["theme"] = "light"; st.rerun()
    with c2:
        if st.button("🌙 Dark", use_container_width=True,
                      type="primary" if current == "dark" else "secondary"):
            st.session_state["theme"] = "dark"; st.rerun()


# ── Page header ────────────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str = "", icon: str = "", color: str = PRIMARY):
    p = T()
    icon_html = f'<span style="margin-right:10px;font-size:22px">{icon}</span>' if icon else ""
    sub_html  = f'<div style="font-size:13px;color:{p["MUTED"]};margin-top:4px;font-weight:400">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div style="border-left:3px solid {color};padding:10px 0 10px 16px;margin-bottom:24px">
        <div style="font-size:22px;font-weight:700;color:{p['TEXT_HEADING']};line-height:1.2">
            {icon_html}{title}
        </div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


# ── Stat cards ─────────────────────────────────────────────────────────────────

def stat_card(label: str, value, delta: str = "", color: str = PRIMARY) -> str:
    p = T()
    delta_html = f'<div style="font-size:11px;color:{p["MUTED"]};margin-top:2px">{delta}</div>' if delta else ""
    return f"""
    <div style="background:{p['SURFACE']};border:1px solid {p['CARD_BORDER']};
                border-radius:12px;padding:18px 20px;border-top:3px solid {color}">
        <div style="font-size:11px;color:{p['MUTED']};font-weight:600;text-transform:uppercase;
                    letter-spacing:0.6px;margin-bottom:8px">{label}</div>
        <div style="font-size:28px;font-weight:700;color:{p['TEXT_HEADING']};line-height:1">{value}</div>
        {delta_html}
    </div>"""

def render_stat_row(stats: list[dict]):
    cols = st.columns(len(stats))
    for col, s in zip(cols, stats):
        with col:
            st.markdown(stat_card(
                label=s.get("label",""), value=s.get("value","—"),
                delta=s.get("delta",""), color=s.get("color", PRIMARY),
            ), unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)


# ── Badge ──────────────────────────────────────────────────────────────────────

STATUS_COLORS = {
    "applied":     ("#2563eb", "#dbeafe"), "shortlisted": ("#d97706", "#fef3c7"),
    "interview":   ("#7c3aed", "#ede9fe"), "selected":    ("#16a34a", "#dcfce7"),
    "rejected":    ("#dc2626", "#fee2e2"), "open":        ("#16a34a", "#dcfce7"),
    "closed":      ("#dc2626", "#fee2e2"), "candidate":   ("#2563eb", "#dbeafe"),
    "employer":    ("#d97706", "#fef3c7"), "admin":       ("#7c3aed", "#ede9fe"),
}

DARK_STATUS_COLORS = {
    "applied":     ("#3b82f6", "#1d3a6e"), "shortlisted": ("#f59e0b", "#4a3000"),
    "interview":   ("#a78bfa", "#3b2f6e"), "selected":    ("#22c55e", "#0f3d1f"),
    "rejected":    ("#ef4444", "#4a1515"), "open":        ("#22c55e", "#0f3d1f"),
    "closed":      ("#ef4444", "#4a1515"), "candidate":   ("#3b82f6", "#1d3a6e"),
    "employer":    ("#f59e0b", "#4a3000"), "admin":       ("#a78bfa", "#3b2f6e"),
}

def badge(text: str, status: str = "") -> str:
    key = status.lower() if status else text.lower()
    colors = DARK_STATUS_COLORS if get_theme() == "dark" else STATUS_COLORS
    fg, bg = colors.get(key, ("#94a3b8", "#1e2530" if get_theme() == "dark" else "#f1f5f9"))
    return (f'<span style="background:{bg};color:{fg};border:1px solid {fg}33;'
            f'padding:2px 10px;border-radius:99px;font-size:11px;font-weight:600;'
            f'text-transform:uppercase;letter-spacing:0.4px">{text}</span>')


# ── Job card ───────────────────────────────────────────────────────────────────

def match_badge(score: float) -> str:
    if score >= 0.70:   return badge("Strong Match", "selected")
    elif score >= 0.40: return badge("Moderate Match", "shortlisted")
    else:               return badge("Weak Match", "rejected")

def score_bar_html(score: float, recruiter: float = 0, optimistic: float = 0, ats: float = 0) -> str:
    p = T()
    pct   = round(score * 100, 1)
    color = SUCCESS if score >= 0.70 else (WARNING if score >= 0.40 else "#ef4444")
    fill  = round(score * 100)
    return f"""
    <div style="margin:10px 0">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
            <span style="font-size:12px;color:{p['MUTED']};font-weight:500">Match Score</span>
            <span style="font-size:18px;font-weight:700;color:{color}">{pct}%</span>
        </div>
        <div style="background:{p['SCORE_BAR_BG']};border-radius:99px;height:6px;overflow:hidden">
            <div style="width:{fill}%;background:linear-gradient(90deg,{color},{color}99);
                        height:100%;border-radius:99px;transition:width 0.4s ease"></div>
        </div>
    </div>"""

def job_card_header(title: str, company: str, location: str, work_mode: str,
                    level: str, salary: str, category: str, posted: str) -> str:
    p = T()
    tags = " ".join([
        f'<span style="background:{p["TAG_BG"]};border:1px solid {p["TAG_BORDER"]};color:{p["MUTED"]};'
        f'padding:2px 8px;border-radius:6px;font-size:11px">{t}</span>'
        for t in [category, work_mode, level] if t
    ])
    return f"""
    <div style="background:{p['SURFACE']};border:1px solid {p['CARD_BORDER']};border-radius:14px;
                padding:20px 22px;margin-bottom:2px;border-top:2px solid {p['CARD_BORDER']}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
            <div>
                <div style="font-size:17px;font-weight:700;color:{p['TEXT_HEADING']};margin-bottom:3px">{title}</div>
                <div style="font-size:13px;color:{p['MUTED']}">
                    🏢 <strong style="color:{p['TEXT_HEADING']}">{company}</strong>
                    {"&nbsp;·&nbsp;📍 " + location if location else ""}
                    {"&nbsp;·&nbsp;💰 " + salary if salary else ""}
                    {"&nbsp;·&nbsp;🗓️ " + posted if posted else ""}
                </div>
            </div>
        </div>
        <div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap">{tags}</div>
    </div>"""


# ── Section header ─────────────────────────────────────────────────────────────

def section_header(title: str, caption: str = ""):
    p = T()
    cap = f'<div style="font-size:12px;color:{p["MUTED"]};margin-top:2px">{caption}</div>' if caption else ""
    st.markdown(f"""
    <div style="margin:28px 0 14px">
        <div style="font-size:16px;font-weight:700;color:{p['TEXT_HEADING']}">{title}</div>
        {cap}
    </div>""", unsafe_allow_html=True)


# ── Empty state ────────────────────────────────────────────────────────────────

def empty_state(icon: str, title: str, subtitle: str = "", cta: str = ""):
    p = T()
    st.markdown(f"""
    <div style="text-align:center;padding:60px 20px;background:{p['SURFACE']};
                border:1px solid {p['CARD_BORDER']};border-radius:16px;margin:20px 0">
        <div style="font-size:48px;margin-bottom:16px">{icon}</div>
        <div style="font-size:17px;font-weight:700;color:{p['TEXT_HEADING']};margin-bottom:8px">{title}</div>
        <div style="font-size:13px;color:{p['MUTED']};max-width:360px;margin:0 auto">{subtitle}</div>
        {"<div style='margin-top:16px;font-size:13px;color:#E8394D;font-weight:500'>"+cta+"</div>" if cta else ""}
    </div>""", unsafe_allow_html=True)


# ── Topbar ─────────────────────────────────────────────────────────────────────

def topbar(role: str, name: str, page: str):
    p = T()
    role_color = {"candidate": INFO, "employer": WARNING, "admin": PURPLE}.get(role.lower(), PRIMARY)
    role_label = role.capitalize()
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:12px 0 20px;border-bottom:1px solid {p['CARD_BORDER']};margin-bottom:24px">
        <div style="display:flex;align-items:center;gap:12px">
            <span style="background:{role_color}22;color:{role_color};border:1px solid {role_color}44;
                         padding:3px 10px;border-radius:99px;font-size:11px;font-weight:700;
                         text-transform:uppercase;letter-spacing:0.5px">{role_label}</span>
            <span style="color:{p['MUTED']};font-size:13px">›</span>
            <span style="color:{p['TEXT_HEADING']};font-size:14px;font-weight:600">{page}</span>
        </div>
        <div style="font-size:12px;color:{p['MUTED']}">👤 {name}</div>
    </div>""", unsafe_allow_html=True)


# ── Skill chips ────────────────────────────────────────────────────────────────

def skill_chips(skills: list, color: str = INFO, max_show: int = 20) -> str:
    p = T()
    chips = "".join(
        f'<span style="background:{color}18;color:{color};border:1px solid {color}33;'
        f'padding:2px 9px;border-radius:6px;font-size:12px;font-weight:500;'
        f'margin:2px;display:inline-block">{s}</span>'
        for s in skills[:max_show]
    )
    more = f'<span style="color:{p["MUTED"]};font-size:12px;margin-left:4px">+{len(skills)-max_show} more</span>' \
           if len(skills) > max_show else ""
    return f'<div style="display:flex;flex-wrap:wrap;gap:2px;margin:6px 0">{chips}{more}</div>'


# ── Card wrapper ───────────────────────────────────────────────────────────────

def card(content_html: str, padding: str = "20px 22px", border_color: str = "") -> str:
    p = T()
    bc = border_color or p["CARD_BORDER"]
    return f"""
    <div style="background:{p['SURFACE']};border:1px solid {bc};
                border-radius:14px;padding:{padding};margin-bottom:12px">
        {content_html}
    </div>"""