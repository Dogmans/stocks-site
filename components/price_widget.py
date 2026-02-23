import streamlit as st

# Reusable price widget for consistent formatting (arrow, color, etc.)
def price_widget(price, change_pct, size='default'):
    """
    Display price with up/down arrow, color, and consistent sizing.
    Args:
        price (float or str): Current price.
        change_pct (float or str): Change percentage.
        size (str): 'default' or 'small' for sizing.
    """
    try:
        price = float(price)
    except (ValueError, TypeError):
        price = price
    try:
        change = float(change_pct)
    except (ValueError, TypeError):
        change = 0
    arrow = '▲' if change > 0 else ('▼' if change < 0 else '')
    color = 'green' if change > 0 else ('red' if change < 0 else 'gray')
    price_str = f"{price:.2f}" if isinstance(price, float) else str(price)
    if arrow:
        change_str = f"{arrow}&nbsp;{change:.2f}%"
    else:
        change_str = f"{change:.2f}%"
    style = f"color:{color}; font-size:{'1.2em' if size=='default' else '1em'}; font-weight:bold;"
    st.markdown(f"<span>Price: {price_str} <span style='color:{color}'>{change_str}</span></span>", unsafe_allow_html=True)
