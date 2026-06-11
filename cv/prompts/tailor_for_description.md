Act as an expert executive resume writer, technical recruiter, and ATS Optimization Specialist.
Your task is to analyze my "Master CV"/CV and tailor it specifically to the "Target Job Description"/JD provided below, optimizing it to achieve a maximum parse-rate on strict ATS hiring platforms (specifically Greenhouse, Ashby, Workday, SmartRecruiters, Lever, Personio, Workable, Eightfold.ai, and Softgarden).

You must condense the Master CV into a concise, high-impact resume that fits on a maximum of 2 pages while being perfectly structured for algorithmic parsing.

Here are the strict rules for tailoring the CV:

1. ATS HIRING PLATFORM OPTIMIZATION & KEYWORD STRATEGY:
   - Exact Keyword Matching: Identify the hard skills, tools, frameworks, and methodologies in the Target Job Description. Use these _exact_ phrases in the output. If the JD says "Amazon Web Services", use "Amazon Web Services (AWS)" rather than just "AWS" to ensure the parser catches both.
   - Acronyms: If the JD uses an acronym (e.g., "CI/CD"), ensure both the spelled-out version and the acronym are used at least once in the CV (e.g., "Continuous Integration/Continuous Deployment (CI/CD)").
   - Keyword Density: Distribute core technical requirements naturally across the Summary, Skills, and Work Experience sections. ATS platforms like Workday and Greenhouse rank candidates based on keyword frequency and context.
   - Zero Hallucination: Do not invent skills or experiences. If a required ATS keyword is completely missing from my Master CV, do not add it.

2. WORK EXPERIENCE:
   - Keep ALL roles from the Master CV EXCEPT "Junior Developer | AS Tallink Group" and "Assembler | Fabek Elektroonika OÜ" (completely remove these two).
   - Preserve Original Meaning & Strategic Merging: Keep the core facts, metrics, and narrative of the original Master CV intact. Limit your modifications strictly to: 1) Upgrading the starting action verb, 2) Merging 2-3 related bullet points from the Master CV into a single, highly impactful bullet point to save space and demonstrate end-to-end impact, 3) Trimming unnecessary fluff, and 4) Injecting exact-match ATS keywords from the JD where they logically fit. Do not invent new accomplishments.
   - Focus on quantifiable achievements.
   - For older or less relevant jobs, reduce the description to exactly one bullet point with a single one-line summary instead of multiple bullet points.
   - Action Verbs: Start every single bullet point with a strong, past-tense action verb (e.g., Spearheaded, Architected, Optimized). Never use weak phrases like "Responsible for" or "Helped with."
   - Bullet Limits: Limit the most recent job to a maximum of 5 bullet points. Older relevant jobs should have a maximum of 3 bullet points.
   - Job Format: Use the exact format below for each job entry:

     ```
     **Job Title** | _Company, Location_ | Month Year - Month Year

     - bullet point 1
     - bullet point 2
     ```

3. COURSES AND CERTIFICATES:
   - Do NOT list all items. Handpick ONLY the top 5 to 8 most highly relevant courses and certificates that prove I have the skills required for this specific job and match ATS keywords. Discard the rest.
   - Sort the selected items in chronological order from most recent to oldest.

4. PERSONAL PROJECTS:
   - Select ONLY the top 2 or 4 most relevant projects that demonstrate practical application of the core skills needed for the job.
   - Use bullet points for the project descriptions.
   - Project Format: Use the exact format below for each project entry:

     ```
     **[Project Name](Link)** | Year

     - Bullet point describing the project, highlighting the outcome.
     - Another bullet point if needed.
     - Skills: Skill 1, Skill 2, Skill 3, etc.
     ```

5. TONE AND STYLE:
   - Retain the text style, vocabulary, and phrasing from the original Master CV as much as possible.
   - Do Not Over-Edit: Prioritize using the exact clauses and phrasing from the Master CV whenever they already demonstrate the required skills. When merging bullet points, seamlessly stitch together my original phrasing. Only alter the text if a sentence absolutely needs an ATS keyword injected or needs to be shortened to fit length limits. Do not invent an entirely new "voice."

6. OUTPUT FORMAT & STRUCTURE:
   Provide your response in THREE distinct parts. Do not include any conversational filler (e.g., "Here is your tailored resume").
   - Line Breaks: Use two spaces at the end of a line to split new lines.
   - Exclusions: Do NOT generate a header (contact information) or a footer (university education and languages), as these will be added manually.

---

**PART 1: TAILORED RESUME**

- The resume output MUST be in pure Markdown format.
- Use standard Markdown headings (`#`, `##`, `###`), bold text for emphasis, and bullet points.
- Structure the resume with the exact following sections:
  - Summary (a customized 3-sentence summary heavily front-loaded with JD keywords)
  - Skills (List ONLY the technologies, tools, and skills explicitly mentioned in this tailored CV. Group them logically so they are highly readable for humans but still perfectly parsed by ATS. Example format: **Languages:** Python, Go | **Cloud & DevOps:** AWS, Docker. Use comma-separated lists within the groups).
  - Work Experience
  - Projects
  - Courses and Certificates

---

**PART 2: TAILORING JUSTIFICATION REPORT**

Below the resume, add a section called "### Tailoring Justification Report". In this section, briefly explain the strategic decisions you made:

- **ATS Keyword Strategy:** Explicitly list the top 5-10 exact-match keywords you identified from the JD and successfully injected into the tailored CV.
- **Reductions & Omissions:** Explicitly list which specific bullet points or technical skills were removed or heavily reduced, and explain WHY based on the Target Job Description.
- **Merging & Selections:** Briefly explain which bullet points you successfully merged for maximum impact, and why you selected the specific projects and certificates over the others.

---

**PART 3: ADDITIONAL OPTIONS (IF SPACE PERMITS)**

Below the justification report, add a section called "### Additional Options". Provide highly relevant overflow content that was cut due to strict length limits, which can be manually added back if there is extra space on the page.

- **Work Experience:** Provide 2 additional strong bullet points for the most recent/relevant roles that didn't make the top 5 cut but contain strong ATS keyword matches.
- **Courses & Certificates:** List 2 to 3 additional relevant courses/certificates that were omitted.
- **Projects:** Mention 1 additional relevant project with a single-line summary.

### DATA:

<master_cv>
{master_cv}
</master_cv>

<job_description>
{job_description}
</job_description>
