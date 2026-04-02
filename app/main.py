"""
AURA — AI-Powered Real-Time Fraud Detection & Financial Guardian System
Fintech-grade Streamlit Dashboard (Stripe / Paytm inspired)
"""
import sys, json, time, uuid, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="AURA — Fraud Detection", page_icon="🛡️",
                   layout="wide", initial_sidebar_state="expanded")

# ── Core UI Imports & State Setup ────────────────
import os
import importlib
sys.path.append(os.path.dirname(__file__))
import login
import chatbot
importlib.reload(login)
importlib.reload(chatbot)
from login import render_login
from chatbot import render_chatbot

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'theme' not in st.session_state: st.session_state.theme = 'dark'

# Load custom external CSS and handle dynamic theming without JS
with open(Path(__file__).parent / 'style.css', 'r', encoding='utf-8') as f:
    css = f.read()
    if st.session_state.theme == 'dark':
        css = css.replace('[data-theme="dark"]', ':root')
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)


if not st.session_state.logged_in:
    render_login()
    st.stop()

# ── Engine ────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="⚡ Loading AURA models…")
def load_engine():
    from backend.model_engine import predict, models_ready
    from backend.database     import save_transaction, get_recent_transactions, get_stats, init_db
    from backend.alert_system import get_recommendations, get_phishing_examples, get_pattern_comparison
    init_db()
    return predict, models_ready, save_transaction, get_recent_transactions, get_stats, \
           get_recommendations, get_phishing_examples, get_pattern_comparison

predict_fn,models_ready_fn,save_tx,get_history,get_stats_fn,get_recs,get_phishing,get_patterns=load_engine()

# ── State ────────────────────────────────────────────────────────
for k,v in [("transactions",[]),("streaming",False),("last_result",None)]:
    if k not in st.session_state: st.session_state[k]=v

# ── Helpers ────────────────────────────────────────────────────────
MERCHANT_LABELS = {1:"Groceries",2:"Retail",3:"Online",4:"Travel",5:"Luxury"}
DAY_LABELS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
def risk_color(lv): return {"Low":"#10b981","Medium":"#f59e0b","High":"#ef4444"}.get(lv,"#94a3b8")
def risk_emoji(lv): return {"Low":"✅","Medium":"⚠️","High":"🚨"}.get(lv,"ℹ️")
def badge_cls(lv): return {"Low":"low","Medium":"medium","High":"high"}.get(lv,"low")

def make_gauge(prob, level):
    col = risk_color(level)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(prob*100,1),
        number={"suffix":"%","font":{"size":40,"color":col,"family":"Inter"}},
        gauge={"axis":{"range":[0,100],"tickcolor":"#1e2d45","tickwidth":1,"tickfont":{"color":"#475569"}},
               "bar":{"color":col,"thickness":0.25},
               "bgcolor":"rgba(0,0,0,0)","borderwidth":0,
               "steps":[{"range":[0,35],"color":"rgba(16,185,129,.1)"},
                        {"range":[35,65],"color":"rgba(245,158,11,.1)"},
                        {"range":[65,100],"color":"rgba(239,68,68,.1)"}],
               "threshold":{"line":{"color":col,"width":3},"thickness":.85,"value":prob*100}}))
    fig.update_layout(transition_duration=700, height=210, margin=dict(t=20,b=0,l=20,r=20),
                      paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"))
    return fig

def make_shap_chart(top):
    feats = list(top.keys())
    vals  = [top[f]["shap"] for f in feats]
    cols  = ["#ef4444" if v>0 else "#10b981" for v in vals]
    fig = go.Figure(go.Bar(x=vals, y=feats, orientation="h", marker_color=cols,
                           text=[f"{v:+.3f}" for v in vals], textposition="outside",
                           textfont=dict(color="#94a3b8", size=10)))
    fig.update_layout(transition_duration=700, height=270, margin=dict(t=5,b=5,l=5,r=60),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=True,
                                 zerolinecolor="#2d4263", color="#475569"),
                      yaxis=dict(autorange="reversed", color="#94a3b8"),
                      font=dict(family="Inter"))
    return fig

def random_transaction(src="stream"):
    fraud = random.random() < .15
    if fraud:
        return dict(amount=round(random.uniform(500,4999),2), hour=random.choice([0,1,2,3,22,23]),
                    day_of_week=random.randint(0,6), merchant_cat=random.choice([3,4,5]),
                    location_risk=round(random.uniform(.65,1),3), device_trust=round(random.uniform(0,.35),3),
                    past_fraud_ct=random.randint(1,4), velocity_1h=random.randint(6,20),
                    dist_home_km=round(random.uniform(300,5000),1), card_age_days=random.randint(1,60),
                    is_online=True, source=src, transaction_id=f"STR-{uuid.uuid4().hex[:8].upper()}")
    return dict(amount=round(random.uniform(5,800),2), hour=random.randint(8,22),
                day_of_week=random.randint(0,6), merchant_cat=random.choice([1,2,3]),
                location_risk=round(random.uniform(0,.3),3), device_trust=round(random.uniform(.6,1),3),
                past_fraud_ct=0, velocity_1h=random.randint(1,4),
                dist_home_km=round(random.uniform(0,80),1), card_age_days=random.randint(100,3000),
                is_online=random.choice([True,False]), source=src,
                transaction_id=f"STR-{uuid.uuid4().hex[:8].upper()}")


