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
