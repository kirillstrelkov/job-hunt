import re
from typing import Optional
from pydantic import BaseModel, Field


class Duration(BaseModel):
    """Pydantic model representing duration with optional start date and end date."""

    start_date: Optional[str] = None
    end_date: str

    @classmethod
    def from_string(cls, s: str) -> "Duration":
        s = s.strip()
        # Find separators. Order matters (longer first)
        separators = [" \\- ", " - ", " \\hfill ", " hfill ", " to ", "\\-", "-"]
        for sep in separators:
            if sep in s:
                parts = s.split(sep, 1)
                return cls(start_date=parts[0].strip(), end_date=parts[1].strip())
        return cls(start_date=None, end_date=s)

    def to_string(self) -> str:
        if self.start_date:
            return f"{self.start_date} \\- {self.end_date}"
        return self.end_date


class BulletPoint(BaseModel):
    """Pydantic model representing a bullet point text."""

    text: str

    @classmethod
    def from_string(cls, s: str) -> "BulletPoint":
        s = s.strip()
        if s.startswith("- "):
            s = s[2:].strip()
        elif s.startswith("* "):
            s = s[2:].strip()
        return cls(text=s)

    def to_string(self) -> str:
        return f"- {self.text}"


class Skill(BaseModel):
    """Pydantic model representing a skill text."""

    text: str

    @classmethod
    def from_string(cls, s: str) -> "Skill":
        return cls(text=s.strip())

    def to_string(self) -> str:
        return self.text


class Summary(BaseModel):
    """Pydantic model representing a summary entry."""

    text: str

    @classmethod
    def from_string(cls, s: str) -> "Summary":
        # Strip header if present
        lines = [line.strip() for line in s.split("\n")]
        text_lines = []
        for line in lines:
            if line.startswith("## ") and "summary" in line.lower():
                continue
            text_lines.append(line)
        return cls(text="\n".join(text_lines).strip())

    def to_string(self) -> str:
        return f"## Summary\n\n{self.text}"


class SkillGroup(BaseModel):
    """Pydantic model representing a skill group containing name and list of skills."""

    name: str
    skills: list[Skill]

    @classmethod
    def from_string(cls, s: str) -> "SkillGroup":
        s = s.strip()
        if ":" in s:
            name_part, skills_part = s.split(":", 1)
            name = name_part.strip().strip("*").strip()
            skills_list = [Skill.from_string(sk) for sk in skills_part.split(",") if sk.strip()]
            return cls(name=name, skills=skills_list)
        return cls(name="", skills=[Skill.from_string(s)])

    def to_string(self) -> str:
        skills_str = ", ".join(sk.to_string() for sk in self.skills)
        return f"**{self.name}**: {skills_str}"


class Skills(BaseModel):
    """Pydantic model representing a skills section containing a list of skill groups."""

    groups: list[SkillGroup]

    @classmethod
    def from_string(cls, s: str) -> "Skills":
        lines = [line.strip() for line in s.split("\n") if line.strip()]
        content_line = ""
        for line in lines:
            if line.startswith("## ") and "skills" in line.lower():
                continue
            content_line = line
            break

        groups_list = []
        if content_line:
            parts = [p.strip() for p in content_line.split("|") if p.strip()]
            for part in parts:
                groups_list.append(SkillGroup.from_string(part))
        return cls(groups=groups_list)

    def to_string(self) -> str:
        groups_str = " | ".join(g.to_string() for g in self.groups)
        return f"## Skills\n\n{groups_str}"


class Thesis(BaseModel):
    """Pydantic model representing a thesis with name and URL."""

    name: str
    url: str

    @classmethod
    def from_string(cls, s: str) -> "Thesis":
        s = s.strip()
        for prefix in ["- Thesis:", "Thesis:", "- Thesis: "]:
            if s.startswith(prefix):
                s = s[len(prefix):].strip()
                break
        match = re.search(r"\[(.*?)\]\((.*?)\)", s)
        if match:
            return cls(name=match.group(1).strip(), url=match.group(2).strip())
        return cls(name=s, url="")

    def to_string(self) -> str:
        return f"- Thesis: [{self.name}]({self.url})"