# ════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-logo">💠</div>
        <div class="sidebar-name">AURA</div>
        <div class="sidebar-tag">AI Fraud Guardian</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["🏠 Dashboard", "🔍 Live Detection", "📊 Analytics", "🔐 Cyber Awareness"],
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if models_ready_fn():
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;background:rgba(16,185,129,0.08);
                    border:1px solid rgba(16,185,129,0.25);border-radius:10px;padding:10px 14px">
            <div style="width:8px;height:8px;background:#10b981;border-radius:50%;flex-shrink:0;
                        box-shadow:0 0 6px #10b981"></div>
            <div style="font-size:0.8rem;font-weight:600;color:#10b981">Models Online</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;background:rgba(239,68,68,0.08);
                    border:1px solid rgba(239,68,68,0.25);border-radius:10px;padding:10px 14px">
            <div style="width:8px;height:8px;background:#ef4444;border-radius:50%;flex-shrink:0"></div>
            <div style="font-size:0.8rem;font-weight:600;color:#ef4444">Models Offline</div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Run `python ml/train_model.py` first.")

    st.markdown('<hr><div class="sidebar-footer">AURA v1.0 &nbsp;·&nbsp; Hackathon Edition<br><span style="color:#64748b">© 2025 AI Financial Guardian</span></div>', unsafe_allow_html=True)
    theme_choice = st.toggle("🌙 Dark Mode", value=(st.session_state.theme == "dark"))
    new_theme = "dark" if theme_choice else "light"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()



# Marquee shifted down after Top Navbar
# ════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ════════════════════════════════════════════════════════════════════
_page_meta = {
    "🏠 Dashboard":      ("🏠 Overview Dashboard",       "Real-time transaction monitoring & fraud analytics"),
    "🔍 Live Detection": ("🔍 Live Transaction Scanner",  "Analyze transactions with XGBoost + SHAP explainability"),
    "📊 Analytics":      ("📊 Deep Analytics",            "Historical patterns, feature importance & trend analysis"),
    "🔐 Cyber Awareness":("🔐 Cybersecurity Hub",         "Phishing awareness, safe patterns & security education"),
}
_htitle, _hsub = _page_meta.get(page, ("AURA", ""))
def render_top_navbar(title, subtitle):
    username = st.session_state.get("username", "System Admin")
    html = f"""<div class="top-navbar">
<div class="nav-left">
<h1 class="nav-title">{title}</h1>
<div class="nav-subtitle">{subtitle}</div>
</div>
<div class="nav-search-container">
<span class="nav-search-icon">🔍</span>
<input type="text" class="nav-search-input" placeholder="Search transactions, analytics...">
</div>
<div class="nav-right-cluster">
<div class="nav-wallet">
<span>₹</span> 24,500.00
</div>
<div class="nav-icon-btn" title="Toggle Theme">
<span>🌓</span>
</div>
<div class="nav-icon-btn notification-container" title="Notifications">
<span>🔔</span>
<div class="notification-badge">3</div>
<!-- Dropdown Tray -->
<div class="notification-dropdown">
    <div class="notif-header">Recent Alerts</div>
    <div class="notif-item">🚨 <strong>SUS-9BA5</strong> flagged for Velocity.</div>
    <div class="notif-item">💵 ₹3,813 transaction blocked successfully.</div>
    <div class="notif-item">⚙️ ML Pipeline Retrained.</div>
</div>
</div>
<div class="nav-user">
<div class="nav-avatar-icon">👨🏻‍💻</div>
<div class="nav-user-text" style="white-space: nowrap;">
<span class="nav-user-name">{username}</span>
<span class="nav-user-sub">Premium Tier</span>
</div>
</div>
</div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)

_htitle, _hsub = _page_meta.get(page, ("AURA", ""))
render_top_navbar(_htitle, _hsub)

# Marquee Alert Bar immediately beneath the Top Navbar
st.markdown('''
<div class="marquee-container">
    <div class="marquee-content">
        🚀 EXCLUSIVE HACKATHON PREVIEW · Global Neural Threat Network Active · Defending 1,938 Nodes · Last Detection 4 seconds ago · Zero False Positives logged in 24 hours · AURA Fintech Engine Online 🚀
    </div>
</div>
''', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    stats   = get_stats_fn()
    history = get_history(200)

    # Custom Custom High-Impact KPI Matrix
    st.markdown(f"""<div class="kpi-wrapper">
