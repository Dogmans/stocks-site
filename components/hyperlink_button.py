import streamlit as st
import uuid

def hyperlink_button(label, key, help=None):
    """
    Renders a Streamlit button styled as a hyperlink (only this button).
    Returns True if clicked, else False.
    """
    # Generate a unique HTML id for this button
    html_id = f"hyperlink-btn-{uuid.uuid4().hex}"
    # Render the button as HTML and use st.markdown for the style
    button_html = f"""
    <style>
    #{html_id} {{
        background: none !important;
        color: #1a73e8;
        border: none;
        padding: 0;
        font-size: 1em;
        text-decoration: underline;
        cursor: pointer;
    }}
    </style>
    <button id="{html_id}" type="submit">{label}</button>
    """
    # Use a form to capture the click event
    form_key = f"form_{key}"
    with st.form(form_key):
        st.markdown(button_html, unsafe_allow_html=True)
        submitted = st.form_submit_button(label=" ", help=help)
    return submitted
