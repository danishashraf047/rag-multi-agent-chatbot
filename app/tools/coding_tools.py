import ast

from langchain_core.tools import tool


@tool
async def python_syntax_check(code: str) -> str:
    """Check whether Python code parses successfully."""

    try:
        ast.parse(code)
    except SyntaxError as exc:
        return f"SyntaxError on line {exc.lineno}: {exc.msg}"
    return "Python syntax looks valid."