class Language(BaseModel):
    """Pydantic model representing a language name and level."""

    name: str
    level: str

    @classmethod
    def from_string(cls, s: str) -> "Language":
        s = s.strip()
        if ":" in s:
            name_part, level_part = s.split(":", 1)
            name = name_part.strip().strip("*").strip()
            level = level_part.strip()
            return cls(name=name, level=level)
        return cls(name=s, level="")

    def to_string(self) -> str:
        return f"**{self.name}**: {self.level}"


class Degree(BaseModel):
    """Pydantic model representing an education degree, institution, duration, and optional thesis."""

    degree: str
    institution: str
    duration: Duration
    thesis: Optional[Thesis] = None

    @classmethod
    def from_string(cls, s: str) -> "Degree":
        lines = [line.strip() for line in s.strip().split("\n") if line.strip()]
        if not lines:
            raise ValueError("Empty string for Degree")

        header_line = lines[0]
        parts = []
        for part in header_line.split("|"):
            for subsep in [" \\hfill ", " \\hfill", "\\hfill ", "\\hfill"]:
                if subsep in part:
                    subparts = part.split(subsep, 1)
                    parts.extend(subparts)
                    break
            else:
                parts.append(part)

        parts = [p.strip() for p in parts if p.strip()]
        degree = ""
        institution = ""
        duration_str = ""

        if len(parts) >= 1:
            degree = parts[0].strip().strip("*").strip()
        if len(parts) >= 2:
            institution = parts[1].strip().strip("_").strip()
        if len(parts) >= 3:
            duration_str = parts[2].strip()

        duration = Duration.from_string(duration_str)

        thesis = None
        for line in lines[1:]:
            if "Thesis:" in line or "thesis" in line.lower():
                thesis = Thesis.from_string(line)
                break

        return cls(degree=degree, institution=institution, duration=duration, thesis=thesis)

    def to_string(self) -> str:
        duration_str = self.duration.to_string()
        lines = [f"**{self.degree}** | _{self.institution}_ \\hfill {duration_str}"]
        if self.thesis:
            lines.append("")
            lines.append(self.thesis.to_string())
        return "\n".join(lines)


class WorkExperience(BaseModel):
    """Pydantic model representing a work experience entry."""

    title: str
    company: str
    location: Optional[str] = None
    duration: Duration
    bullet_points: list[BulletPoint]
    reason_for_resignation: Optional[str] = None
    skills: Optional[list[Skill]] = None

    @classmethod
    def from_string(cls, s: str) -> "WorkExperience":
        lines = [line.strip() for line in s.strip().split("\n") if line.strip()]
        if not lines:
            raise ValueError("Empty string for WorkExperience")

        header_line = lines[0]
        parts = [p.strip() for p in header_line.split("|")]

        title = ""
        company_loc = ""
        duration_str = ""

        if len(parts) >= 1:
            title = parts[0].strip().strip("*").strip()
        if len(parts) >= 2:
            company_loc = parts[1].strip().strip("_").strip()
        if len(parts) >= 3:
            duration_str = parts[2].strip()

        # Split on the first comma to support company and location
        company = company_loc
        location = None
        if "," in company_loc:
            c_part, l_part = company_loc.split(",", 1)
            company = c_part.strip()
            location = l_part.strip()

        duration = Duration.from_string(duration_str)

        bullet_points = []
        reason = None
        skills = None

        for line in lines[1:]:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith(">"):
                content = line_str.lstrip(">").strip()
                if content.startswith("_") and content.endswith("_"):
                    content = content[1:-1].strip()
                prefix = "Reason for resignation:"
                if content.startswith(prefix):
                    reason = content[len(prefix):].strip()
            elif "Skills:" in line_str or line_str.startswith("- Skills:") or line_str.startswith("Skills:"):
                skills_part = line_str
                for prefix in ["- Skills:", "* Skills:", "Skills:"]:
                    if skills_part.startswith(prefix):
                        skills_part = skills_part[len(prefix):].strip()
                        break
                skills_part = skills_part.rstrip(".")
                skill_names = [sk.strip() for sk in skills_part.split(",") if sk.strip()]
                skills = [Skill(text=name) for name in skill_names]
            elif line_str.startswith("- ") or line_str.startswith("* "):
                bullet_points.append(BulletPoint.from_string(line_str))

        return cls(
            title=title,
            company=company,
            location=location,
            duration=duration,
            bullet_points=bullet_points,
            reason_for_resignation=reason,
            skills=skills,
        )

    def to_string(self) -> str:
        lines = []
        duration_str = self.duration.to_string()
        if self.location:
            comp_loc_str = f"{self.company}, {self.location}"
        else:
            comp_loc_str = self.company
        lines.append(f"**{self.title}** | _{comp_loc_str}_ | {duration_str}")
        lines.append("")
        for bp in self.bullet_points:
            lines.append(bp.to_string())
        if self.skills:
            skills_str = ", ".join(s.to_string() for s in self.skills)
            lines.append(f"- Skills: {skills_str}")
        if self.reason_for_resignation:
            lines.append("")
            lines.append(f"> _Reason for resignation: {self.reason_for_resignation}_")
        return "\n".join(lines)


