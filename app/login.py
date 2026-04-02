import streamlit as st
import time
from pathlib import Path


def _get_login_bg_b64():
    """Load background image as base64 — prefer committed PNG in assets/, fall back to scratch .b64 file."""
    import base64
    root = Path(__file__).parent.parent

    # Primary: assets/login_bg.png (committed to repo, always available)
    png_path = root / "assets" / "login_bg.png"
    if not png_path.exists():
        # fallback to older cyber_bg.png if present
        png_path = root / "assets" / "cyber_bg.png"
    if png_path.exists():
        with open(png_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    # Fallback: local dev scratch file
    b64_path = root / "login_bg.b64"
    if b64_path.exists():
        with open(b64_path, "r") as f:
            return f.read().strip()

    return ""


def render_login():
    bg_b64 = _get_login_bg_b64()

    user_svg = "data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%23FFFFFF' viewBox='0 0 16 16'%3E%3Cpath d='M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H3zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z'/%3E%3C/svg%3E"
    lock_svg = "data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%23FFFFFF' viewBox='0 0 16 16'%3E%3Cpath d='M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2zm3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z'/%3E%3C/svg%3E"

    # Build background CSS only if image data is available
    bg_css = ""
    if bg_b64:
        bg_css = f"""
        /* ── FULL-SCREEN BACKGROUND IMAGE WITH SLOW ZOOM ── */
        /* body::before sits at z-index -1, cleanly behind all Streamlit layers */
        body::before {{
            content: '';
            position: fixed;
            inset: 0;
            width: 100vw;
            height: 100vh;
            background-image: url('data:image/png;base64,{bg_b64}');
            background-size: cover;
            background-position: center center;
            background-repeat: no-repeat;
            z-index: -1;
            pointer-events: none;
            animation: loginBgZoom 20s ease-in-out infinite alternate;
        }}

        /* ── BASE HTML/BODY — must be transparent for ::before to show ── */
        html, body {{
            background: transparent !important;
        }}

        /* ── DARK OVERLAY on .stApp (sits above ::before) ── */
        .stApp {{
            background: rgba(2, 6, 23, 0.60) !important;
        }}

        /* ── GLOW OVERLAY (blue → purple) on .stApp::before ── */
        .stApp::before {{
            content: '';
            position: fixed;
            inset: 0;
            width: 100vw;
            height: 100vh;
            background:
                radial-gradient(ellipse at 20% 50%, rgba(56, 189, 248, 0.14) 0%, transparent 55%),
                radial-gradient(ellipse at 80% 30%, rgba(124, 58, 237, 0.12) 0%, transparent 55%),
                radial-gradient(ellipse at 50% 80%, rgba(79, 195, 247, 0.08) 0%, transparent 60%);
            z-index: 0;
            pointer-events: none;
            animation: loginGlowPulse 8s ease-in-out infinite alternate;
        }}

        @keyframes loginBgZoom {{
            0%   {{ transform: scale(1);    }}
            100% {{ transform: scale(1.06); }}
        }}

        @keyframes loginGlowPulse {{
            0%   {{ opacity: 0.55; }}
            100% {{ opacity: 1.0; }}
        }}
        """

    st.markdown(f"""
    <style>
    /* ── BASE: dark fallback; bg_css overrides this when image is available ── */
    .stApp {{
        background: #020617 !important;
    }}

    {bg_css}

    /* ── FREEZE OLD pseudo ::before / ::after grid junk on login page ── */
    .stApp::after {{
        display: none !important;
    }}

    /* ── CENTERING LAYOUT ── */
    [data-testid="stAppViewBlockContainer"] {{
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        min-height: 100vh !important;
        max-width: 100% !important;
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
    }}

    .block-container {{
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        min-height: 100vh !important;
        max-width: 100% !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }}

    /* ── TITLE BLOCK ── */
    .title-block {{
        text-align: center;
        margin-bottom: 30px;
        z-index: 10;
        position: relative;
    }}
    .login-logo {{
        font-size: 3.5rem;
        text-shadow: 0 0 30px rgba(56, 189, 248, 1.0);
        margin-bottom: 5px;
        display: block;
    }}
    .login-title {{
        font-size: 2.4rem;
        font-weight: 900;
        background: linear-gradient(135deg, #4FC3F7, #7C4DFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
        filter: drop-shadow(0 0 20px rgba(124, 77, 255, 0.7));
    }}
    .login-subtitle {{
        color: #CBD5E1;
        font-size: 0.95rem;
        font-weight: 600;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.95);
        margin-top: 4px;
    }}

    /* ── GLASS CARD (ENHANCED for visibility over image) ── */
    [data-testid="stForm"] {{
        background: rgba(4, 12, 32, 0.60) !important;
        backdrop-filter: blur(36px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(36px) saturate(180%) !important;
        border: 1px solid rgba(79, 195, 247, 0.32) !important;
        border-radius: 22px !important;
        padding: 44px 40px 40px 40px !important;
        width: 420px !important;
        max-width: 96vw !important;
        box-sizing: border-box !important;
        margin: 0 auto !important;
        box-shadow:
            0 32px 64px rgba(0, 0, 0, 0.70),
            0 0 48px rgba(56, 189, 248, 0.10),
            inset 0 0 28px rgba(124, 77, 255, 0.08) !important;
        transition: box-shadow 0.35s ease, border-color 0.35s ease !important;
        z-index: 10;
        position: relative;
    }}

    [data-testid="stForm"]:hover {{
        border-color: rgba(79, 195, 247, 0.58) !important;
        box-shadow:
            0 38px 72px rgba(0, 0, 0, 0.80),
            0 0 60px rgba(56, 189, 248, 0.22),
            inset 0 0 28px rgba(124, 77, 255, 0.14) !important;
    }}

    [data-testid="stForm"] > div {{
        gap: 1.2rem !important;
    }}

    /* ── INPUT FIELDS ── */
    [data-testid="stTextInput"] > div > div > input {{
        background-color: rgba(8, 20, 50, 0.65) !important;
        border: 1px solid rgba(160, 174, 192, 0.35) !important;
        border-radius: 10px !important;
        color: #FFFFFF !important;
        height: 50px !important;
        padding: 12px 16px 12px 46px !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        transition: border-color 0.3s, box-shadow 0.3s, background-color 0.3s !important;
        width: 100% !important;
    }}

    [data-testid="stTextInput"]:nth-of-type(1) > div > div > input {{
        background-image: url("{user_svg}");
        background-position: 16px center;
        background-repeat: no-repeat;
    }}
    [data-testid="stTextInput"]:nth-of-type(2) > div > div > input {{
        background-image: url("{lock_svg}");
        background-position: 16px center;
        background-repeat: no-repeat;
    }}

    [data-testid="stTextInput"] > div > div > input::placeholder {{
        color: #94A3B8 !important;
        opacity: 1 !important;
    }}

    [data-testid="stTextInput"] > div > div > input:focus {{
        border-color: #4FC3F7 !important;
        box-shadow: 0 0 22px rgba(79, 195, 247, 0.50) !important;
        background-color: rgba(10, 25, 60, 0.85) !important;
    }}

    [data-testid="stTextInput"] label {{ display: none !important; }}

    /* ── SUBMIT BUTTON ── */
    [data-testid="stFormSubmitButton"] > button {{
        background: linear-gradient(135deg, #38bdf8, #7c3aed) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        height: 50px !important;
        width: 100% !important;
        margin-top: 10px !important;
        box-shadow: 0 8px 28px rgba(124, 77, 255, 0.50) !important;
        transition: transform 0.2s ease, box-shadow 0.3s ease !important;
    }}

    [data-testid="stFormSubmitButton"] > button:hover {{
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 18px 42px rgba(79, 195, 247, 0.70) !important;
    }}
    [data-testid="stFormSubmitButton"] > button:active {{
        transform: scale(0.97) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # (No div injection needed — background is handled entirely via CSS on html/body and .stApp)

    # 1. Titles
    st.markdown("""
    <div class="title-block">
        <span class="login-logo">💠</span>
        <div class="login-title">AURA Secure Login</div>
        <div class="login-subtitle">AI-Powered Fraud Guardian Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Form
    with st.form("web3_login_form", clear_on_submit=False):
        user = st.text_input("Username", placeholder="Enter your ID")
        pwd = st.text_input("Password", type="password", placeholder="••••••••")
        submit = st.form_submit_button("Authenticate System", use_container_width=True)

        if submit:
            if user and pwd:
                with st.spinner("Establishing secure connection..."):
                    time.sleep(1.2)
                st.session_state.logged_in = True
                st.session_state.username = user
                st.rerun()
            else:
                st.error("Please provide valid credentials.")
