Act as an expert executive resume writer and technical recruiter.
Your task is to analyze my "Master CV" and tailor it specifically to the "Target Job Description" provided below.

You must condense the Master CV into a concise, high-impact resume that would fit on a maximum of 2 pages.

Here are the strict rules for tailoring the CV:

1. WORK EXPERIENCE:

   - Keep ALL roles from the Master CV EXCEPT "Junior Developer | AS Tallink Group" and "Assembler | Fabek Elektroonika OÜ" (completely remove these two).
   - Highlight the most recent and relevant roles by rewriting and compacting the bullet points so they directly align with the keywords, requirements, and responsibilities mentioned in the Target Job Description.
   - Focus on quantifiable achievements.
   - For older or less relevant jobs, reduce the description to exactly one bullet point with single one-line summary instead of multiple bullet points.
   - Action Verbs: Start every single bullet point with a strong, past-tense action verb (e.g., Spearheaded, Architected, Optimized). Never use weak phrases like "Responsible for" or "Helped with."
   - Bullet Limits: Limit the most recent job to a maximum of 5 bullet points. Older relevant jobs should have a maximum of 3 bullet points.
   - Job Format: Use the exact format below for each job entry:

     ```
     **Job Title** | _Company, Location_ | Month Year - Month Year

     - bullet point 1
     - bullet point 2
     ```

2. COURSES AND CERTIFICATES:

   - Do NOT list all items. Handpick ONLY the top 5 to 8 most highly relevant courses and certificates that prove I have the skills required for this specific job. Discard the rest.
   - Sort the selected items in chronological order from most recent to oldest.

3. PERSONAL PROJECTS:

   - Select ONLY the top 2 or 4 most relevant projects that demonstrate practical application of the core skills needed for the job.
   - Use bullet points for the project descriptions.
   - Project Format: Use the exact format below for each project entry:

     ```
     **[Project Name](Link)** | Year

     - Bullet point describing the project, highlighting the outcome.
     - Another bullet point if needed.
     - Skills: Skill 1, Skill 2, Skill 3, etc.
     ```

4. TONE AND STYLE:

   - Retain the text style, vocabulary, and phrasing from the original Master CV as much as possible.
   - Only rewrite when necessary to improve impact, insert crucial keywords from the job description, or combine points for conciseness. Do not invent an entirely new "voice."

5. OUTPUT FORMAT & STRUCTURE:
   Provide your response in THREE distinct parts. Do not include any conversational filler (e.g., "Here is your tailored resume").
   - Line Breaks: Use two spaces at the end of a line to split new lines.
   - Exclusions: Do NOT generate a header (contact information) or a footer (university education and languages), as these will be added manually.

---

**PART 1: TAILORED RESUME**

- The resume output MUST be in pure Markdown format.
- Use standard Markdown headings (`#`, `##`, `###`), bold text for emphasis, and bullet points.
- Structure the resume with the exact following sections:
  - Summary (a customized 3-sentence summary based on the job description)
  - Skills (List ONLY the technologies, tools, and skills that are explicitly mentioned inside the text of this newly tailored CV. Do not pull extra skills from the Master CV if they did not make the cut).
  - Work Experience
  - Projects
  - Courses and Certificates

---

**PART 2: TAILORING JUSTIFICATION REPORT**

Below the resume, add a section called "### Tailoring Justification Report". In this section, briefly explain the strategic decisions you made:

- **Reductions & Omissions:** Explicitly list which specific bullet points or technical skills were removed or heavily reduced, and explain WHY based on the Target Job Description.
- **Selections:** Briefly explain why you selected the specific projects and certificates over the others.

---

**PART 3: ADDITIONAL OPTIONS (IF SPACE PERMITS)**

Below the justification report, add a section called "### Additional Options". Provide highly relevant overflow content that was cut due to strict length limits, which can be manually added back if there is extra space on the page.

- **Work Experience:** Provide 2 additional strong bullet points for the most recent/relevant roles that didn't make the top 5 cut but are highly relevant to the job.
- **Courses & Certificates:** List 2 to 3 additional relevant courses/certificates that were omitted.
- **Projects:** Mention 1 additional relevant project with a single-line summary.

### DATA:

<master_cv>
{master_cv}
</master_cv>

<job_description>
{job_description}
</job_description>
