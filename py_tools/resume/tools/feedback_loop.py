import json
import re
from typing import Any

from loguru import logger
from pydantic_ai import Agent

from config.config import DEFAULT_CONFIG
from resume.tools.process_resume import check_markdown
from helpers.llm import get_agent, run_agent

_MAX_RETRIES = 5
SYSTEM_INSTRUCTIONS = """# You are an expert Resume Formatter Agent.
Your task is to fix specific formatting and validation errors in markdown Resume documents.

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
3. Finally, output the fully corrected and with  markdown text wrapped inside
   <final_resume>```markdown ... ```</final_resume> tags.

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
I added '  ' at the end of line 12, 13
## ...

```
</thinking>
<final_resume>
```markdown

...
## Skills

**Languages**: Python, Go, C++  
**Databases**: PostgreSQL  
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
    resume: str,
    model: str = DEFAULT_CONFIG.llm.fix_model,
    max_retries: int = _MAX_RETRIES,
    *,
    agent: Agent[Any, Any] | None = None,
) -> str:
    """Recursively run agent to fix Resume validation errors statelessly."""
    if agent is None:
        agent = get_agent(
            model_name=model,
            output_type=str,
            system_prompt=SYSTEM_INSTRUCTIONS,
        )

    cur_resume = resume
    current_errors = check_markdown(cur_resume)

    md_with_min_errors = cur_resume
    min_errors = len(current_errors)

    for iteration in range(max_retries):
        if min_errors == 0:
            logger.info("All validation errors successfully fixed.")
            break

        logger.info(f"Running agent to fix {min_errors} errors (iteration={iteration})...")

        errors_formatted = json.dumps([e.model_dump() for e in current_errors], indent=2)

        prompt = FIX_PROMPT_TEMPLATE.format(
            md=cur_resume,
            errors_formatted=errors_formatted,
        )

        try:
            result = run_agent(
                agent=agent,
                user_prompt=prompt,
            )

            cur_resume = extract_final_resume(result.output)

        except Exception as e:
            logger.error(f"Error during LLM generation: {e}")
            break

        current_errors = check_markdown(cur_resume)
        if min_errors > len(current_errors):
            min_errors = len(current_errors)
            md_with_min_errors = cur_resume

    return extract_final_resume(md_with_min_errors)
