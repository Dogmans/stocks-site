import streamlit as st

def hyperlink_button(label, symbol, page="Stock/ETF Detail"):
    """
    Renders a true hyperlink that, when clicked, sets session state for navigation.
    Returns True if this link was just clicked (i.e., query param matches), else False.
    """
    import urllib.parse
    # Encode the symbol and page for the URL
    url = f"?detail_symbol={urllib.parse.quote(symbol)}&page={urllib.parse.quote(page)}"
    st.markdown(f'<a href="{url}" style="color:#1a73e8;text-decoration:underline;">{label}</a>', unsafe_allow_html=True)
    if (
        st.query_params.get("detail_symbol", [None]) == symbol and
        st.query_params.get("page", [None]) == page
    ):
        st.session_state["detail_symbol"] = symbol
        st.session_state["page"] = page
        st.query_params.clear()  # Clear query params to prevent repeated triggers
        st.rerun()
        return True
    return False
