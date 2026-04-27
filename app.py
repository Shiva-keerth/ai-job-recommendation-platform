import time
import streamlit as st
from streamlit_option_menu import option_menu

from modules.db          import init_db
from modules.auth        import verify_login, register_user, create_admin_if_missing
from modules.otp_service    import send_otp_email, verify_otp, clear_otp, otp_exists, seconds_remaining
from modules.email_validator import validate_email, get_email_suggestion
from modules.ui_candidate import candidate_dashboard
from modules.ui_employer  import employer_dashboard
from modules.ui_admin     import admin_dashboard
from modules.theme import inject_global_css, T

st.set_page_config(page_title="Skill Match AI", layout="centered", page_icon="🚀")

# Theme must default before inject
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

inject_global_css()

def _auth_css():
    p = T()
    return f"""<style>
.block-container{{padding-top:2.2rem;max-width:980px}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}
.fadeUp{{animation:fadeUp 420ms ease-out}}
.auth-hero{{padding:22px 26px;border-radius:18px;background:{p['SURFACE']};
  border:1px solid {p['CARD_BORDER']};margin-bottom:16px}}
.auth-title{{font-size:34px;font-weight:850;line-height:1.1;margin:0;color:{p['TEXT_HEADING']}}}
.auth-sub{{margin-top:10px;font-size:15px;color:{p['MUTED']}}}
.chips{{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}}
.chip{{padding:6px 10px;border-radius:999px;font-size:12px;font-weight:650;
  border:1px solid {p['CARD_BORDER']};background:{p['TAG_BG']};color:{p['TEXT']}}}
.auth-card{{padding:18px 18px 12px 18px;border-radius:18px;
  background:{p['SURFACE']};border:1px solid {p['CARD_BORDER']}}}
div.stButton>button{{border-radius:12px!important;padding:0.65rem 1rem!important;font-weight:800!important}}
.small-note{{font-size:12px;color:{p['MUTED']};margin-top:10px}}
.otp-box{{background:rgba(37,99,235,0.06);border:1px solid rgba(37,99,235,0.25);
  border-radius:14px;padding:16px;margin:12px 0}}
.otp-timer{{font-size:13px;color:#d97706;font-weight:600}}
.step-badge{{display:inline-block;background:#E8394D;color:#ffffff;
  border-radius:999px;padding:2px 10px;font-size:11px;font-weight:800;margin-bottom:8px}}
</style>"""
st.markdown(_auth_css(), unsafe_allow_html=True)

# ── Init ──────────────────────────────────────────────────────────────
init_db()
create_admin_if_missing("admin@project.com", "Admin@1234")

# ── Session state ─────────────────────────────────────────────────────
defaults = [
    ("logged_in",        False),
    ("user_email",       None),
    ("role",             None),
    ("auth_page",        "Login"),
    ("go_login",         False),
    ("welcome_toast",    None),
    ("login_pass_val",   ""),
    ("reg_pass_val",     ""),
    ("otp_stage",        "form"),
    ("otp_email",        ""),
    ("otp_password",     ""),
    ("otp_role",         "candidate"),
    ("menu_key",         0),
]
for k, v in defaults:
    if k not in st.session_state:
        st.session_state[k] = v

