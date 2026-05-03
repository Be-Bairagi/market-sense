import streamlit as st
from contextlib import contextmanager

@contextmanager
def render_loader(message: str = "Processing..."):
    """
    Centralized loader component for MarketSense.
    Standardizes the loading experience across the application.
    
    Args:
        message (str): The message to display while loading.
    """
    # Ensure the message ends with an ellipsis for consistent styling
    if not message.endswith("..."):
        message += "..."
        
    with st.spinner(f"⏳ {message}"):
        yield