<div class="kpi-card">
<div class="kpi-title">💳 Total Transactions</div>
<div class="kpi-value glow-blue">{stats['total']:,}</div>
<div class="kpi-sub">All time volume</div>
</div>
<div class="kpi-card">
<div class="kpi-title">🚨 Fraud Detected</div>
<div class="kpi-value glow-fraud">{stats['fraud']:,}</div>
<div class="kpi-sub" style="color: #FF4D4D;">{stats['fraud_rate']}% block rate</div>
</div>
<div class="kpi-card">
<div class="kpi-title">✅ Legitimate</div>
<div class="kpi-value glow-safe">{stats['legit']:,}</div>
<div class="kpi-sub">Securely cleared</div>
</div>
<div class="kpi-card">
<div class="kpi-title">🛡️ Detection Engine</div>
<div class="kpi-value glow-purple">99.2%</div>
<div class="kpi-sub">Neural net accuracy</div>
</div>
</div>""", unsafe_allow_html=True)

    # Charts row
    col_line, col_pie = st.columns([2, 1], gap="medium")
    with col_line:
        st.markdown('<div class="card-title">📈 Transaction Volume & Fraud Trend</div>', unsafe_allow_html=True)
        if history:
            df_h = pd.DataFrame(history)
            df_h["timestamp"] = pd.to_datetime(df_h["timestamp"])
            df_h["bin"] = df_h["timestamp"].dt.floor("1min")
            g = df_h.groupby("bin")["is_fraud"].agg(["count","sum"]).reset_index()
            g.columns = ["t","total","fraud"]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=g["t"],y=g["total"],name="Total Txns",fill="tozeroy",
                fillcolor="rgba(59,130,246,.12)",line=dict(color="#3b82f6",width=2)))
            fig.add_trace(go.Scatter(x=g["t"],y=g["fraud"],name="Fraud",fill="tozeroy",
                fillcolor="rgba(239,68,68,.15)",line=dict(color="#ef4444",width=2)))
            fig.update_layout(transition_duration=700, height=240,margin=dict(t=5,b=5,l=0,r=0),
                paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#94a3b8"),orientation="h",y=1.1),
                xaxis=dict(color="#475569",showgrid=False,zeroline=False),
                yaxis=dict(color="#475569",gridcolor="#1e2d45"),font=dict(family="Inter"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        else:
            st.markdown('<div style="height:200px;display:flex;align-items:center;justify-content:center;color:#334155;font-size:.85rem">Submit transactions in Live Detection to see data here</div>', unsafe_allow_html=True)

    with col_pie:
        st.markdown('<div class="card-title">🎯 Risk Distribution</div>', unsafe_allow_html=True)
        if history:
            df_h = pd.DataFrame(history)
            rc_data = df_h["risk_level"].value_counts().reset_index()
            rc_data.columns = ["level","count"]
            fig2 = go.Figure(go.Pie(
                labels=rc_data["level"],values=rc_data["count"],hole=.6,
                marker_colors=[{"Low":"#4ade80","Medium":"#fbbf24","High":"#f87171"}.get(l,"#64748b") for l in rc_data["level"]],
                textfont=dict(color="#e2e8f0",size=12),
            ))
            fig2.update_layout(transition_duration=700, height=240,margin=dict(t=5,b=5,l=5,r=5),
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#94a3b8")),
                font=dict(family="Inter"))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        else:
            st.markdown('<div style="height:200px;display:flex;align-items:center;justify-content:center;color:#334155;font-size:.85rem">No data yet</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # Alerts + Table side by side
    col_alerts, col_table = st.columns([1,2], gap="medium")

    with col_alerts:
        st.markdown('<div class="card-title">🚨 Live Alerts</div>', unsafe_allow_html=True)
        if history:
            df_h = pd.DataFrame(history)
            fraud_rows = df_h[df_h["is_fraud"]==True].head(6)
            if not fraud_rows.empty:
                for _, row in fraud_rows.iterrows():
                    st.markdown(f"""
                    <div class="alert-banner alert-high" style="background: rgba(255, 77, 77, 0.1); border-color: rgba(255, 77, 77, 0.5);">
                      <div style="font-size:1.3rem">🚨</div>
                      <div>
                        <div class="alert-text">
                            <span style="color:#FFFFFF; font-weight:800; font-size:0.85rem; letter-spacing:0.5px; text-shadow:0 0 6px rgba(79,195,247,0.5);">{row['transaction_id']}</span>
                            <span style="color:#A0AEC0;">&nbsp;·&nbsp;</span>
                            <span style="color:#00E676; font-weight:800; font-size:0.9rem;">₹{row['amount']:,.0f}</span>
                        </div>
                        <div class="alert-sub" style="margin-top:3px;">
                            <span style="color:#FF4D4D; font-weight:800; text-shadow:0 0 8px rgba(255,77,77,0.5);">{row['fraud_probability']*100:.1f}% fraud probability</span>
                            <span style="color:#A8CFFF; font-size:0.75rem;">&nbsp;· {str(row['timestamp'])[:16]}</span>
                        </div>
                      </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert-banner alert-low"><div style="font-size:1.2rem">✅</div><div class="alert-text">All clear — no fraud detected</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#334155;font-size:.82rem;padding:12px 0">Run transactions to see alerts</div>', unsafe_allow_html=True)

    with col_table:
        st.markdown('<div class="card-title">📋 Recent Transactions</div>', unsafe_allow_html=True)
        if history:
            df_d = pd.DataFrame(history)[["transaction_id","timestamp","amount","risk_level","fraud_probability","is_fraud","source"]].head(15)
            df_d["Probability"] = (df_d["fraud_probability"]*100).round(1).astype(str)+"%"
            df_d["Amount"]      = df_d["amount"].apply(lambda x:f"₹{x:,.2f}")
            df_d["Fraud"]       = df_d["is_fraud"].map({True:"🚨 Yes",False:"✅ No"})
            df_d = df_d.rename(columns={"transaction_id":"ID","timestamp":"Time","risk_level":"Risk","source":"Source"})
            st.dataframe(df_d[["ID","Time","Amount","Risk","Probability","Fraud","Source"]],
                         use_container_width=True, hide_index=True, height=300)
        else:
            st.info("No transactions yet.")

