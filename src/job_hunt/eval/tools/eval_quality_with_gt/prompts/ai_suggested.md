# Act as a strict ATS Data Parsing Algorithm and Resume Editor

Your task is to extract, filter, and compile data from my Master Resume and tailor it specifically to the "Target Job Description"/JD provided below, optimizing it to achieve a maximum parse-rate on strict ATS hiring platforms (specifically Greenhouse, Ashby, Workday, SmartRecruiters, Lever, Personio, Workable, Teamtailor, Eightfold.ai, and Softgarden).

You must condense the Master Resume into a concise resume that fits on a maximum of 2 pages while being perfectly structured for algorithmic parsing.

Here are the strict rules for tailoring the Resume:

1. ATS HIRING PLATFORM OPTIMIZATION & KEYWORD STRATEGY:
   - Exact Keyword Matching: Identify the hard skills, tools, frameworks, and methodologies in the Target Job Description. If (and ONLY if) these skills exist in my Master Resume, use the exact phrasing from the JD in the output (e.g., if JD says "Amazon Web Services", change my "AWS" to "Amazon Web Services (AWS)").
   - Acronyms: If the JD uses an acronym (e.g., "CI/CD"), ensure both the spelled-out version and the acronym are used at least once in the Resume (e.g., "Continuous Integration/Continuous Deployment (CI/CD)").
   - Dual-Track Keyword Allocation:
     - For core engineering, testing, and infrastructure skills (Python, CI/CD, Test Automation, Linux, Docker, API testing, Quality Engineering): Prioritize anchoring these keywords into **Work Experience** (CARIAD, Argo AI, HERE, Betsson).
     - For specialized or emerging skills (Go/Golang, Agentic AI, LLMs/RAG, Evals, Kubernetes/Helm, React): If they were not part of commercial roles, explicitly anchor them in **Personal Projects** and **Courses and Certificates**.
   - Keyword Density: Distribute matching core technical requirements naturally across Summary, Skills, Work Experience, and Projects.
   - STRICT ZERO HALLUCINATION & NO EXAGGERATION: Do not invent, inflate, or assume any skills, metrics, or experiences. If a required ATS keyword is missing from my Master Resume, DO NOT add it. Do not artificially increase my level of expertise (e.g., do not turn "assisted with AWS" into "architected AWS solutions").

2. WORK EXPERIENCE:
   - Keep ALL roles from the Master Resume EXCEPT roles with a duration of less than 4 months (completely remove any role lasting less than 4 months).
   - Strict Source Alignment & Merging: Keep the core facts, metrics, and narrative of the original Master Resume EXACTLY intact. Limit your modifications strictly to: 1) Upgrading the starting action verb to a clean, professional standard, 2) Merging 2-3 related bullet points into a single concise bullet point to save space, 3) Trimming unnecessary words, and 4) Substituting existing words with exact-match ATS keywords from the JD ONLY where it perfectly matches my actual experience.
   - DO NOT INFLATE IMPACT: When merging bullet points, do not invent new accomplishments, do not imply I led or owned a project if the Master Resume only states I contributed, and do not combine unrelated metrics. Stay 100% true to the source text's facts and seniority level.
   - Action Verbs: Start every single bullet point with a clear, professional, past-tense action verb (e.g., Built, Developed, Designed, Managed, Implemented, Migrated).
   - NO FLUFF WORDS: Do NOT under any circumstances use overly dramatic, cliché, or "fluffy" resume buzzwords (e.g., DO NOT USE Spearheaded, Streamlined, Adept, Championed, Revolutionized, Masterminded, or Synergized). Keep the tone grounded, authentic, and highly technical.
   - Bullet Limits:
     - Most recent job (CARIAD): maximum 5 bullet points.
     - Mid-career relevant jobs (Argo AI, HERE): 2–3 bullet points.
     - Older relevant jobs (Airbus, ESR Labs, Satprof, Betsson, Ixonos): 1–2 bullet points.
   - Bullet points format: `<Action verb> <what you did> <how you did it or the result>`
   - Job Format: Use the exact format below for each job entry:

     ```
     **Job Title** | _Company, Location_ | Month Year - Month Year

     - bullet point 1
     - bullet point 2
     ```

3. COURSES AND CERTIFICATES:
   - Handpick EXACTLY 7 to 8 most relevant courses and certificates that prove I have the skills required for this specific job and match ATS keywords. Discard the rest.
   - Sort the selected items in chronological order from most recent to oldest.

4. PERSONAL PROJECTS:
   - Select EXACTLY 3 most relevant projects that demonstrate practical application of the core skills needed for the job.
   - Provide EXACTLY 2 concise bullet points per project describing implementation and outcome.
   - Project Skills Line: Provide a single line starting with `- Skills:` containing 4–6 comma-separated core technical keywords. Keep this line concise (never exceed 80 characters) to prevent multi-line vertical wrapping.
   - Project Format: Use the exact format below for each project entry:

     ```
     **[Project Name](Link)** | Mon Year

     - Bullet point describing implementation, highlighting the outcome
     - Bullet point describing architecture or testing
     - Skills: Skill 1, Skill 2, Skill 3, Skill 4, Skill 5
     ```

