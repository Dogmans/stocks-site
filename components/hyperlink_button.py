import streamlit as st

# Only inject style once per page
if not hasattr(st.session_state, "_hyperlink_button_style_injected"):
    st.markdown("""
        <style>
        div[data-testid="stButton"] button.hyperlink-btn {
            background: none !important;
            color: #1a73e8;
            border: none;
            padding: 0;
            font-size: 1em;
            text-decoration: underline;
            cursor: pointer;
        }
        </style>
    """, unsafe_allow_html=True)
    st.session_state._hyperlink_button_style_injected = True

def hyperlink_button(label, key, help=None):
    """
    Renders a Streamlit button styled as a hyperlink.
    Returns True if clicked, else False.
    """
    return st.button(label, key=key, help=help)
