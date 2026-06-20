#

## How to tailor CV for job description

```bash
# <folder> should be under ./tmp/tailoring
folder=<folder>
just prepare-llm $folder
# open <folder>/gen/llm_prompt.txt and paste into Google Studio AI
# paste output PART 1 into <folder>/body.md
just prepare-cv $folder
# genereate CV created in <folder>/gen/cv.md and PDF <folder>/gen/cv.pdf

# to update PDF if changes to <folder>/gen/cv.md were made
just prepare-cv $folder
```