class PersonalProjects(BaseModel):
    """Pydantic model representing a personal project entry."""

    name: str
    url: str
    duration: Duration
    bullet_points: list[BulletPoint]
    skills: list[Skill]

    @classmethod
    def from_string(cls, s: str) -> "PersonalProjects":
        lines = [line.strip() for line in s.strip().split("\n") if line.strip()]
        if not lines:
            raise ValueError("Empty string for PersonalProjects")

        header_line = lines[0]
        parts = [p.strip() for p in header_line.split("|")]

        link_part = ""
        duration_str = ""

        if len(parts) >= 1:
            link_part = parts[0].strip().strip("*").strip()
        if len(parts) >= 2:
            duration_str = parts[1].strip()

        name = link_part
        url = ""
        match = re.search(r"\[(.*?)\]\((.*?)\)", link_part)
        if match:
            name = match.group(1).strip()
            url = match.group(2).strip()

        duration = Duration.from_string(duration_str)

        bullet_points = []
        skills = []

        for line in lines[1:]:
            line_str = line.strip()
            if not line_str:
                continue
            if "Skills:" in line_str or line_str.startswith("- Skills:") or line_str.startswith("Skills:"):
                skills_part = line_str
                for prefix in ["- Skills:", "* Skills:", "Skills:"]:
                    if skills_part.startswith(prefix):
                        skills_part = skills_part[len(prefix):].strip()
                        break
                skills_part = skills_part.rstrip(".")
                skill_names = [sk.strip() for sk in skills_part.split(",") if sk.strip()]
                skills = [Skill(text=name) for name in skill_names]
            elif line_str.startswith("- ") or line_str.startswith("* "):
                bullet_points.append(BulletPoint.from_string(line_str))

        return cls(
            name=name,
            url=url,
            duration=duration,
            bullet_points=bullet_points,
            skills=skills,
        )

    def to_string(self) -> str:
        lines = []
        duration_str = self.duration.to_string()
        lines.append(f"**[{self.name}]({self.url})** | {duration_str}")
        lines.append("")
        for bp in self.bullet_points:
            lines.append(bp.to_string())
        skills_str = ", ".join(s.to_string() for s in self.skills)
        lines.append(f"- Skills: {skills_str}.")
        return "\n".join(lines)


class CoursesAndCertificates(BaseModel):
    """Pydantic model representing a course or certificate entry."""

    name: str
    institution: str
    duration: Duration

    @classmethod
    def from_string(cls, s: str) -> "CoursesAndCertificates":
        s = s.strip()
        if s.startswith("- "):
            s = s[2:].strip()
        elif s.startswith("* "):
            s = s[2:].strip()

        parts = [p.strip() for p in s.split("|")]
        name = ""
        institution = ""
        duration_str = ""

        if len(parts) >= 1:
            name = parts[0].strip()
        if len(parts) >= 2:
            institution = parts[1].strip().strip("_").strip()
        if len(parts) >= 3:
            duration_str = parts[2].strip()

        duration = Duration.from_string(duration_str)
        return cls(name=name, institution=institution, duration=duration)

    def to_string(self) -> str:
        duration_str = self.duration.to_string()
        return f"- {self.name} | _{self.institution}_ | {duration_str}"


