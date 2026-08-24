"""
nova_auth.py — NovaMS animated sign-in flow

Drop-in replacement for the login block already in streamlit_app.py
(_FALLBACK_AUTH_USER / _FALLBACK_AUTH_PASS / _get_configured_users() /
_render_login_screen() / require_login()). Same session_state contract,
same secrets.toml credential source — just a nicer, three-step flow
(Email -> Code -> Success) styled with NovaMS's own --nova-* CSS
variables instead of the plain form.

INTEGRATION — in streamlit_app.py:

1. Add near your other imports, after the page-level CSS block that
   defines --nova-blue / --nova-bg / etc. (nova_auth reads those
   variables, so it must be injected after that CSS, not before):

       from nova_auth import require_login_animated

2. Replace this line:

       # require_login()

   with:

       require_login_animated()

That's it — _FALLBACK_AUTH_USER/_PASS and _get_configured_users() in
streamlit_app.py are reused as-is via the constants/function below, so
nothing about how credentials are configured changes. If you'd rather
not import from streamlit_app.py, copy those two lines and that
function down here instead — they're duplicated as safe defaults below
so this file also works standalone.
"""

import streamlit as st

# ── Safe standalone defaults (overridden by streamlit_app.py's versions
# if you import from there instead — see integration note above) ──────────
_FALLBACK_AUTH_USER = "demo"
_FALLBACK_AUTH_PASS = "novams2026"


def _get_configured_users() -> dict:
    try:
        users = dict(st.secrets["auth"]["users"])
        if users:
            return users
    except Exception:
        pass
    return {}


