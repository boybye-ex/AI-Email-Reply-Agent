from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import streamlit as st
from src.workflow import create_workflow
from src.config import GROQ_API_KEY, TAVILY_API_KEY
import json

MISSING_API_KEYS_MESSAGE = (
    "Missing API keys. Copy .env.example to .env and add your Groq and Tavily keys."
)

def initialize_session_state():
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'current_email' not in st.session_state:
        st.session_state.current_email = None
    if 'current_response' not in st.session_state:
        st.session_state.current_response = None
    if 'current_triage' not in st.session_state:
        st.session_state.current_triage = None
    if 'response_counter' not in st.session_state:
        st.session_state.response_counter = 0

def display_header():
    st.title("✉️ Email Response Generator")

def display_input_section():
    with st.container():
        st.markdown('<p class="section-title">📝 Input Email</p>', unsafe_allow_html=True)
        email_content = st.text_area(
            label="",
            placeholder="""Hi, Bhavik!

It's Day 2 of your automation adventure with Apify, and it's time to connect the dots! 
Integrating your Actors with other solutions you use opens up a world of possibilities, 
making your workflows smarter and your life easier.

Have fun!

The Bhavik Team""",
            height=400,
            key="email_input"
        )
        
        generate_button = st.button(
            "🚀 Generate Response",
            key="generate_button",
            use_container_width=True,
            type="primary"
        )
        
        if st.session_state.history:
            with st.expander("📚 Previous Emails", expanded=False):
                for idx, item in enumerate(st.session_state.history):
                    st.text_area(
                        f"Email {idx + 1}",
                        item["email"],
                        height=400,
                        key=f"history_email_{idx}"
                    )
                    st.markdown("---")
        
        return email_content, generate_button

def extract_triage_metadata(output: dict) -> dict:
    """Extract triage metadata from workflow output."""
    return {
        "email_category": output.get("email_category", "unknown"),
        "urgency_level": output.get("urgency_level", "low"),
        "needs_human_escalation": output.get("needs_human_escalation", False),
        "escalation_reasoning": output.get("escalation_reasoning", ""),
    }
    
def extract_email_draft(response_text: str) -> str:
    """Extract email draft from the response text."""
    try:
        # Try parsing as JSON first
        if isinstance(response_text, str):
            try:
                json_response = json.loads(response_text)
                if isinstance(json_response, dict) and 'email_draft' in json_response:
                    return json_response['email_draft']
            except json.JSONDecodeError:
                pass

        # If JSON parsing fails, try extracting using string manipulation
        if '"email_draft":' in response_text:
            # Find the start of the email draft
            start_idx = response_text.find('"email_draft":') + len('"email_draft":')
            # Find the content between quotes
            content_start = response_text.find('"', start_idx) + 1
            content_end = response_text.rfind('"')
            if content_start < content_end:
                return response_text[content_start:content_end]

        # If all extraction methods fail, return the original text
        return response_text
    except Exception as e:
        print(f"Error extracting email draft: {e}")
        return response_text

def process_email(email_content):
    try:
        with st.spinner("🔄 Processing your email..."):
            app = create_workflow()
            inputs = {
                "initial_email": email_content,
                "research_info": None,
                "num_steps": 0
            }
            output = app.invoke(inputs)
            response = output.get('draft_email', 'Unable to process email')
            triage = extract_triage_metadata(output)
            
            clean_response = extract_email_draft(response)
            return clean_response, triage, None
    except ValueError as e:
        if "GROQ_API_KEY" in str(e):
            return None, None, MISSING_API_KEYS_MESSAGE
        return None, None, str(e)
    except Exception as e:
        return None, None, str(e)

