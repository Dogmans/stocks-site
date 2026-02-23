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
    # Check if the query params match this symbol and page
    query_params = st.query_params
    if (
        query_params.get("detail_symbol", [None]) == symbol and
        query_params.get("page", [None]) == page
    ):
        st.session_state["detail_symbol"] = symbol
        st.session_state["page"] = page
        query_params.clear()  # Clear query params to prevent repeated triggers
        st.rerun()
        return True
    return False