# ════════════════════════════════ NOT LOGGED IN ════════════════════════
if not st.session_state.logged_in:

    if st.session_state.go_login:
        st.session_state.auth_page = "Login"
        st.session_state.go_login  = False
        st.session_state.menu_key += 1

    st.markdown("""
    <div class="auth-hero fadeUp">
      <div class="auth-title">🚀 Skill Match AI</div>
      <div class="auth-sub">Skill-first matching · ATS shortlisting · Admin analytics</div>
      <div class="chips">
        <div class="chip">📄 Resume Parsing</div>
        <div class="chip">🎯 Smart Matching</div>
        <div class="chip">📚 Skill Gap Learning</div>
        <div class="chip">🏆 Leaderboard</div>
        <div class="chip">🛡️ Admin Analytics</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="auth-card fadeUp">', unsafe_allow_html=True)

    choice = option_menu(None, ["Login", "Register"],
                         icons=["box-arrow-in-right", "person-plus"],
                         orientation="horizontal",
                         key=f"auth_menu_idx_{st.session_state.menu_key}",
                         default_index=0 if st.session_state.auth_page == "Login" else 1)
    st.session_state.auth_page = choice

    # ── LOGIN ──────────────────────────────────────────────────────────
    if choice == "Login":
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")

        def _sync_lp(): st.session_state.login_pass_val = st.session_state.login_pass_input
        st.text_input("Password",
                      type="default" if st.session_state.get("show_login_pass") else "password",
                      value=st.session_state.login_pass_val,
                      key="login_pass_input", on_change=_sync_lp)
        st.checkbox("Show password", key="show_login_pass")

        if st.button("Login", use_container_width=True):
            email_val = email.strip().lower()
            with st.spinner("Authenticating..."):
                time.sleep(0.4)
            ok, role = verify_login(email_val, st.session_state.login_pass_input)
            if ok:
                st.session_state.logged_in   = True
                st.session_state.user_email  = email_val
                st.session_state.role        = role
                name = email_val.split("@")[0].split(".")[0].capitalize()
                st.session_state.welcome_toast = f"👋 Welcome back, {name}!"
                st.rerun()
            else:
                st.error("Invalid email or password ❌")

    # ── REGISTER ───────────────────────────────────────────────────────
    else:
        # ── STAGE 1: Fill registration form ──
        if st.session_state.otp_stage == "form":
            st.subheader("Register New Account")
            st.markdown('<div class="step-badge">Step 1 of 2 — Fill Details</div>', unsafe_allow_html=True)

            new_email = st.text_input("Email", key="reg_email", placeholder="you@example.com")

            def _sync_rp(): st.session_state.reg_pass_val = st.session_state.reg_pass_input
            st.text_input("Password",
                          type="default" if st.session_state.get("show_reg_pass") else "password",
                          value=st.session_state.reg_pass_val,
                          key="reg_pass_input", on_change=_sync_rp,
                          placeholder="Minimum 6 characters")
            st.checkbox("Show password", key="show_reg_pass")

            st.markdown("#### Select your role")
            role_choice = st.selectbox(
                "I am a...",
                options=["candidate", "employer"],
                format_func=lambda x:
                    "👤 Candidate — Upload resume, get recommendations, apply to jobs"
                    if x == "candidate" else
                    "👔 Employer — Post jobs, review applicants, shortlist with AI",
                key="role_dropdown"
            )

            st.divider()

            if st.button("Send Verification Code →", use_container_width=True, type="primary"):
                email_val    = new_email.strip().lower()
                password_val = st.session_state.reg_pass_input.strip()

                if not email_val:
                    st.error("⚠️ Please enter your email address.")
                elif len(password_val) < 6:
                    st.error("⚠️ Password must be at least 6 characters.")
                else:
                    # Level 1 + 2 — format and domain validation
                    with st.spinner("Validating email..."):
                        is_valid, val_msg = validate_email(email_val, check_domain=True)

                    if not is_valid:
                        st.error(f"❌ {val_msg}")
                        # Show typo suggestion if available
                        suggestion = get_email_suggestion(email_val)
                        if suggestion:
                            st.info(f"💡 Did you mean **{suggestion}**?")
                    else:
                        from modules.db import get_conn
                        conn = get_conn()
                        existing = conn.cursor().execute(
                            "SELECT email FROM users WHERE email=?", (email_val,)
                        ).fetchone()
                        conn.close()

                        if existing:
                            st.error("❌ This email is already registered. Please login.")
                        else:
                            with st.spinner("Sending verification code to your email..."):
                                ok, msg = send_otp_email(email_val)
                            if ok:
                                st.session_state.otp_email    = email_val
                                st.session_state.otp_password = password_val
                                st.session_state.otp_role     = role_choice
                                st.session_state.otp_stage    = "verify"
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                                st.info("💡 Set GMAIL_SENDER and GMAIL_APP_PWD in config.py to enable email OTP.")

        # ── STAGE 2: OTP verification ──
        elif st.session_state.otp_stage == "verify":
            st.subheader("Verify Your Email")
            st.markdown('<div class="step-badge">Step 2 of 2 — Enter OTP</div>', unsafe_allow_html=True)

            email_val = st.session_state.otp_email
            secs      = seconds_remaining(email_val)

            st.markdown(f"""
            <div class="otp-box">
              ✉️ A 6-digit code was sent to <strong>{email_val}</strong><br>
              <span class="otp-timer">⏱️ Expires in {secs // 60}m {secs % 60}s</span>
            </div>
            """, unsafe_allow_html=True)

            otp_input = st.text_input(
                "Enter 6-digit OTP",
                max_chars=6,
                placeholder="e.g. 482916",
                key="otp_input_field"
            )

            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("✅ Verify & Create Account", use_container_width=True, type="primary"):
                    if not otp_input.strip():
                        st.error("Please enter the OTP.")
                    else:
                        valid, vmsg = verify_otp(email_val, otp_input.strip())
                        if valid:
                            ok, reg_msg = register_user(
                                email_val,
                                st.session_state.otp_password,
                                st.session_state.otp_role
                            )
                            if ok:
                                st.success("🎉 Account created! Please login.")
                                st.session_state.otp_stage    = "form"
                                st.session_state.otp_email    = ""
                                st.session_state.otp_password = ""
                                st.session_state.otp_role     = "candidate"
                                time.sleep(1.2)
                                st.session_state.go_login = True
                                st.rerun()
                            else:
                                st.error(f"Registration error: {reg_msg}")
                        else:
                            st.error(f"❌ {vmsg}")

            with col2:
                if st.button("← Back", use_container_width=True):
                    clear_otp(email_val)
                    st.session_state.otp_stage = "form"
                    st.rerun()

            st.divider()
            if not otp_exists(email_val):
                st.warning("⚠️ Your OTP has expired.")

            if st.button("🔄 Resend OTP", use_container_width=True):
                with st.spinner("Resending..."):
                    ok, msg = send_otp_email(email_val)
                if ok:
                    st.success("✅ New OTP sent!")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="small-note">🔒 Passwords are securely hashed (PBKDF2-SHA256). OTP expires in 5 minutes.</div>',
        unsafe_allow_html=True
    )

# ════════════════════════════════ LOGGED IN ════════════════════════════
else:
    if st.session_state.welcome_toast:
        st.toast(st.session_state.welcome_toast, icon="✅")
        st.session_state.welcome_toast = None

    role  = (st.session_state.role or "").strip().lower()
    email = st.session_state.user_email or ""

    if role == "candidate":
        candidate_dashboard(email)
    elif role == "employer":
        employer_dashboard()
    elif role == "admin":
        admin_dashboard(email)
    else:
        st.error(f"Unknown role: '{role}'. Please contact support.")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()