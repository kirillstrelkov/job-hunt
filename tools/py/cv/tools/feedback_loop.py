import json
import re
from typing import Any

from loguru import logger
from pydantic_ai import Agent

from config.config import DEFAULT_CONFIG
from cv.tools.process_cv import check_markdown
from helpers.llm import get_agent, run_agent

_DEPTH_LIMIT = 5
SYSTEM_INSTRUCTIONS = """# You are an expert Resume Formatter Agent.
Your task is to fix specific formatting and validation errors in markdown CV documents.

Strictly follow these steps:
1. First group validation errros by msg, analyze the errors and apply fixes for each group separately
   inside <thinking>...</thinking> tags use following format:
   <thinking>
    ```
    ## Error: "<msg>", lines: <line_num1>, <line_num2>, ...
    <description about what was changed>
    ...
    ```
   </thinking>
2. Keep all original content, sections, titles, and bullet points exactly the same.
   Do not re-write or summarize the text.
3. Finally, output the fully corrected and with  markdown text wrapped inside <final_resume>```markdown ... ```</final_resume> tags.

Do not output anything after the </final_resume> tag.

## validation_errors structure

```json
[
    {
        "msg": str,
        "filepath": str,
        "line_num": int,
        "line": str
    }
]
```

## Output example
```
<thinking>
```markdown

## Error: "Line in Skills section must end with single backslash", lines: 12, 13
I added '\\' at the end of line 12, 13
## ...

```
</thinking>
<final_resume>
```markdown

...
## Skills

**Languages**: Python, Go, C++\\
**Databases**: PostgreSQL\\
...

```
</final_resume>

"""

FIX_PROMPT_TEMPLATE = """Please fix the validation errors in the following resume.

## Resume

<resume>
```markdown

{md}

```
</resume>

## Validation errors

<validation_errors>
```json

{errors_formatted}

```
</validation_errors>
"""


def extract_final_resume(llm_output: str) -> str:
    """Safely extracts the resume from the LLM output."""
    match = re.search(r"<final_resume>(.*?)</final_resume>", llm_output, re.DOTALL)
    if match:
        return match.group(1).strip()

    match_md = re.search(r"```(?:markdown)?\n(.*?)\n```", llm_output, re.DOTALL)
    if match_md:
        return match_md.group(1).strip()

    clean_text = re.sub(r"<thinking>.*?</thinking>", "", llm_output, flags=re.DOTALL)
    return clean_text.strip()


def fix_with_feedback(
    md: str,
    model: str = DEFAULT_CONFIG.llm.fix_model,
    errors: list[Any] | None = None,
    *,
    _depth: int = 0,
    agent: Agent[Any, Any] | None = None,
) -> str:
    """Recursively run agent to fix CV validation errors statelessly."""
    if agent is None:
        agent = get_agent(
            model_name=model,
            output_type=str,
            system_prompt=SYSTEM_INSTRUCTIONS,
        )

    if errors is None:
        errors = check_markdown(md)

    if not errors:
        logger.info("All validation errors successfully fixed.")
        return md

    if _depth >= _DEPTH_LIMIT:
        logger.warning("Max recursion depth reached. Returning current markdown.")
        return md

    logger.info(f"Running agent to fix {len(errors)} errors (depth={_depth})...")

    errors_formatted = json.dumps([e.model_dump() for e in errors], indent=2)

    prompt = FIX_PROMPT_TEMPLATE.format(md=md, errors_formatted=errors_formatted)

    try:
        result = run_agent(
            agent=agent,
            user_prompt=prompt,
        )

        new_md = extract_final_resume(result.output)

    except Exception as e:
        logger.error(f"Error during LLM generation: {e}")
        return md

    return fix_with_feedback(
        new_md,
        model,
        _depth=_depth + 1,
        agent=agent,
    )