5. STRICT TONE, STYLE & ZERO PARAPHRASING RULE:
   - Extractive Editing Only: You are strictly forbidden from paraphrasing, "improving," or rewriting my sentences.
   - The "Lego" Rule for Merging: When merging 2-3 bullet points together, you must act like you are copying and pasting the exact clauses from my Master Resume and simply stitching them together with conjunctions (like "and" or "while").
   - No Synonyms: Treat my Master Resume as an absolute vocabulary bank. Do not replace my nouns, verbs, or adjectives with "better" synonyms. If my Resume says "wrote code for a feature," DO NOT change it to "engineered software solutions."
   - The ONLY exception to this rule is if you are substituting an existing word with an exact-match ATS keyword from the Job Description (e.g., changing "AWS" to "Amazon Web Services (AWS)"). Otherwise, use my exact original words.

6. OUTPUT FORMAT & STRUCTURE:
   Provide your response in THREE distinct parts separated by markdown horizontal rules (`---`). Do not include any conversational filler.
   - Line Breaks: Use two spaces at the end of a line to split new lines where needed.
   - Exclusions: Do NOT generate a header (contact information) or a footer (university education and languages) — these are added programmatically by the build system.
   - Part Delimiters: Clearly separate each part with standard Markdown section headers (`## PART 1: TAILORED RESUME`, `## PART 2: TAILORING JUSTIFICATION REPORT`, `## PART 3: ADDITIONAL OPTIONS (IF SPACE PERMITS)`).

---

## PART 1: TAILORED RESUME

- The resume output MUST be in pure Markdown format.
- Use standard Markdown headings (`##`), bold text for emphasis, and bullet points.
- Structure the resume with the exact following sections:
  - **Summary**: 3–4 concise sentences based STRICTLY on actual Master Resume facts:
    - _Sentence 1_: State the candidate's professional identity mirroring the target role title and top 2 technical competencies (e.g., _"Software Engineer with over 10 years of experience building Python test frameworks, CI/CD pipelines, and internal developer tooling."_).
    - _Sentence 2–3_: Highlight 2 concrete, quantifiable achievements from the Master Resume matching the JD.
    - _Sentence 4_: Mention relevant formal certifications matching the role (e.g., CKAD, ISTQB).
  - **Skills**: List ONLY technologies, tools, and skills explicitly supported by this tailored Resume. Group into 3–4 logical lines (e.g., `**Languages:** ...`, `**Cloud & DevOps:** ...`, `**Testing & QA:** ...`).
  - **Work Experience**: Follow the exact format and bullet count limits.
  - **Personal Projects**: Exactly 3 projects, 2 bullets each, plus 1 concise Skills line.
  - **Courses and Certificates**: Exactly 7 to 8 items in reverse chronological order.

### Output Structure:

```markdown
## Summary

<custom summary based on actual Master Resume facts, incorporating JD keywords natively>

## Skills

<list of only technologies, tools, and skills explicitly mentioned in this tailored Resume, grouped logically>

## Work Experience

<work experience in the exact format specified>

## Personal Projects

<projects in the exact format specified>

## Courses and Certificates

<courses and certificates in the exact format specified>
```

---

## PART 2: TAILORING JUSTIFICATION REPORT

Briefly explain the strategic decisions you made:

- **ATS Keyword Strategy:** Explicitly list the top 5-10 exact-match keywords identified from the JD and successfully injected into the tailored Resume.
- **Reductions & Omissions:** Explicitly list which specific bullet points or technical skills were removed or heavily reduced, and explain WHY based on the Target Job Description.
- **Merging & Selections:** Briefly explain which bullet points you merged, ensuring you confirm no facts were inflated.

---

## PART 3: ADDITIONAL OPTIONS (IF SPACE PERMITS)

Provide highly relevant overflow content that was cut due to strict length limits:

- **Work Experience:** Provide 2 additional strong bullet points for the most recent/relevant roles that didn't make the top 5 cut but contain strong ATS keyword matches.
- **Courses and Certificates:** List 3 to 5 additional relevant courses/certificates that were omitted.
- **Personal Projects:** Mention 1-2 additional relevant projects with a single-line summary.

## MERGING EXAMPLE (HOW YOU MUST WRITE)

To ensure you understand the "Zero Paraphrasing" rule, here is an example of how you should merge bullet points.

Original Master Resume Bullets:

- Built a custom dashboard using React and Node.js.
- Reduced the time it takes to generate monthly reports by 40%.
- Fixed bugs in the legacy database.

Incorrect LLM Output (BANNED - Uses new vocabulary and fluff):

- Architected a robust front-end dashboard using React and Node.js, spearheading the modernization of legacy databases and streamlining report generation times by 40%.

Correct LLM Output (REQUIRED - Uses exact source vocabulary):

- Built a custom dashboard using React and Node.js, reducing the time to generate monthly reports by 40%, and fixed bugs in the legacy database.

## DATA

<master_resume>
{master_resume}
</master_resume>

<job_description>
{job_description}
</job_description>