# ════════════════════════════════════════════════════════════════════
# LIVE DETECTION
# ════════════════════════════════════════════════════════════════════
elif page == "🔍 Live Detection":
    if not models_ready_fn():
        st.error("⚠️ Models not loaded — run `python ml/train_model.py` first.")
        st.stop()

    tab_m, tab_s = st.tabs(["✍️  Manual Input", "⚡  Auto Stream"])

    with tab_m:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        with st.form("tx_form"):
            st.markdown('<div class="card-title">💳 Transaction Parameters</div>', unsafe_allow_html=True)
            r1c1, r1c2, r1c3 = st.columns(3, gap="medium")
            with r1c1:
                amount       = st.number_input("💰 Amount (₹)", .01, 100000., 250., step=10.)
                hour         = st.slider("🕐 Hour of Day", 0, 23, 14)
                day_of_week  = st.selectbox("📅 Day", list(range(7)), format_func=lambda x: DAY_LABELS[x])
            with r1c2:
                merchant_cat  = st.selectbox("🎦 Merchant Category", list(MERCHANT_LABELS.keys()), format_func=lambda x:MERCHANT_LABELS[x])
                location_risk = st.slider("📍 Location Risk", 0., 1., 0.1, .01)
                device_trust  = st.slider("📱 Device Trust",  0., 1., 0.9, .01)
            with r1c3:
                past_fraud_ct = st.number_input("🔢 Past Frauds", 0, 20, 0)
                velocity_1h   = st.number_input("⚡ Txns / hour", 1, 50, 1)
                dist_home_km  = st.number_input("🗺️ Distance (km)", 0., 20000., 10.)
                card_age_days = st.number_input("📆 Card Age (days)", 0, 5000, 730)
                is_online     = st.toggle("🌐 Online Transaction", False)

            sb1, sb2 = st.columns(2, gap="medium")
            with sb1: submitted = st.form_submit_button("🔍 Analyze Transaction", use_container_width=True)
            with sb2: load_sus  = st.form_submit_button("🎲 Load Suspicious Sample", use_container_width=True)

        if load_sus:
            tx = random_transaction("manual")
            # Override to guaranteed high-risk suspicious values
            tx.update({
                "amount":        round(random.uniform(1200, 4500), 2),
                "location_risk": 0.85,
                "device_trust":  0.10,
                "velocity_1h":   12,
                "hour":          2,
                "is_online":     True,
                "past_fraud_ct": 2,
                "dist_home_km":  round(random.uniform(400, 3000), 1),
                "merchant_cat":  random.choice([3, 4, 5]),
                "source":        "manual",
                "transaction_id": f"SUS-{uuid.uuid4().hex[:8].upper()}",
            })
            progress_text = "🧠 Analyzing suspicious sample..."
            my_bar = st.progress(0, text=progress_text)
            for percent_complete in range(100):
                time.sleep(0.015)
                my_bar.progress(percent_complete + 1, text=progress_text)
            my_bar.empty()
            with st.spinner("Classifying risk score..."):
                result = predict_fn(tx)
                save_tx(result)
                st.session_state.last_result = result
                st.session_state.transactions.append(result)

        st.markdown('</div>', unsafe_allow_html=True)

        if submitted:
            progress_text = "🧠 AI analyzing transaction telemetry..."
            my_bar = st.progress(0, text=progress_text)
            for percent_complete in range(100):
                time.sleep(0.015)
                my_bar.progress(percent_complete + 1, text=progress_text)
            my_bar.empty()
            with st.spinner("Classifying risk score..."):
                tx=dict(amount=amount,hour=hour,day_of_week=day_of_week,merchant_cat=merchant_cat,
                        location_risk=location_risk,device_trust=device_trust,
                        past_fraud_ct=int(past_fraud_ct),velocity_1h=int(velocity_1h),
                        dist_home_km=dist_home_km,card_age_days=int(card_age_days),
                        is_online=is_online,source="manual",
                        transaction_id=f"MAN-{uuid.uuid4().hex[:8].upper()}")
                result=predict_fn(tx); save_tx(result)
                risk_pct = result.get('fraud_probability', 0.0) * 100
                risk_class = "risk-low" if risk_pct < 40 else "risk-med" if risk_pct < 75 else "risk-high"
                
                st.markdown(f'''
                <div style="font-size:1.2rem; font-weight:800; color:#FFFFFF; margin-top:20px;">
                    Neural Risk Assessment: <span style="color:{'#FF4D4D' if risk_pct>75 else '#00E676'}; text-shadow:0 0 15px currentColor">{risk_pct:.1f}%</span>
                </div>
                <div class="risk-meter-bg">
                    <div class="risk-meter-fill {risk_class}" style="width: {risk_pct}%;"></div>
                </div>
                ''', unsafe_allow_html=True)
                
                st.session_state.last_result=result

                st.session_state.transactions.append(result)

        if st.session_state.last_result:
            r=st.session_state.last_result
            prob=r["fraud_probability"]; lv=r["risk_level"]
            col=risk_color(lv); em=risk_emoji(lv); bcl=badge_cls(lv)

            # Result banner
            banner_cls = "alert-high" if lv=="High" else "alert-med" if lv=="Medium" else "alert-low"
            st.markdown(f"""
            <div class="alert-banner {banner_cls}" style="margin-top:20px;padding:18px 22px">
              <div style="font-size:2rem">{em}</div>
              <div>
                <div style="font-size:1.1rem;font-weight:800;color:{col}">{lv.upper()} RISK TRANSACTION</div>
                <div style="color:#64748b;font-size:.8rem;margin-top:3px">
                  <code style="color:#94a3b8">{r['transaction_id']}</code>
                  &nbsp;·&nbsp; Fraud probability: <strong style="color:{col}">{prob*100:.1f}%</strong>
                  &nbsp;·&nbsp; Anomaly score: {r['anomaly_score']*100:.1f}%
                </div>
              </div>
            </div>""", unsafe_allow_html=True)
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

            g1, g2, g3 = st.columns([1,1,1.6], gap="medium")

            with g1:
                st.markdown('<div class="card-title">🎯 Risk Gauge</div>', unsafe_allow_html=True)
                st.plotly_chart(make_gauge(prob,lv), use_container_width=True, config={"displayModeBar":False})
                st.markdown(f"<div style='text-align:center;margin-top:-8px'><span class='badge-{bcl}'>{em} {lv} Risk</span></div>", unsafe_allow_html=True)

            with g2:
                st.markdown('<div class="card-title">📊 Prediction Details</div>', unsafe_allow_html=True)
                glow_class = "glow-fraud" if r["is_fraud"] else "glow-safe"
                st.markdown(f'''<div style="display:flex; flex-direction:column; gap:16px;">
<div class="kpi-card" style="padding:15px; text-align:center; transform:none;">
<div class="kpi-title">Fraud Probability</div>
<div class="kpi-value glow-purple">{prob*100:.1f}%</div>
</div>
<div class="kpi-card" style="padding:15px; text-align:center; transform:none;">
<div class="kpi-title">Anomaly Score</div>
<div class="kpi-value glow-blue">{r['anomaly_score']*100:.1f}%</div>
</div>
<div class="kpi-card" style="padding:15px; text-align:center; transform:none;">
<div class="kpi-title">Is Fraud</div>
<div class="kpi-value {glow_class}">{"🚨 YES" if r["is_fraud"] else "✅ NO"}</div>
</div>
</div>''', unsafe_allow_html=True)

            with g3:
                st.markdown('<div class="card-title">🔍 SHAP Feature Attribution</div>', unsafe_allow_html=True)
                top=json.loads(r["top_features"])
                st.plotly_chart(make_shap_chart(top), use_container_width=True, config={"displayModeBar":False})
                st.markdown('<div style="font-size:.7rem;color:#475569;text-align:center">🔴 pushes toward fraud · 🟢 supports legitimacy</div>', unsafe_allow_html=True)

            # Recommendations
            recs=get_recs(lv,{k:r[k] for k in ["location_risk","device_trust","velocity_1h","dist_home_km","is_online"]})
            if recs["immediate_actions"] or recs["security_tips"]:
                st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)
                rc1,rc2=st.columns(2,gap="medium")
                with rc1:
                    if recs["immediate_actions"]:
                        st.markdown('<div class="card-title">🚨 Immediate Actions</div>', unsafe_allow_html=True)
                        for a in recs["immediate_actions"]:
                            st.markdown(f"<div style='padding:6px 0;border-bottom:1px solid #1e2d45;font-size:.82rem;color:#e2e8f0'>{a}</div>", unsafe_allow_html=True)
                with rc2:
                    if recs["security_tips"]:
                        st.markdown('<div class="card-title">🔒 Security Tips</div>', unsafe_allow_html=True)
                        for t in recs["security_tips"]:
                            st.markdown(f"<div style='padding:6px 0;border-bottom:1px solid #1e2d45;font-size:.82rem;color:#94a3b8'>💡 {t}</div>", unsafe_allow_html=True)
            if recs["watch_factors"]:
                st.markdown('<div class="card-title" style="margin-top:16px">👁️ Risk Signals</div>',unsafe_allow_html=True)
                cols_w=st.columns(min(len(recs["watch_factors"]),3),gap="medium")
                for i,wf in enumerate(recs["watch_factors"]):
                    with cols_w[i%3]:
                        st.markdown(f'<div class="alert-banner alert-med" style="padding:10px 14px"><span style="font-size:.82rem;color:#fbbf24">{wf}</span></div>', unsafe_allow_html=True)

    with tab_s:
        st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)
        st.markdown('<div class="card-title">⚡ Real-Time Transaction Stream Simulator</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:.82rem;color:#64748b;margin-bottom:20px">Simulate autonomous transaction ingestion and watch the fraud detection engine respond in real time.</div>', unsafe_allow_html=True)

        sc1,sc2,sc3=st.columns([1,1,1],gap="medium")
        with sc1: interval=st.slider("⏱️ Interval (s)",0.5,5.,1.5,.5)
        with sc2: n_stream=st.number_input("📦 Batch size",5,100,15)
        with sc3:
            st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
            go_stream=st.button("▶️ Start Stream",use_container_width=True)

        if go_stream:
            ph=st.empty(); pb=st.progress(0); fraud_ct=0; results=[]
            for i in range(int(n_stream)):
                tx=random_transaction("stream"); res=predict_fn(tx); save_tx(res); results.append(res)
                if res["is_fraud"]: fraud_ct+=1
                df_l=pd.DataFrame(results)[["transaction_id","amount","risk_level","fraud_probability","is_fraud","timestamp"]].copy()
                df_l["prob%"]=(df_l["fraud_probability"]*100).round(1).astype(str)+"%"
                df_l["amount"]=df_l["amount"].apply(lambda x:f"₹{x:,.2f}")
                with ph.container():
                    m1,m2,m3,m4=st.columns(4)
                    m1.metric("Processed",i+1)
                    m2.metric("Fraud",fraud_ct,delta=f"{fraud_ct/(i+1)*100:.0f}%",delta_color="inverse")
                    m3.metric("Last Risk",res["risk_level"])
                    m4.metric("Last Prob",f"{res['fraud_probability']*100:.1f}%")
                    st.dataframe(df_l[["transaction_id","amount","risk_level","prob%","timestamp"]].tail(8),
                                 use_container_width=True,hide_index=True,height=240)
                pb.progress((i+1)/int(n_stream))
                time.sleep(interval)
            st.success(f"✅ Done! Detected {fraud_ct}/{int(n_stream)} fraudulent transactions ({fraud_ct/int(n_stream)*100:.0f}%)")

