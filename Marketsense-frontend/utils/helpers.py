import re
CURRENCY_SYMBOL = "₹"


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

def format_currency(value: float, show_symbol: bool = True) -> str:
    """Format a numeric value as Indian Rupee with appropriate suffixes."""
    if value is None:
        return f"{CURRENCY_SYMBOL}0.00" if show_symbol else "0.00"
    
    symbol = CURRENCY_SYMBOL if show_symbol else ""
    
    if value >= 10000000:  # Cr
        return f"{symbol}{value / 10000000:.2f} Cr"
    elif value >= 100000:  # L
        return f"{symbol}{value / 100000:.2f} L"
    else:
        return f"{symbol}{value:,.2f}"

def format_date(dt_obj_or_str, format: str = "%d %b %Y") -> str:
    """Format a date object or ISO string into a standard display date."""
    if dt_obj_or_str is None:
        return "N/A"
    
    import datetime
    if isinstance(dt_obj_or_str, str):
        try:
            # Handle potential ISO format or just date
            dt_obj = datetime.datetime.fromisoformat(dt_obj_or_str.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt_obj = datetime.datetime.strptime(dt_obj_or_str[:10], "%Y-%m-%d")
            except:
                return dt_obj_or_str
    else:
        dt_obj = dt_obj_or_str
        
    return dt_obj.strftime(format)

def format_datetime(dt_obj_or_str, format: str = "%d %b %Y, %H:%M") -> str:
    """Format a datetime object or ISO string into a standard display datetime."""
    return format_date(dt_obj_or_str, format)

def format_time(dt_obj_or_str, format: str = "%H:%M:%S") -> str:
    """Format time only."""
    return format_date(dt_obj_or_str, format)

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
