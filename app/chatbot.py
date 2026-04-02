import streamlit as st
import time

def generate_ai_response(prompt, tx_context=None):
    """Rule-based AI response generator."""
    prompt = prompt.lower()
    
    # 1. Provide context-driven response if a transaction just happened
    if tx_context and any(kw in prompt for kw in ['why', 'explain', 'flagged', 'risk', 'transaction']):
        prob = tx_context.get('fraud_probability', 0)
        risk = tx_context.get('risk_level', 'Low')
        amt = tx_context.get('amount', 0)
        
        if risk == 'High':
            return (f"The transaction of ₹{amt:,.2f} was flagged as **{risk} Risk** ({prob*100:.1f}% probability). "
                    "This is typically due to anomalous factors such as high velocity, mismatch in location, "
                    "or an unusual merchant category for your profile. I recommend verifying the origin immediately.")
        else:
            return (f"The transaction of ₹{amt:,.2f} looks normal. It scored a {prob*100:.1f}% fraud probability "
                    f"and is currently classified as **{risk} Risk**.")
                    
    # 2. General Queries
    if "how does fraud detection work" in prompt:
        return ("AURA uses an ensemble of Machine Learning models. Primarily, an XGBoost Classifier analyzes patterns "
                "in transaction metadata (time, location, device metrics) while an Isolation Forest provides unsupervised "
                "anomaly scoring to detect completely novel threats.")
    elif "fraud trends" in prompt or "recent trends" in prompt:
        return ("Recently, we've seen a 34% uptick in 'Velocity' based attacks late at night (12 AM - 3 AM). "
                "Attackers are testing stolen credentials in small, rapid increments on online merchants.")
    elif "what should i do" in prompt or "help" in prompt:
        return ("If you suspect fraud:\n1. Freeze your card instantly (via banking app)\n"
                "2. Report the specific transaction ID inside the Live Alerts table.\n"
                "3. Enable 2FA on your core accounts.")
                
    # 3. Fallback
    return ("I am AURA's AI Assistant. I can explain recent transaction flags, detail our machine learning architecture, "
            "or provide general cybersecurity advice. How can I assist you today?")

def render_chatbot():
    """Renders the floating chatbot UI."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am AURA. I can analyze recent transactions, explain risk scores, and help with fraud prevention."}
        ]
        
    # We use a globally hijacked st.expander to act as our floating chatbot module.
    # Expanders natively preserve their open/close state across component reruns,
    # completely solving the st.popover instant collapse bug.
    with st.expander("💠 AURA AI Chatbot", expanded=False):
        
        # Display chat messages
        chat_container = st.container(height=320)
        with chat_container:
            for message in st.session_state.messages:
                cls = "chat-user" if message["role"] == "user" else "chat-bot"
                st.markdown(f'<div class="chat-bubble {cls}">{message["content"]}</div>', unsafe_allow_html=True)
        
        # Quick actions
        cols = st.columns(3)
        with cols[0]:
            if st.button("Explain Risk", key="btn_explain", use_container_width=True):
                st.session_state.kb_prompt = "Why was this transaction flagged?"
        with cols[1]:
            if st.button("Fraud Tips", key="btn_tips", use_container_width=True):
                st.session_state.kb_prompt = "What should I do if fraud is detected?"
        with cols[2]:
            if st.button("System", key="btn_sys", use_container_width=True):
                st.session_state.kb_prompt = "How does fraud detection work?"
                
        # Main input handling
        user_input = st.chat_input("Ask AURA...")
        
        # Override with quick button press
        if "kb_prompt" in st.session_state:
            user_input = st.session_state.kb_prompt
            del st.session_state.kb_prompt
            
        if user_input:
            # 1. Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.rerun() # Refresh to show user bubble immediately
            
        # 2. Add AI response logic if last message was from user
        if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
            with chat_container:
                st.markdown('<div class="chat-bubble chat-bot"><span class="typing-indicator">AURA is thinking</span></div>', unsafe_allow_html=True)
                time.sleep(1) # Simulated delay
                ctx = st.session_state.get("last_result", None)
                reply = generate_ai_response(st.session_state.messages[-1]["content"], tx_context=ctx)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun() # Refresh to show AI bubble
