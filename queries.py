import streamlit as st

def handle_query_params():
    if not st.query_params:
        return False

    for name, value in st.query_params.items():
        st.session_state[name] = value

    st.query_params.clear()  # Clear query params after syncing to session state
    st.rerun()
    return True