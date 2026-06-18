Act as a strict ATS Data Parsing Algorithm and Resume Editor.
Your task is to extract, filter, and compile data from my Master CV and tailor it specifically to the "Target Job Description"/JD provided below, optimizing it to achieve a maximum parse-rate on strict ATS hiring platforms (specifically Greenhouse, Ashby, Workday, SmartRecruiters, Lever, Personio, Workable, Eightfold.ai, and Softgarden).

You must condense the Master CV into a concise resume that fits on a maximum of 2 pages while being perfectly structured for algorithmic parsing.

Here are the strict rules for tailoring the CV:

1. ATS HIRING PLATFORM OPTIMIZATION & KEYWORD STRATEGY:
   - Exact Keyword Matching: Identify the hard skills, tools, frameworks, and methodologies in the Target Job Description. If (and ONLY if) these skills exist in my Master CV, use the exact phrasing from the JD in the output (e.g., if JD says "Amazon Web Services", change my "AWS" to "Amazon Web Services (AWS)").
   - Acronyms: If the JD uses an acronym (e.g., "CI/CD"), ensure both the spelled-out version and the acronym are used at least once in the CV (e.g., "Continuous Integration/Continuous Deployment (CI/CD)").
   - Keyword Density: Distribute matching core technical requirements naturally across the Summary, Skills, and Work Experience sections.
   - STRICT ZERO HALLUCINATION & NO EXAGGERATION: Do not invent, inflate, or assume any skills, metrics, or experiences. If a required ATS keyword is missing from my Master CV, DO NOT add it. Do not artificially increase my level of expertise (e.g., do not turn "assisted with AWS" into "architected AWS solutions").

2. WORK EXPERIENCE:
   - Keep ALL roles from the Master CV EXCEPT "Junior Developer | AS Tallink Group" and "Assembler | Fabek Elektroonika OÜ" (completely remove these two).
   - Strict Source Alignment & Merging: Keep the core facts, metrics, and narrative of the original Master CV EXACTLY intact. Limit your modifications strictly to: 1) Upgrading the starting action verb to a clean, professional standard, 2) Merging 2-3 related bullet points into a single concise bullet point to save space, 3) Trimming unnecessary words, and 4) Substituting existing words with exact-match ATS keywords from the JD ONLY where it perfectly matches my actual experience.
   - DO NOT INFLATE IMPACT: When merging bullet points, do not invent new accomplishments, do not imply I led or owned a project if the Master CV only states I contributed, and do not combine unrelated metrics. Stay 100% true to the source text's facts and seniority level.
   - Action Verbs: Start every single bullet point with a clear, professional, past-tense action verb (e.g., Built, Developed, Designed, Managed, Implemented, Migrated).
   - NO FLUFF WORDS: Do NOT under any circumstances use overly dramatic, cliché, or "fluffy" resume buzzwords (e.g., DO NOT USE Spearheaded, Streamlined, Adept, Championed, Revolutionized, Masterminded, or Synergized). Keep the tone grounded, authentic, and highly technical.
   - Bullet Limits: Limit the most recent job to a maximum of 5 bullet points. Older relevant jobs should have a maximum of 3 bullet points. Less relevant/older jobs should have exactly 1 bullet point summarizing the role.
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

5. STRICT TONE, STYLE & ZERO PARAPHRASING RULE:
   - Extractive Editing Only: You are strictly forbidden from paraphrasing, "improving," or rewriting my sentences.
   - The "Lego" Rule for Merging: When merging 2-3 bullet points together, you must act like you are copying and pasting the exact clauses from my Master CV and simply stitching them together with conjunctions (like "and" or "while").
   - No Synonyms: Treat my Master CV as an absolute vocabulary bank. Do not replace my nouns, verbs, or adjectives with "better" synonyms. If my CV says "wrote code for a feature," DO NOT change it to "engineered software solutions."
   - The ONLY exception to this rule is if you are substituting an existing word with an exact-match ATS keyword from the Job Description (e.g., changing "AWS" to "Amazon Web Services (AWS)"). Otherwise, use my exact original words.

6. OUTPUT FORMAT & STRUCTURE:
   Provide your response in THREE distinct parts. Do not include any conversational filler.
   - Line Breaks: Use two spaces at the end of a line to split new lines.
   - Exclusions: Do NOT generate a header (contact information) or a footer (university education and languages).

---

**PART 1: TAILORED RESUME**

- The resume output MUST be in pure Markdown format.
- Use standard Markdown headings (`#`, `##`, `###`), bold text for emphasis, and bullet points.
- Structure the resume with the exact following sections:
  - Summary (a customized 3-sentence summary based STRICTLY on actual Master CV facts, incorporating JD keywords natively)
  - Skills (List ONLY the technologies, tools, and skills explicitly mentioned in this tailored CV. Group them logically. Example: **Languages:** Python, Go | **Cloud & DevOps:** AWS, Docker).
  - Work Experience
  - Projects
  - Courses and Certificates

---

**PART 2: TAILORING JUSTIFICATION REPORT**

Briefly explain the strategic decisions you made:

- **ATS Keyword Strategy:** Explicitly list the top 5-10 exact-match keywords identified from the JD and successfully injected into the tailored CV.
- **Reductions & Omissions:** Explicitly list which specific bullet points or technical skills were removed or heavily reduced, and explain WHY based on the Target Job Description.
- **Merging & Selections:** Briefly explain which bullet points you merged, ensuring you confirm no facts were inflated.

---

**PART 3: ADDITIONAL OPTIONS (IF SPACE PERMITS)**

Provide highly relevant overflow content that was cut due to strict length limits:

- **Work Experience:** Provide 2 additional strong bullet points for the most recent/relevant roles that didn't make the top 5 cut but contain strong ATS keyword matches.
- **Courses & Certificates:** List 2 to 3 additional relevant courses/certificates that were omitted.
- **Projects:** Mention 1 additional relevant project with a single-line summary.

### MERGING EXAMPLE (HOW YOU MUST WRITE):

To ensure you understand the "Zero Paraphrasing" rule, here is an example of how you should merge bullet points.

Original Master CV Bullets:

- Built a custom dashboard using React and Node.js.
- Reduced the time it takes to generate monthly reports by 40%.
- Fixed bugs in the legacy database.

Incorrect LLM Output (BANNED - Uses new vocabulary and fluff):

- Architected a robust front-end dashboard using React and Node.js, spearheading the modernization of legacy databases and streamlining report generation times by 40%.

Correct LLM Output (REQUIRED - Uses exact source vocabulary):

- Built a custom dashboard using React and Node.js, reducing the time to generate monthly reports by 40%, and fixed bugs in the legacy database.

### DATA:

<master_cv>
{master_cv}
</master_cv>

<job_description>
{job_description}
</job_description>