def display_triage_banner(triage: dict):
    """Display urgency and escalation status from triage metadata."""
    if not triage:
        return

    if triage.get("needs_human_escalation"):
        st.warning(
            "Human review required — escalated to senior support. "
            "A draft has been generated, but please review before sending."
        )
    else:
        st.success(
            f"Category: **{triage.get('email_category', 'unknown')}** | "
            f"Urgency: **{triage.get('urgency_level', 'low')}**"
        )

    with st.expander("Triage Details", expanded=triage.get("needs_human_escalation", False)):
        st.markdown(f"**Category:** {triage.get('email_category', 'unknown')}")
        st.markdown(f"**Urgency Level:** {triage.get('urgency_level', 'low')}")
        st.markdown(
            f"**Needs Human Escalation:** "
            f"{'Yes' if triage.get('needs_human_escalation') else 'No'}"
        )
        reasoning = triage.get("escalation_reasoning", "")
        if reasoning:
            st.markdown(f"**Reasoning:** {reasoning}")

def display_response_section(response, triage=None, is_new=False):
    if is_new:
        st.session_state.response_counter += 1
    
    response_id = st.session_state.response_counter
    
    if response:
        st.markdown('<p class="section-title">📨 Generated Response</p>', unsafe_allow_html=True)
        display_triage_banner(triage)
        tabs = st.tabs(["✏️ Editor", "👀 Preview", "💾 Drafts"])
        
        with tabs[0]:
            edited_response = st.text_area(
                label="",
                value=response,
                height=400,
                key=f"response_editor_{response_id}"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Copy to Clipboard", 
                            key=f"copy_{response_id}",
                            use_container_width=True):
                    st.toast("Response copied to clipboard! 📋")
            with col2:
                if st.button("💾 Save Draft", 
                            key=f"save_{response_id}",
                            use_container_width=True):
                    st.session_state.history.append({
                        "email": st.session_state.current_email,
                        "response": edited_response,
                        "triage": triage or {},
                    })
                    st.toast("Draft saved! 💾")
        
        with tabs[1]:
            st.markdown(f"""<div style="background-color: #2D2D2D; padding: 20px; border-radius: 8px; border: 1px solid #404040;">
                <pre style="color: #FFFFFF; margin: 0;">{response}</pre>
            </div>""", unsafe_allow_html=True)
        
        with tabs[2]:
            if st.session_state.history:
                for idx, item in enumerate(reversed(st.session_state.history)):
                    with st.expander(f"Draft {len(st.session_state.history) - idx}", expanded=False):
                        item_triage = item.get("triage", {})
                        if item_triage:
                            st.caption(
                                f"Category: {item_triage.get('email_category', 'unknown')} | "
                                f"Urgency: {item_triage.get('urgency_level', 'low')} | "
                                f"Escalated: {'Yes' if item_triage.get('needs_human_escalation') else 'No'}"
                            )
                        st.text_area(
                            "Response",
                            item["response"],
                            height=200,
                            key=f"draft_response_{response_id}_{idx}"
                        )
            else:
                st.info("No saved drafts yet!")

def main():
    st.set_page_config(
        page_title="AI ER Agent",
        page_icon="✉️",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get help': None,
            'Report a bug': None,
            'About': None
        }
    )
    
    initialize_session_state()

    if not GROQ_API_KEY or not TAVILY_API_KEY:
        st.error(MISSING_API_KEYS_MESSAGE)
        st.stop()

    display_header()
    
    col1, col2 = st.columns([4, 5])
    
    with col1:
        st.markdown('<div class="content-box">', unsafe_allow_html=True)
        email_content, generate_clicked = display_input_section()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="content-box">', unsafe_allow_html=True)
        if generate_clicked and email_content:
            st.session_state.current_email = email_content
            response, triage, error = process_email(email_content)
            
            if error:
                st.error(f"❌ An error occurred: {error}")
            else:
                st.session_state.current_response = response
                st.session_state.current_triage = triage
                display_response_section(response, triage=triage, is_new=True)
        
        elif st.session_state.current_response:
            display_response_section(
                st.session_state.current_response,
                triage=st.session_state.current_triage,
            )
        
        else:
            st.info("Generate a response to see it here!")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
