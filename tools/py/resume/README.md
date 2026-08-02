#

## How to tailor Resume for job description

```bash
# <folder> should be under ./tmp/tailoring
folder=<folder>
just prepare-llm $folder
# open <folder>/gen/llm_prompt.txt and paste into Google Studio AI
# paste output PART 1 into <folder>/body.md
just prepare-resume $folder
# genereate Resume created in <folder>/gen/resume.md and PDF <folder>/gen/resume.pdf

# to update PDF if changes to <folder>/gen/resume.md were made
just prepare-resume $folder
```