def _inject_auth_css():
    st.markdown(
        """
        <style>
        .nova-auth-wrap {
            max-width: 380px;
            margin: 7vh auto 0 auto;
            text-align: center;
        }
        .nova-auth-logo {
            width: 48px; height: 48px; border-radius: 11px;
            background: var(--nova-blue, #1D4DFF);
            display: inline-flex; align-items: center; justify-content: center;
            font-size: 22px; font-weight: 700; color: #fff; margin-bottom: 14px;
        }
        .nova-auth-title {
            font-size: 24px; font-weight: 700; color: var(--nova-ink, #F1F5F9);
            margin: 0 0 4px; letter-spacing: -0.01em;
        }
        .nova-auth-sub {
            font-size: 13px; color: var(--nova-ink-soft, #9AA4B2); margin: 0 0 26px;
        }
        div[data-testid="stForm"] div.stButton > button,
        div.stButton > button, div[data-testid="stFormSubmitButton"] button {
            border-radius: 999px !important;
            border: 1px solid var(--nova-border, #262B33) !important;
            background: rgba(255,255,255,0.05) !important;
            color: var(--nova-ink, #F1F5F9) !important;
            transition: background 0.2s ease, border-color 0.2s ease !important;
        }
        div.stButton > button:hover, div[data-testid="stFormSubmitButton"] button:hover {
            background: rgba(255,255,255,0.1) !important;
            border-color: rgba(255,255,255,0.3) !important;
        }
        div[data-testid="stFormSubmitButton"] button[kind="primary"],
        div.stButton > button[kind="primary"] {
            background: var(--nova-blue, #1D4DFF) !important;
            color: #fff !important; border: none !important; font-weight: 600 !important;
        }
        div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover,
        div.stButton > button[kind="primary"]:hover {
            filter: brightness(0.9);
        }
        .nova-auth-wrap div.stTextInput > div > div > input {
            border-radius: 999px !important;
            background: transparent !important;
            border: 1px solid var(--nova-border, #262B33) !important;
            color: var(--nova-ink, #F1F5F9) !important;
            text-align: center !important;
            letter-spacing: 0.25em;
        }
        .nova-auth-wrap div.stTextInput label { display: none; }
        .nova-auth-divider {
            display: flex; align-items: center; gap: 12px;
            color: var(--nova-ink-soft, #9AA4B2); font-size: 12.5px; margin: 16px 0;
        }
        .nova-auth-divider .line { flex: 1; height: 1px; background: var(--nova-border, #262B33); }
        .nova-auth-legal {
            font-size: 11px; color: var(--nova-muted, #6B7688); margin-top: 22px; line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_flow_state():
    st.session_state.setdefault("_auth_flow_step", "credentials")   # credentials -> code -> success
    st.session_state.setdefault("_auth_pending_user", "")


def _render_credentials_step():
    st.markdown(
        """
        <div class="nova-auth-wrap">
          <div class="nova-auth-logo">N</div>
          <div class="nova-auth-title">NovaMS</div>
          <div class="nova-auth-sub">Sign in to continue</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    configured_users = _get_configured_users()
    using_fallback = not configured_users

    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        if using_fallback:
            st.markdown(
                '<div class="missing-box">⚠️ No <code>[auth]</code> section found in '
                '<code>secrets.toml</code> — using a fallback demo login '
                f'(<code>{_FALLBACK_AUTH_USER}</code> / <code>{_FALLBACK_AUTH_PASS}</code>). '
                'Set real credentials before sharing this deployment.</div>',
                unsafe_allow_html=True,
            )

        with st.form("nova_auth_credentials_form"):
            username = st.text_input("Username", placeholder="Username")
            password = st.text_input("Password", type="password", placeholder="Password")
            submitted = st.form_submit_button("Continue", use_container_width=True, type="primary")

        if submitted:
            valid_users = configured_users if configured_users else {_FALLBACK_AUTH_USER: _FALLBACK_AUTH_PASS}
            if username in valid_users and password == valid_users[username]:
                st.session_state["_auth_pending_user"] = username
                st.session_state["_auth_flow_step"] = "code"
                st.rerun()
            else:
                st.error("❌ Incorrect username or password.")

        st.markdown(
            '<div class="nova-auth-legal">Access is limited to authorized NovaMS users. '
            "Contact your administrator for credentials.</div>",
            unsafe_allow_html=True,
        )


def _render_code_step():
    st.markdown(
        f"""
        <div class="nova-auth-wrap">
          <div class="nova-auth-title">Verify it's you</div>
          <div class="nova-auth-sub">Enter the 6-digit code sent for {st.session_state['_auth_pending_user']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        code = st.text_input(
            "Code", key="_nova_auth_code", max_chars=6,
            placeholder="------", label_visibility="collapsed",
        )
        col_back, col_continue = st.columns([1, 2])
        with col_back:
            if st.button("Back", use_container_width=True):
                st.session_state["_auth_flow_step"] = "credentials"
                st.session_state.pop("_nova_auth_code", None)
                st.rerun()
        with col_continue:
            ready = len(code) == 6
            if st.button("Verify", use_container_width=True, disabled=not ready, type="primary"):
                st.session_state["_auth_flow_step"] = "success"
                st.rerun()
        if st.button("Resend code", use_container_width=False):
            st.info(f"Code resent for {st.session_state['_auth_pending_user']}.")
        st.caption(
            "No SMS/email delivery is wired up yet — any 6-digit code passes. "
            "Plug in a real OTP service (Twilio, SES, etc.) here when ready."
        )


def _render_success_step():
    st.markdown(
        """
        <div class="nova-auth-wrap">
          <div class="nova-auth-title">You're in!</div>
          <div class="nova-auth-sub">Welcome to NovaMS</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        if st.button("Continue to Dashboard", use_container_width=True, type="primary"):
            st.session_state["_authenticated"] = True
            st.session_state["_auth_user"] = st.session_state["_auth_pending_user"]
            st.session_state.pop("_auth_flow_step", None)
            st.session_state.pop("_auth_pending_user", None)
            st.session_state.pop("_nova_auth_code", None)
            st.rerun()


def render_login_screen_animated():
    """Renders the 3-step sign-in flow. Call require_login_animated()
    instead of this directly, unless you're managing st.stop() yourself."""
    _inject_auth_css()
    _init_flow_state()
    step = st.session_state["_auth_flow_step"]
    if step == "credentials":
        _render_credentials_step()
    elif step == "code":
        _render_code_step()
    else:
        _render_success_step()


def require_login_animated():
    """Drop-in replacement for require_login() in streamlit_app.py.
    Same contract: sets st.session_state["_authenticated"] = True and
    st.session_state["_auth_user"] on success, calls st.stop() until then."""
    if not st.session_state.get("_authenticated"):
        render_login_screen_animated()
        st.stop()
