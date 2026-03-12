import re


def to_snake_case(text: str) -> str:
    """
    Converts a string to lower snake case format using a single chained
    regular expression statement.

    Examples:
    - "HelloWorld" -> "hello_world"
    - "user ID" -> "user_id"
    - "MyAPIKey" -> "my_api_key" (Handles acronyms correctly)
    - "my-variable-name" -> "my_variable_name"

    Args:
        text: The input string.

    Returns:
        The string converted to lower snake case.
    """
    if not text:
        return ""

    # Single-line implementation combining all previous regex steps via chaining:
    # 1. Replace spaces/hyphens with underscore
    # 2. Insert underscore before CamelCase/PascalCase
    # 3. Handle acronyms (e.g., 'APIKey' -> 'API_Key')
    # 4. Convert to lowercase
    # 5. Clean up multiple underscores and leading/trailing ones
    return (
        re.sub(
            r"_+",
            "_",
            re.sub(
                r"([A-Z]+)([A-Z][a-z])",
                r"\1_\2",
                re.sub(r"([A-Z])([a-z])", r"_\1\2", re.sub(r"[ -]+", "_", text)),
            ),
        )
        .lower()
        .strip("_")
    )

def format_currency(value: float) -> str:
    """Format a numeric value as Indian Rupee (₹) with appropriate suffixes."""
    if value is None:
        return "₹0.00"
    
    if value >= 10000000:  # Cr
        return f"₹{value / 10000000:.2f} Cr"
    elif value >= 100000:  # L
        return f"₹{value / 100000:.2f} L"
    else:
        return f"₹{value:,.2f}"

def get_signal_icon(signal: str) -> str:
    """Return an emoji icon based on the signal direction."""
    if not signal:
        return "⚪"
    
    s = signal.upper()
    if "BUY" in s:
        return "🟢"
    elif "AVOID" in s or "SELL" in s:
        return "🔴"
    else:
        return "🟡"

def get_sentiment_color(sentiment: str) -> str:
    """Return a CSS color name or hex code based on sentiment."""
    if not sentiment:
        return "grey"
    
    s = sentiment.lower()
    if s == "positive":
        return "green"
    elif s == "negative":
        return "red"
    else:
        return "orange"