class Header(BaseModel):
    """Pydantic model representing the CV header containing contact information."""

    name: str
    address: str
    email: str
    telephone: str
    linkedin: str
    github: str

    @classmethod
    def from_string(cls, s: str) -> "Header":
        lines = [line.strip() for line in s.strip().split("\n") if line.strip()]

        name = ""
        address = ""
        email = ""
        telephone = ""
        linkedin = ""
        github = ""

        def get_md_link_url(text: str) -> str:
            match = re.search(r"\[(.*?)\]\((.*?)\)", text)
            if match:
                return match.group(2).strip()
            return text.strip()

        for line in lines:
            if line.startswith("# "):
                name = line[2:].strip()
            elif "---" in line:
                continue
            elif "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if any("linkedin.com" in p or "github.com" in p for p in parts):
                    for part in parts:
                        if "linkedin.com" in part:
                            linkedin = get_md_link_url(part)
                        elif "github.com" in part:
                            github = get_md_link_url(part)
                else:
                    for part in parts:
                        if "@" in part or "<" in part:
                            email_str = part.strip()
                            if email_str.startswith("<") and email_str.endswith(">"):
                                email_str = email_str[1:-1].strip()
                            email = email_str
                        elif part.strip().startswith("+") or any(c.isdigit() for c in part):
                            telephone = part.strip()
                        else:
                            address = part.strip()

        return cls(
            name=name,
            address=address,
            email=email,
            telephone=telephone,
            linkedin=linkedin,
            github=github,
        )

    def to_string(self) -> str:
        lines = []
        lines.append(f"# {self.name}")
        lines.append("")

        contact_parts = []
        if self.address:
            contact_parts.append(self.address)
        if self.email:
            contact_parts.append(f"<{self.email}>")
        if self.telephone:
            contact_parts.append(self.telephone)
        lines.append(" | ".join(contact_parts) + "  ")

        social_parts = []
        if self.linkedin:
            label = self.linkedin.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
            social_parts.append(f"[{label}]({self.linkedin})")
        if self.github:
            label = self.github.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
            social_parts.append(f"[{label}]({self.github})")
        lines.append(" | ".join(social_parts))
        lines.append("")
        lines.append("---")
        lines.append("")
        return "\n".join(lines)


class Footer(BaseModel):
    """Pydantic model representing the CV footer containing education and languages."""

    educations: list[Degree] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)

    @classmethod
    def from_string(cls, s: str) -> "Footer":
        lines = [line.strip() for line in s.strip().split("\n")]

        educations = []
        languages = []

        current_section = None
        section_lines = []

        for line in lines:
            line_str = line.strip()
            if line_str.startswith("## "):
                if current_section == "education" and section_lines:
                    edu_block = []
                    for edu_line in section_lines:
                        if edu_line.strip().startswith("**") and " | " in edu_line:
                            if edu_block:
                                educations.append(Degree.from_string("\n".join(edu_block)))
                                edu_block = []
                        edu_block.append(edu_line)
                    if edu_block:
                        educations.append(Degree.from_string("\n".join(edu_block)))
                elif current_section == "languages" and section_lines:
                    lang_line = " ".join(section_lines).strip()
                    lang_parts = [lp.strip() for lp in lang_line.split(",") if lp.strip()]
                    for lp in lang_parts:
                        languages.append(Language.from_string(lp))

                current_section = line_str[3:].strip().lower()
                section_lines = []
            else:
                if current_section:
                    section_lines.append(line)

        # Parse last section
        if current_section == "education" and section_lines:
            edu_block = []
            for edu_line in section_lines:
                if edu_line.strip().startswith("**") and " | " in edu_line:
                    if edu_block:
                        educations.append(Degree.from_string("\n".join(edu_block)))
                        edu_block = []
                edu_block.append(edu_line)
            if edu_block:
                educations.append(Degree.from_string("\n".join(edu_block)))
        elif current_section == "languages" and section_lines:
            lang_line = " ".join(section_lines).strip()
            lang_parts = [lp.strip() for lp in lang_line.split(",") if lp.strip()]
            for lp in lang_parts:
                languages.append(Language.from_string(lp))

        return cls(educations=educations, languages=languages)

    def to_string(self) -> str:
        lines = []
        if self.educations:
            lines.append("## Education")
            lines.append("")
            for edu in self.educations:
                lines.append(edu.to_string())
                lines.append("")
        if self.languages:
            lines.append("## Languages")
            lines.append("")
            lang_strs = [lang.to_string() for lang in self.languages]
            lines.append(", ".join(lang_strs))
            lines.append("")
        return "\n".join(lines)