# ════════════════════════════════════════════════════════════════════
# ANALYTICS
# ════════════════════════════════════════════════════════════════════
elif page == "📊 Analytics":
    st.markdown('''
    <style>
    /* Analytics Page Dedicated Background Controls */
    .stApp { --bg-orb-opacity: 0.03 !important; }
    </style>
    <div style="background:linear-gradient(135deg, rgba(8, 17, 31, 0.8), rgba(15, 23, 42, 0.95));
                backdrop-filter: blur(24px); border: 2px solid rgba(124, 77, 255, 0.4); border-radius: 20px;
                padding: 30px; margin-bottom: 30px; box-shadow: 0 15px 40px rgba(0,0,0,0.5), inset 0 0 30px rgba(79, 195, 247, 0.1);
                animation: fadeInSlideUp 0.8s backwards;">
      <div style="font-size:2rem; font-weight:900; color:#FFFFFF; text-shadow:0 0 20px rgba(79,195,247,0.8); margin-bottom:8px; display:flex; align-items:center; gap:12px;">
        🔮 Deep Neural Analytics
      </div>
      <div style="font-size:1.1rem; color:#E2E8F0; font-weight:600;">Identify complex fraud topologies, feature distributions, and geographic threat vectors.</div>
    </div>
    ''', unsafe_allow_html=True)
    
    history = get_history(1000)
    if not history:
        st.markdown('<div style="text-align:center;padding:100px;color:#FFFFFF;font-size:1.5rem;font-weight:700;text-shadow:0 0 15px currentColor;">📊 Connect Neural Network in Live Detection to begin streaming data...</div>', unsafe_allow_html=True)
    else:
        df = pd.DataFrame(history)
        
        # Calculate dynamic KPIs
        tot = len(df)
        fraud_df = df[df["is_fraud"] == 1]
        fraud_tot = len(fraud_df)
        f_rate = (fraud_tot / tot) * 100 if tot > 0 else 0
        avg_risk = df["fraud_probability"].mean() * 100
        
        # 1. KPI Bar precisely retained inside struct columns
        k1, k2, k3, k4 = st.columns(4)
        
        k_html = """
        <style>
        .an-kpi { transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); animation: anPop 0.8s backwards; }
        .an-kpi:hover { transform: scale(1.03); }
        .an-lab { font-size: 0.9rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; margin-bottom: 2px; }
        .an-val { font-size: 2.8rem; font-weight: 900; line-height: 1; transition: text-shadow 0.3s ease; }
        @keyframes anPop {
            0% { opacity: 0; transform: translateY(15px); filter: blur(5px); }
            100% { opacity: 1; transform: translateY(0); filter: blur(0); }
        }
        </style>
        """
        st.markdown(k_html, unsafe_allow_html=True)

        k1.markdown(f'''<div class="an-kpi" style="animation-delay:0.1s;"><div class="an-lab">Total Transactions</div><div class="an-val" style="color:#4FC3F7; text-shadow:0 0 12px rgba(79,195,247,0.4);">{tot:,}</div></div>''', unsafe_allow_html=True)
        k2.markdown(f'''<div class="an-kpi" style="animation-delay:0.15s;"><div class="an-lab">Neural Flags</div><div class="an-val" style="color:#FF4D4D; text-shadow:0 0 12px rgba(255,77,77,0.4);">{fraud_tot:,}</div></div>''', unsafe_allow_html=True)
        k3.markdown(f'''<div class="an-kpi" style="animation-delay:0.2s;"><div class="an-lab">Threat Rate</div><div class="an-val" style="background:linear-gradient(135deg, #FF6B6B, #FF3D00); -webkit-background-clip:text; -webkit-text-fill-color:transparent; text-shadow:0 0 12px rgba(255,61,0,0.5);">{f_rate:.2f}%</div></div>''', unsafe_allow_html=True)
        k4.markdown(f'''<div class="an-kpi" style="animation-delay:0.25s;"><div class="an-lab">Average Risk Factor</div><div class="an-val" style="color:#7C4DFF; text-shadow:0 0 12px rgba(124,77,255,0.4);">{avg_risk:.1f}%</div></div>''', unsafe_allow_html=True)

        
        # Standard Chart Tweaker (removes UI noise)
        def _chart_layout(fig, h=320):
            fig.update_layout(transition_duration=1000, height=h, margin=dict(t=20, b=20, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#FFFFFF", size=13)),
                xaxis=dict(color="#FFFFFF", gridcolor="rgba(255,255,255,0.1)", showgrid=True, title_font=dict(size=14, color="#4FC3F7")),
                yaxis=dict(color="#FFFFFF", gridcolor="rgba(255,255,255,0.1)", title_font=dict(size=14, color="#4FC3F7")),
                font=dict(family="Inter", color="#FFFFFF"), hoverlabel=dict(bgcolor="rgba(15,23,42,0.95)", font_size=16, font_family="Inter"))
            return fig

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        
        # Row 1
        a1, a2 = st.columns(2, gap="large")
        with a1:
            st.markdown('<div class="premium-chart-container"><div class="chart-header-title">💸 Transaction Volume Hierarchy</div>', unsafe_allow_html=True)
            fig1 = px.box(df, x="risk_level", y="amount", color="risk_level", points="all",
                          color_discrete_map={"Low": "#00E676", "Medium": "#FFEA00", "High": "#FF4D4D"})
            fig1.update_traces(marker=dict(size=4, opacity=0.8), line=dict(width=2))
            st.plotly_chart(_chart_layout(fig1), use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)
            
        with a2:
            st.markdown('<div class="premium-chart-container"><div class="chart-header-title">⏳ Threat Density by Hour</div>', unsafe_allow_html=True)
            if "hour" in df.columns:
                fbh = df.groupby("hour")["is_fraud"].sum().reset_index()
                fig2 = go.Figure(go.Bar(x=fbh["hour"], y=fbh["is_fraud"], marker_color="#FF4D4D",
                                        marker=dict(line=dict(color='rgba(255, 77, 77, 1.0)', width=2)),
                                        opacity=0.9))
                st.plotly_chart(_chart_layout(fig2), use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

        # Row 2
        a3, a4 = st.columns(2, gap="large")
        with a3:
            st.markdown('<div class="premium-chart-container"><div class="chart-header-title">📍 Spatial Geolocation Risk Mapping</div>', unsafe_allow_html=True)
            fig3 = px.scatter(df.sample(min(400, len(df))), x="location_risk", y="fraud_probability", size="amount",
                              color="risk_level", opacity=0.85,
                              color_discrete_map={"Low": "#00E676", "Medium": "#4FC3F7", "High": "#FF4D4D"})
            fig3.update_traces(marker=dict(line=dict(width=1, color='rgba(255,255,255,0.4)')), selector=dict(mode='markers'))
            st.plotly_chart(_chart_layout(fig3), use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)
            
        with a4:
            st.markdown('<div class="premium-chart-container"><div class="chart-header-title">🎯 Threat Origin by Sector</div>', unsafe_allow_html=True)
            if "merchant_cat" in df.columns:
                mc = df.groupby("merchant_cat").agg(fraud=("is_fraud", "sum")).reset_index()
                mc = mc[mc["fraud"] > 0]
                if not mc.empty:
                    # User requested Pie Chart for radial fill!
                    fig4 = px.pie(mc, values='fraud', names='merchant_cat', hole=0.5,
                                  color_discrete_sequence=["#FF4D4D", "#7C4DFF", "#4FC3F7", "#00E676", "#FFEA00"])
                    fig4.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#0A0F1C', width=3)))
                    fig4.update_layout(transition_duration=1000, height=320, margin=dict(t=10, b=10, l=10, r=10),
                                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                       font=dict(family="Inter", color="#FFFFFF", size=14))
                    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.markdown("<div style='color:#00E676; font-weight:800; text-align:center; padding:50px;'>No fraud sectors detected yet!</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # SHAP block integration
        imp_path = Path(__file__).parent.parent / "models" / "feature_importance.json"
        if imp_path.exists():
            st.markdown('<div class="premium-chart-container"><div class="chart-header-title">🧠 AI Engine Global Feature Importance (SHAP)</div>', unsafe_allow_html=True)
            with open(imp_path) as f: imp = json.load(f)
            imp_df = pd.DataFrame(list(imp.items()), columns=["Feature", "Importance"]).sort_values("Importance")
            fig5 = go.Figure(go.Bar(x=imp_df["Importance"], y=imp_df["Feature"], orientation="h",
                marker=dict(color=imp_df["Importance"], colorscale=[[0, "#4FC3F7"], [0.5, "#7C4DFF"], [1, "#FF4D4D"]],
                            line=dict(width=1, color="rgba(255,255,255,0.4)"))))
            fig5 = _chart_layout(fig5, 360)
            fig5.update_layout(yaxis=dict(color="#FFFFFF", showgrid=False), xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"))
            st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# CYBER AWARENESS
# ════════════════════════════════════════════════════════════════════
elif page == "🔐 Cyber Awareness":
    st.markdown('''
    <style>
    /* Animated Simulator Background */
    .stApp {
        background: linear-gradient(-45deg, #0A0F1C, #130a38, #051629, #170d2b) !important;
        background-size: 400% 400% !important;
        animation: cyberShift 12s ease infinite !important;
    }
    /* Hide top padding for complete immersion */
    .block-container { max-width: 1100px; padding-top: 2rem !important; }
    </style>
    ''', unsafe_allow_html=True)
    
    # Simulator State Initialization
    if "sim_score" not in st.session_state: st.session_state.sim_score = 0
    if "sim_attempts" not in st.session_state: st.session_state.sim_attempts = 0
    if "sim_scenarios" not in st.session_state:
        import random
        base_phish = get_phishing()
        # Add a couple "safe" examples manually to make the quiz fair!
        safe_ex = [
            {"type": "Safe Bank Notification", "message": "Dear customer, your statement for A/C **4589 is ready on your official netbanking portal. We will never ask for your PIN.", "fraud": False, "exp": "Directs you to use your own bookmark/app, explicitly mentions they won't ask for PIN."},
            {"type": "Safe Payment Alert", "message": "Transaction alert: ₹149 debited from your card ending 1234. If unrecognized, lock card via banking app.", "fraud": False, "exp": "Informational only, no links, standard protocol."}
        ]
        # Map original as fraud
        for p in base_phish: 
            p["fraud"] = True
            p["exp"] = "This relies on urgency, unverified links, and coercion. Flags: " + ", ".join(p["red_flags"])
            
        pool = base_phish + safe_ex
        random.shuffle(pool)
        st.session_state.sim_scenarios = pool
        st.session_state.current_index = 0
        st.session_state.quiz_result = None

    # Header Panel
    perc = int((st.session_state.sim_score / max(1, st.session_state.sim_attempts)) * 100)
    g_color = "#10b981" if perc >= 70 else "#f59e0b" if perc >= 40 else "#ef4444"
    st.markdown(f'''
    <div style="background:rgba(15, 23, 42, 0.85); backdrop-filter:blur(24px); border:1px solid rgba(124, 77, 255, 0.3); border-radius:18px; padding:25px; margin-bottom:25px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 10px 30px rgba(0,0,0,0.5);">
        <div>
            <div style="font-size:1.8rem; font-weight:900; color:#FFFFFF; text-shadow:0 0 15px rgba(124,77,255,0.6); display:flex; align-items:center; gap:10px;">
                🔐 Cyber Simulator Engine
            </div>
            <div style="color:#94a3b8; font-size:1rem; margin-top:4px;">Train your neural pathways against modern synthetic attacks.</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:0.8rem; color:#64748b; text-transform:uppercase; letter-spacing:1px; font-weight:700;">Awareness Rating</div>
            <div style="font-size:2.2rem; font-weight:900; color:{g_color}; text-shadow:0 0 20px {g_color}80;">{perc}%</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["🎮 Scam Simulator", "🎣 Phishing Arsenal", "🔎 Deep Analyzer"])

    # ════════════════════════════════════════════
    # TAB 1: THE SIMULATOR (QUIZ LOGIC)
    # ════════════════════════════════════════════
    with t1:
        if st.session_state.current_index >= len(st.session_state.sim_scenarios):
            st.markdown('<div class="result-correct">🎉 Simulation Complete! You survived the gauntlet. Reset to play again.</div>', unsafe_allow_html=True)
            if st.button("🔄 Restart Simulator"):
                st.session_state.sim_attempts = 0
                st.session_state.sim_score = 0
                st.session_state.current_index = 0
                st.session_state.quiz_result = None
                st.rerun()
        else:
            scenario = st.session_state.sim_scenarios[st.session_state.current_index]
            
            st.markdown('<div class="chart-header-title">Incoming Communication Intercepted...</div>', unsafe_allow_html=True)
            st.markdown(f'''
            <div style="background:rgba(0,0,0,0.4); border:1px solid #334155; border-radius:12px; padding:20px 25px; margin:15px 0 30px 0;">
                <div style="font-size:0.8rem; color:#94a3b8; margin-bottom:10px; text-transform:uppercase; font-weight:700;">{scenario["type"]}</div>
                <div style="font-size:1.4rem; color:#FFFFFF; line-height:1.5; font-weight:500;">"{scenario["message"]}"</div>
            </div>
            ''', unsafe_allow_html=True)

            # Interactive Result Frame
            if st.session_state.quiz_result is not None:
                res = st.session_state.quiz_result
                if res == "correct":
                    st.markdown('<div class="result-correct">✅ DIRECT HIT! Threat neutralize.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="result-wrong">❌ COMPROMISED! You fell for it.</div>', unsafe_allow_html=True)
                
                st.markdown(f'<div style="background:rgba(15,23,42,0.8); border-left:4px solid #4FC3F7; padding:15px 20px; color:#E2E8F0; border-radius:8px; margin-bottom:20px;"><b>Debrief:</b> {scenario["exp"]}</div>', unsafe_allow_html=True)
                
                if st.button("⏭️ Next Scenario", type="primary"):
                    st.session_state.current_index += 1
                    st.session_state.quiz_result = None
                    st.rerun()
            else:
                st.markdown('<div style="text-align:center; font-size:1.2rem; color:#E2E8F0; margin-bottom:20px; font-weight:700;">Is this a fraudulent attack?</div>', unsafe_allow_html=True)
                btn_cols = st.columns([1,1,1,1]) # Keep centered
                
                with btn_cols[1]:
                    st.html('<style>div.stButton > button.yes-btn { width: 100%; border:2px solid #ef4444; color:#ef4444; background:transparent; font-weight:800; font-size:1.2rem; } div.stButton > button.yes-btn:hover { background:#ef4444; color:white; }</style>')
                    if st.button("🚨 YES, FRAUD", key="btn_yes", use_container_width=True):
                        st.session_state.sim_attempts += 1
                        if scenario["fraud"] == True:
                            st.session_state.sim_score += 1
                            st.session_state.quiz_result = "correct"
                        else:
                            st.session_state.quiz_result = "wrong"
                        st.rerun()
                
                with btn_cols[2]:
                    st.html('<style>div.stButton > button.no-btn { width: 100%; border:2px solid #10b981; color:#10b981; background:transparent; font-weight:800; font-size:1.2rem; } div.stButton > button.no-btn:hover { background:#10b981; color:white; }</style>')
                    if st.button("✅ NO, SAFE", key="btn_no", use_container_width=True):
                        st.session_state.sim_attempts += 1
                        if scenario["fraud"] == False:
                            st.session_state.sim_score += 1
                            st.session_state.quiz_result = "correct"
                        else:
                            st.session_state.quiz_result = "wrong"
                        st.rerun()

    # ════════════════════════════════════════════
    # TAB 2: HTML ACCORDION ARSENAL
    # ════════════════════════════════════════════
    with t2:
        st.markdown('<div class="chart-header-title" style="margin-bottom:20px;">🎣 Attack Vector Library</div>', unsafe_allow_html=True)
        for ex in get_phishing():
            flags_html = "".join([f"<li style='color:#ef4444; margin-left:15px; margin-bottom:5px;'>{f}</li>" for f in ex["red_flags"]])
            st.markdown(f'''
            <details class="cyber-accordion">
                <summary><span style="display:flex; align-items:center; gap:10px;"><span style="color:{ex["color"]}; font-size:1.4rem;">⚠️</span> {ex["type"]}</span></summary>
                <div class="accordion-content">
                    <div style="background:rgba(0,0,0,0.3); border:1px solid #334155; padding:15px; border-radius:8px; font-family:monospace; color:#E2E8F0; margin-bottom:15px; font-size:0.9rem;">{ex["message"]}</div>
                    <div style="color:#FFFFFF; font-weight:700; margin-bottom:10px;">🚩 Red Flag Detectors:</div>
                    <ul style="padding-left:10px;">{flags_html}</ul>
                </div>
            </details>
            ''', unsafe_allow_html=True)

    # ════════════════════════════════════════════
    # TAB 3: HIGHLIGHT ANALYZER
    # ════════════════════════════════════════════
    with t3:
        st.markdown('<div class="chart-header-title">🔎 Forensic Analyzer Module</div>', unsafe_allow_html=True)
        # We use st.radio for the toggle, styled horizontally
        mode = st.radio("Select Document Mode:", ["🚨 Analyze Malicious Frame", "✅ Analyze Secure Frame"], horizontal=True)
        
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        
        if "Malicious" in mode:
            # Highlight red flags
            msg = "Dear Customer, your account accesses have been restricted due to suspicious logins. Please click <mark class='red-flag'>here immediately</mark> to verify your identity. Failure to do so will result in <mark class='red-flag'>permanent suspension</mark>."
            st.markdown(f'''
            <div style="background:linear-gradient(135deg,rgba(239,68,68,0.1),rgba(15,23,42,0.8)); border:1px solid rgba(239,68,68,0.5); border-left:4px solid #ef4444; border-radius:12px; padding:25px; box-shadow:0 10px 30px rgba(0,0,0,0.5);">
                <div style="font-size:1.1rem; line-height:1.8; color:#E2E8F0;">{msg}</div>
                <div style="margin-top:20px; font-size:0.9rem; color:#94a3b8; border-top:1px solid #334155; padding-top:15px;">
                    <b>Diagnostic:</b> AI detected forced urgency ("immediately") and punitive threats ("permanent suspension"). Links are obfuscated behind bare inline text rather than exposing the raw destination.
                </div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            msg = "Hello John, <mark class='green-flag'>Log in to your banking app</mark> to review your statement. We will <mark class='green-flag'>never</mark> ask for your password or OTP over email."
            st.markdown(f'''
            <div style="background:linear-gradient(135deg,rgba(16,185,129,0.1),rgba(15,23,42,0.8)); border:1px solid rgba(16,185,129,0.5); border-left:4px solid #10b981; border-radius:12px; padding:25px; box-shadow:0 10px 30px rgba(0,0,0,0.5);">
                <div style="font-size:1.1rem; line-height:1.8; color:#E2E8F0;">{msg}</div>
                <div style="margin-top:20px; font-size:0.9rem; color:#94a3b8; border-top:1px solid #334155; padding-top:15px;">
                    <b>Diagnostic:</b> Secure communication protocol detected. Vendor uses personal salutation, directs the user to leverage existing trusted architecture (the App), and reinforces security guardrails (denying OTP requests).
                </div>
            </div>
            ''', unsafe_allow_html=True)

# ── Global UI Components ────────────────────────────────────────────
render_chatbot()
