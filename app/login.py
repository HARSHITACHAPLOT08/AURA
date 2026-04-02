import streamlit as st
import time

def render_login():
    # User and Lock SVGs remain
    user_svg = "data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%23FFFFFF' viewBox='0 0 16 16'%3E%3Cpath d='M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H3zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z'/%3E%3C/svg%3E"
    lock_svg = "data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%23FFFFFF' viewBox='0 0 16 16'%3E%3Cpath d='M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2zm3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z'/%3E%3C/svg%3E"

    st.markdown(f'''
    <style>
    /* ── RESET & BACKGROUND ────────────── */
    .stApp {{
        background: linear-gradient(145deg, #020617, #0B172E, #1E1B4B) !important;
        animation: fadeInSlideUp 0.8s ease-out;
    }}

    /* Global Glow Orb & Particle Background */
    .stApp::after {{
        content: ""; position: fixed; top: -20%; left: -10%; width: 50vw; height: 50vw;
        background: radial-gradient(circle, rgba(79,195,247,0.15) 0%, transparent 60%);
        filter: blur(100px); z-index: 0; pointer-events: none;
    }}
    .stApp::before {{
        content: ""; position: fixed; bottom: -20%; right: -10%; width: 60vw; height: 60vw;
        background: radial-gradient(circle, rgba(124,77,255,0.15) 0%, transparent 60%);
        filter: blur(120px); z-index: 0; pointer-events: none;
        animation: orbShift 10s infinite alternate ease-in-out;
    }}
    @keyframes orbShift {{ 100% {{ transform: translate(-50px, -50px); }} }}

    /* ── CENTERING LAYOUT ────────────── */
    /* Target the main wrapper to establish vertical viewport context */
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

    /* Fallback for classic layout classes */
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

    /* ── TITLE BLOCK ────────────── */
    .title-block {{
        text-align: center;
        margin-bottom: 30px;
        z-index: 10;
        position: relative;
    }}
    .login-logo {{ font-size: 3.5rem; text-shadow: 0 0 25px rgba(56,189,248,0.9); margin-bottom: 5px; }}
    .login-title {{
        font-size: 2.2rem; font-weight: 900;
        background: linear-gradient(135deg, #4FC3F7, #7C4DFF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px; text-shadow: 0 0 15px rgba(124, 77, 255, 0.4);
    }}
    .login-subtitle {{
        color: #E2E8F0; font-size: 0.95rem; font-weight: 600; text-shadow: 0 1px 5px rgba(0,0,0,0.8);
    }}

    /* ── REDESIGN: THE LOGIN CARD ────────────── */
    /* Transform Streamlit's native form boundary into the Glass Card */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(25px) saturate(160%) !important;
        -webkit-backdrop-filter: blur(25px) saturate(160%) !important;
        border: 1px solid rgba(79, 195, 247, 0.25) !important;
        border-radius: 20px !important;
        padding: 40px 35px 35px 35px !important;
        width: 100% !important;
        width: 400px !important;  /* Strictly lock width to prevent stretching */
        max-width: 100vw !important;
        box-sizing: border-box !important;
        margin: 0 auto !important; /* Explicit horizontal center */
        box-shadow: 0 25px 50px rgba(0,0,0,0.5), inset 0 0 20px rgba(124, 77, 255, 0.1) !important;
        transition: box-shadow 0.3s ease, border-color 0.3s ease !important;
        z-index: 10;
        position: relative;
    }}
    
    [data-testid="stForm"]:hover {{
        border-color: rgba(79, 195, 247, 0.5) !important;
        box-shadow: 0 30px 60px rgba(0,0,0,0.6), 0 0 30px rgba(79, 195, 247, 0.2) !important;
    }}

    [data-testid="stForm"] > div {{
        gap: 1.2rem !important; 
    }}

    /* ── INPUT FIELDS (CRITICAL FIX) ────────────── */
    [data-testid="stTextInput"] > div > div > input {{
        background-color: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(160, 174, 192, 0.3) !important;
        border-radius: 10px !important;
        color: #FFFFFF !important;
        height: 50px !important;
        padding: 12px 16px 12px 46px !important; /* Space for icon */
        font-size: 1rem !important;
        font-weight: 500 !important;
        transition: border-color 0.3s, box-shadow 0.3s, background-color 0.3s !important;
        width: 100% !important;
    }}

    /* SVG Icons for Inputs */
    [data-testid="stTextInput"]:nth-of-type(1) > div > div > input {{
        background-image: url("{user_svg}");
        background-position: 16px center; background-repeat: no-repeat;
    }}
    [data-testid="stTextInput"]:nth-of-type(2) > div > div > input {{
        background-image: url("{lock_svg}");
        background-position: 16px center; background-repeat: no-repeat;
    }}

    /* Placeholders */
    [data-testid="stTextInput"] > div > div > input::placeholder {{
        color: #94A3B8 !important; opacity: 1 !important;
    }}

    /* Focus States */
    [data-testid="stTextInput"] > div > div > input:focus {{
        border-color: #4FC3F7 !important;
        box-shadow: 0 0 20px rgba(79, 195, 247, 0.4) !important;
        background-color: rgba(15, 23, 42, 0.8) !important;
    }}

    /* Hide standard labels */
    [data-testid="stTextInput"] label {{ display: none !important; }}

    /* ── BUTTON REDESIGN ────────────── */
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
        box-shadow: 0 8px 25px rgba(124, 77, 255, 0.4) !important;
        transition: transform 0.2s ease, box-shadow 0.3s ease !important;
    }}
    
    [data-testid="stFormSubmitButton"] > button:hover {{
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 15px 35px rgba(79, 195, 247, 0.6) !important;
    }}
    [data-testid="stFormSubmitButton"] > button:active {{
        transform: scale(0.97) !important;
    }}
    </style>
    ''', unsafe_allow_html=True)

    # 1. Main Titles
    st.markdown('''
    <div class="title-block">
        <div class="login-logo">💠</div>
        <div class="login-title">AURA Secure Login</div>
        <div class="login-subtitle">AI-Powered Fraud Guardian Dashboard</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 2. Form - the CSS will strictly constrain the Form to 400px and center it inherently in Flex column
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