class Body(BaseModel):
    """Pydantic model representing the CV body containing work history, projects, and courses."""

    work_experience: list[WorkExperience] = Field(default_factory=list)
    personal_projects: list[PersonalProjects] = Field(default_factory=list)
    courses_and_certificates: list[CoursesAndCertificates] = Field(default_factory=list)

    @classmethod
    def from_string(cls, s: str) -> "Body":
        lines = s.replace("\r\n", "\n").split("\n")

        sections = {}
        current_section = None
        section_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(section_lines)
                    section_lines = []
                current_section = stripped[3:].strip().lower()
            else:
                if current_section:
                    section_lines.append(line)
        if current_section:
            sections[current_section] = "\n".join(section_lines)

        work_experience = []
        personal_projects = []
        courses_and_certificates = []

        # Parse work experience
        work_text = next((content for name, content in sections.items() if "work" in name), "")
        if work_text.strip():
            we_block = []
            for w_line in work_text.split("\n"):
                stripped = w_line.strip()
                if stripped.startswith("**") and " | " in stripped:
                    if we_block:
                        work_experience.append(WorkExperience.from_string("\n".join(we_block)))
                        we_block = []
                we_block.append(w_line)
            if we_block:
                work_experience.append(WorkExperience.from_string("\n".join(we_block)))

        # Parse personal projects
        project_text = next((content for name, content in sections.items() if "project" in name), "")
        if project_text.strip():
            pp_block = []
            for p_line in project_text.split("\n"):
                stripped = p_line.strip()
                if stripped.startswith("**") and (" | " in stripped or "[" in stripped):
                    if pp_block:
                        personal_projects.append(PersonalProjects.from_string("\n".join(pp_block)))
                        pp_block = []
                pp_block.append(p_line)
            if pp_block:
                personal_projects.append(PersonalProjects.from_string("\n".join(pp_block)))

        # Parse courses and certificates
        course_text = next((content for name, content in sections.items() if "course" in name or "cert" in name), "")
        if course_text.strip():
            for c_line in course_text.split("\n"):
                stripped = c_line.strip()
                if stripped.startswith("- ") or stripped.startswith("* "):
                    courses_and_certificates.append(CoursesAndCertificates.from_string(c_line))

        return cls(
            work_experience=work_experience,
            personal_projects=personal_projects,
            courses_and_certificates=courses_and_certificates,
        )

    def to_string(self) -> str:
        sections = []
        if self.work_experience:
            we_lines = ["## Work experience", ""]
            we_lines.extend(we.to_string() for we in self.work_experience)
            sections.append("\n\n".join(we_lines))
        if self.personal_projects:
            pp_lines = ["## Personal projects", ""]
            pp_lines.extend(pp.to_string() for pp in self.personal_projects)
            sections.append("\n\n".join(pp_lines))
        if self.courses_and_certificates:
            cc_section = ["## Courses and certificates", ""]
            cc_section.append("\n".join(cc.to_string() for cc in self.courses_and_certificates))
            sections.append("\n".join(cc_section))
        return "\n\n".join(sections)


class CV(BaseModel):
    """Pydantic model representing the entire CV structure."""

    header: Optional[Header] = None
    body: Body
    footer: Optional[Footer] = None

    @classmethod
    def from_string(cls, s: str) -> "CV":
        text = s.replace("\r\n", "\n")

        header_text = None
        body_text = text
        footer_text = None

        if "---" in text:
            parts = text.split("---", 1)
            header_text = parts[0] + "---"
            body_text = parts[1]

        footer_start = -1
        for marker in ["## Education", "## Languages"]:
            idx = body_text.find(marker)
            if idx != -1:
                if footer_start == -1 or idx < footer_start:
                    footer_start = idx

        if footer_start != -1:
            footer_text = body_text[footer_start:]
            body_text = body_text[:footer_start]

        header = Header.from_string(header_text) if header_text and header_text.strip() else None
        body = Body.from_string(body_text)
        footer = Footer.from_string(footer_text) if footer_text and footer_text.strip() else None

        return cls(header=header, body=body, footer=footer)

    def to_string(self) -> str:
        parts = []
        if self.header:
            parts.append(self.header.to_string().strip())
        if self.body:
            parts.append(self.body.to_string().strip())
        if self.footer:
            parts.append(self.footer.to_string().strip())
        return "\n\n".join(parts) + "\n"
