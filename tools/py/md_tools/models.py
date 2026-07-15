"""Pydantic models representing structured sections and elements of a CV."""

import re
import tempfile
from pathlib import Path
from pydantic import BaseModel, Field


class SectionConstant:
    """Constants for section names in a CV."""

    SUMMARY = "Summary"
    SKILLS = "Skills"
    LANGUAGES = "Languages"
    EDUCATION = "Education"
    WORK_EXPERIENCE = "Work experience"
    PERSONAL_PROJECTS = "Personal projects"
    COURSES_AND_CERTIFICATES = "Courses and certificates"
    INFO = "Info"


class Line(BaseModel):
    """Represents a single line from the CV with its content and line number."""

    raw_line: str
    number: int


class Section(BaseModel):
    """Base Pydantic model representing a structured section of a CV."""

    name: str
    md_prefix: str
    filepath: Path = Field(default_factory=lambda: Path(""))
    raw_lines: list[Line] = Field(default_factory=list)

    def __init__(self, **data):
        if "filepath" not in data or data["filepath"] is None:
            # Create a temp file path if None/not provided
            with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as tmp:
                data["filepath"] = Path(tmp.name)
        elif isinstance(data["filepath"], str):
            data["filepath"] = Path(data["filepath"])
        super().__init__(**data)

    def is_root(self) -> bool:
        return self.md_prefix == "#"


class Duration(BaseModel):
    """Pydantic model representing duration with optional start date and end date."""

    start_date: str | None = None
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
        if s.startswith(("- ", "* ")):
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


class Summary(Section):
    """Pydantic model representing a summary section."""

    name: str = SectionConstant.SUMMARY
    md_prefix: str = "##"
    text: str = ""

    @classmethod
    def from_string(cls, s: str, filepath: Path | None = None, raw_lines: list[Line] = None) -> "Summary":
        # Strip header if present
        lines = [line.strip() for line in s.split("\n")]
        text_lines = []
        for line in lines:
            if line.startswith("## ") and "summary" in line.lower():
                continue
            text_lines.append(line)
        text = "\n".join(text_lines).strip()
        return cls(
            name=SectionConstant.SUMMARY, md_prefix="##", filepath=filepath, raw_lines=raw_lines or [], text=text
        )

    def to_string(self) -> str:
        return f"## {SectionConstant.SUMMARY}\n\n{self.text}"


class SkillGroupEntry(BaseModel):
    """Pydantic model representing a skill group containing name and list of skills."""

    name: str
    skills: list[Skill]

    @classmethod
    def from_string(cls, s: str) -> "SkillGroupEntry":
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


class SkillGroup(Section):
    """Pydantic model representing a skills section containing a list of skill groups."""

    name: str = SectionConstant.SKILLS
    md_prefix: str = "##"
    groups: list[SkillGroupEntry] = Field(default_factory=list)

    @classmethod
    def from_string(cls, s: str, filepath: Path | None = None, raw_lines: list[Line] = None) -> "SkillGroup":
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
            groups_list.extend(SkillGroupEntry.from_string(part) for part in parts)
        return cls(
            name=SectionConstant.SKILLS,
            md_prefix="##",
            filepath=filepath,
            raw_lines=raw_lines or [],
            groups=groups_list,
        )

    def to_string(self) -> str:
        groups_str = " | ".join(g.to_string() for g in self.groups)
        return f"## {SectionConstant.SKILLS}\n\n{groups_str}"


# Alias for backward compatibility
Skills = SkillGroup


class Thesis(BaseModel):
    """Pydantic model representing a thesis with name and URL."""

    name: str
    url: str

    @classmethod
    def from_string(cls, s: str) -> "Thesis":
        s = s.strip()
        for prefix in ["- Thesis:", "Thesis:", "- Thesis: "]:
            if s.startswith(prefix):
                s = s[len(prefix) :].strip()
                break
        match = re.search(r"\[(.*?)\]\((.*?)\)", s)
        if match:
            return cls(name=match.group(1).strip(), url=match.group(2).strip())
        return cls(name=s, url="")

    def to_string(self) -> str:
        return f"- Thesis: [{self.name}]({self.url})"


class LanguageEntry(BaseModel):
    """Pydantic model representing a single language name and level."""

    name: str
    level: str

    @classmethod
    def from_string(cls, s: str) -> "LanguageEntry":
        s = s.strip()
        if ":" in s:
            name_part, level_part = s.split(":", 1)
            name = name_part.strip().strip("*").strip()
            level = level_part.strip()
            return cls(name=name, level=level)
        return cls(name=s, level="")

    def to_string(self) -> str:
        return f"**{self.name}**: {self.level}"


class Language(Section):
    """Pydantic model representing the languages section."""

    name: str = SectionConstant.LANGUAGES
    md_prefix: str = "##"
    languages: list[LanguageEntry] = Field(default_factory=list)

    @classmethod
    def from_string(cls, s: str, filepath: Path | None = None, raw_lines: list[Line] = None) -> "Language":
        lines = [line.strip() for line in s.split("\n") if line.strip()]
        content_lines = []
        for line in lines:
            if line.startswith("## ") and "languages" in line.lower():
                continue
            content_lines.append(line)
        lang_line = " ".join(content_lines).strip()
        lang_parts = [lp.strip() for lp in lang_line.split(",") if lp.strip()]
        languages = [LanguageEntry.from_string(lp) for lp in lang_parts if lp.strip()]
        return cls(
            name=SectionConstant.LANGUAGES,
            md_prefix="##",
            filepath=filepath,
            raw_lines=raw_lines or [],
            languages=languages,
        )

    def to_string(self) -> str:
        lang_strs = [lang.to_string() for lang in self.languages]
        return f"## {SectionConstant.LANGUAGES}\n\n" + ", ".join(lang_strs)


class Degree(BaseModel):
    """Pydantic model representing an education degree, institution, duration, and optional thesis."""

    degree: str
    institution: str
    duration: Duration
    thesis: Thesis | None = None

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


class Education(Section):
    """Pydantic model representing the education section."""

    name: str = SectionConstant.EDUCATION
    md_prefix: str = "##"
    degrees: list[Degree] = Field(default_factory=list)

    @classmethod
    def from_string(cls, s: str, filepath: Path | None = None, raw_lines: list[Line] = None) -> "Education":
        lines = [line.strip() for line in s.split("\n") if line.strip()]
        content_lines = []
        for line in lines:
            if line.startswith("## ") and "education" in line.lower():
                continue
            content_lines.append(line)

        edu_blocks = []
        current_block_lines = []
        for line in content_lines:
            if line.strip().startswith("**") and len(current_block_lines) > 0:
                edu_blocks.append("\n".join(current_block_lines))
                current_block_lines = []
            current_block_lines.append(line)
        if current_block_lines:
            edu_blocks.append("\n".join(current_block_lines))

        degrees = [Degree.from_string(block) for block in edu_blocks]
        return cls(
            name=SectionConstant.EDUCATION,
            md_prefix="##",
            filepath=filepath,
            raw_lines=raw_lines or [],
            degrees=degrees,
        )

    def to_string(self) -> str:
        lines = [f"## {SectionConstant.EDUCATION}", ""]
        for edu in self.degrees:
            lines.append(edu.to_string())
            lines.append("")
        return "\n".join(lines)


class WorkExperienceEntry(BaseModel):
    """Pydantic model representing a work experience entry."""

    title: str
    company: str
    location: str | None = None
    duration: Duration
    bullet_points: list[BulletPoint]
    reason_for_resignation: str | None = None
    skills: list[Skill] | None = None

    @classmethod
    def from_string(cls, s: str) -> "WorkExperienceEntry":
        lines = [line.strip() for line in s.strip().split("\n") if line.strip()]
        if not lines:
            raise ValueError("Empty string for WorkExperienceEntry")

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
                    reason = content[len(prefix) :].strip()
            elif "Skills:" in line_str or line_str.startswith(("- Skills:", "Skills:")):
                skills_part = line_str
                for prefix in ["- Skills:", "* Skills:", "Skills:"]:
                    if skills_part.startswith(prefix):
                        skills_part = skills_part[len(prefix) :].strip()
                        break
                skills_part = skills_part.rstrip(".")
                skill_names = [sk.strip() for sk in skills_part.split(",") if sk.strip()]
                skills = [Skill(text=name) for name in skill_names]
            elif line_str.startswith(("- ", "* ")):
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
        comp_loc_str = f"{self.company}, {self.location}" if self.location else self.company
        lines.append(f"**{self.title}** | _{comp_loc_str}_ | {duration_str}")
        lines.append("")
        lines.extend(bp.to_string() for bp in self.bullet_points)
        if self.skills:
            skills_str = ", ".join(s.to_string() for s in self.skills)
            lines.append(f"- Skills: {skills_str}")
        if self.reason_for_resignation:
            lines.append("")
            lines.append(f"> _Reason for resignation: {self.reason_for_resignation}_")
        return "\n".join(lines)


class WorkExperience(Section):
    """Pydantic model representing the work experience section."""

    name: str = SectionConstant.WORK_EXPERIENCE
    md_prefix: str = "##"
    entries: list[WorkExperienceEntry] = Field(default_factory=list)

    @classmethod
    def from_string(cls, s: str, filepath: Path | None = None, raw_lines: list[Line] = None) -> "WorkExperience":
        lines = s.split("\n")
        content_lines = []
        for line in lines:
            if line.strip().startswith("## ") and "work" in line.lower():
                continue
            content_lines.append(line)

        work_text = "\n".join(content_lines).strip()
        entries = []
        if work_text:
            we_block = []
            for w_line in work_text.split("\n"):
                stripped = w_line.strip()
                if stripped.startswith("**") and " | " in stripped and we_block:
                    entries.append(WorkExperienceEntry.from_string("\n".join(we_block)))
                    we_block = []
                we_block.append(w_line)
            if we_block:
                entries.append(WorkExperienceEntry.from_string("\n".join(we_block)))
        return cls(
            name=SectionConstant.WORK_EXPERIENCE,
            md_prefix="##",
            filepath=filepath,
            raw_lines=raw_lines or [],
            entries=entries,
        )

    def to_string(self) -> str:
        lines = [f"## {SectionConstant.WORK_EXPERIENCE}", ""]
        lines.append("\n\n".join(we.to_string() for we in self.entries))
        return "\n".join(lines)


class PersonalProjectsEntry(BaseModel):
    """Pydantic model representing a personal project entry."""

    name: str
    url: str
    duration: Duration
    bullet_points: list[BulletPoint]
    skills: list[Skill]

    @classmethod
    def from_string(cls, s: str) -> "PersonalProjectsEntry":
        lines = [line.strip() for line in s.strip().split("\n") if line.strip()]
        if not lines:
            raise ValueError("Empty string for PersonalProjectsEntry")

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
            if "Skills:" in line_str or line_str.startswith(("- Skills:", "Skills:")):
                skills_part = line_str
                for prefix in ["- Skills:", "* Skills:", "Skills:"]:
                    if skills_part.startswith(prefix):
                        skills_part = skills_part[len(prefix) :].strip()
                        break
                skills_part = skills_part.rstrip(".")
                skill_names = [sk.strip() for sk in skills_part.split(",") if sk.strip()]
                skills = [Skill(text=name) for name in skill_names]
            elif line_str.startswith(("- ", "* ")):
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
        lines.extend(bp.to_string() for bp in self.bullet_points)
        skills_str = ", ".join(s.to_string() for s in self.skills)
        lines.append(f"- Skills: {skills_str}")
        return "\n".join(lines)


class PersonalProjects(Section):
    """Pydantic model representing the personal projects section."""

    name: str = SectionConstant.PERSONAL_PROJECTS
    md_prefix: str = "##"
    entries: list[PersonalProjectsEntry] = Field(default_factory=list)

    @classmethod
    def from_string(cls, s: str, filepath: Path | None = None, raw_lines: list[Line] = None) -> "PersonalProjects":
        lines = s.split("\n")
        content_lines = []
        for line in lines:
            if line.strip().startswith("## ") and "project" in line.lower():
                continue
            content_lines.append(line)

        project_text = "\n".join(content_lines).strip()
        entries = []
        if project_text:
            pp_block = []
            for p_line in project_text.split("\n"):
                stripped = p_line.strip()
                if stripped.startswith("**") and (" | " in stripped or "[" in stripped) and pp_block:
                    entries.append(PersonalProjectsEntry.from_string("\n".join(pp_block)))
                    pp_block = []
                pp_block.append(p_line)
            if pp_block:
                entries.append(PersonalProjectsEntry.from_string("\n".join(pp_block)))
        return cls(
            name=SectionConstant.PERSONAL_PROJECTS,
            md_prefix="##",
            filepath=filepath,
            raw_lines=raw_lines or [],
            entries=entries,
        )

    def to_string(self) -> str:
        lines = [f"## {SectionConstant.PERSONAL_PROJECTS}", ""]
        lines.append("\n\n".join(pp.to_string() for pp in self.entries))
        return "\n".join(lines)


class CourseOrCertificateEntry(BaseModel):
    """Pydantic model representing a course or certificate entry."""

    name: str
    institution: str
    duration: Duration

    @classmethod
    def from_string(cls, s: str) -> "CourseOrCertificateEntry":
        s = s.strip()
        if s.startswith(("- ", "* ")):
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


class CourseOrCertificate(Section):
    """Pydantic model representing the courses and certificates section."""

    name: str = SectionConstant.COURSES_AND_CERTIFICATES
    md_prefix: str = "##"
    entries: list[CourseOrCertificateEntry] = Field(default_factory=list)

    @classmethod
    def from_string(cls, s: str, filepath: Path | None = None, raw_lines: list[Line] = None) -> "CourseOrCertificate":
        lines = s.split("\n")
        content_lines = []
        for line in lines:
            if line.strip().startswith("## ") and ("course" in line.lower() or "cert" in line.lower()):
                continue
            content_lines.append(line)

        course_text = "\n".join(content_lines).strip()
        entries = []
        if course_text:
            for c_line in course_text.split("\n"):
                stripped = c_line.strip()
                if stripped.startswith(("- ", "* ")):
                    entries.append(CourseOrCertificateEntry.from_string(c_line))
        return cls(
            name=SectionConstant.COURSES_AND_CERTIFICATES,
            md_prefix="##",
            filepath=filepath,
            raw_lines=raw_lines or [],
            entries=entries,
        )

    def to_string(self) -> str:
        lines = [f"## {SectionConstant.COURSES_AND_CERTIFICATES}", ""]
        lines.append("\n".join(cc.to_string() for cc in self.entries))
        return "\n".join(lines)


class Info(Section):
    """Pydantic model representing the personal contact info section."""

    name: str = SectionConstant.INFO
    md_prefix: str = "#"
    address: str = ""
    email: str = ""
    telephone: str = ""
    linkedin: str = ""
    github: str = ""

    @classmethod
    def from_string(cls, s: str, filepath: Path | None = None, raw_lines: list[Line] = None) -> "Info":
        lines = [line.strip() for line in s.strip().split("\n") if line.strip()]

        name = SectionConstant.INFO
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
            md_prefix="#",
            filepath=filepath,
            raw_lines=raw_lines or [],
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


class Header(BaseModel):
    """Pydantic model representing the CV header containing contact information."""

    info_sec: Info = Field(alias="info")

    model_config = {
        "populate_by_name": True,
    }

    @classmethod
    def from_string(cls, s: str) -> "Header":
        info = Info.from_string(s)
        return cls(info=info)

    def to_string(self) -> str:
        return self.info_sec.to_string()

    @property
    def name(self) -> str:
        return self.info_sec.name

    @property
    def address(self) -> str:
        return self.info_sec.address

    @property
    def email(self) -> str:
        return self.info_sec.email

    @property
    def telephone(self) -> str:
        return self.info_sec.telephone

    @property
    def linkedin(self) -> str:
        return self.info_sec.linkedin

    @property
    def github(self) -> str:
        return self.info_sec.github


class Footer(BaseModel):
    """Pydantic model representing the CV footer containing education and languages."""

    education_sec: Education = Field(
        default_factory=lambda: Education(name=SectionConstant.EDUCATION, md_prefix="##"), alias="education"
    )
    language_sec: Language = Field(
        default_factory=lambda: Language(name=SectionConstant.LANGUAGES, md_prefix="##"), alias="language"
    )

    model_config = {
        "populate_by_name": True,
    }

    @classmethod
    def from_string(cls, s: str) -> "Footer":
        from md_tools.parse import split_markdown_into_sections

        sections = split_markdown_into_sections(s)
        edu = Education(name=SectionConstant.EDUCATION, md_prefix="##")
        lang = Language(name=SectionConstant.LANGUAGES, md_prefix="##")

        for sec in sections:
            sec_name = sec.name.lower()
            sec_text = "\n".join(l.raw_line for l in sec.raw_lines)
            if "education" in sec_name:
                edu = Education.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)
            elif "language" in sec_name:
                lang = Language.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)

        return cls(education=edu, language=lang)

    def to_string(self) -> str:
        parts = []
        if self.education_sec and self.education_sec.degrees:
            parts.append(self.education_sec.to_string().strip())
        if self.language_sec and self.language_sec.languages:
            parts.append(self.language_sec.to_string().strip())
        return "\n\n".join(parts) + ("\n" if parts else "")

    @property
    def educations(self) -> list[Degree]:
        return self.education_sec.degrees

    @property
    def languages(self) -> list[LanguageEntry]:
        return self.language_sec.languages


class Body(BaseModel):
    """Pydantic model representing the CV body containing work history, projects, and courses."""

    work_experience_sec: WorkExperience = Field(
        default_factory=lambda: WorkExperience(name=SectionConstant.WORK_EXPERIENCE, md_prefix="##"),
        alias="work_experience",
    )
    personal_projects_sec: PersonalProjects = Field(
        default_factory=lambda: PersonalProjects(name=SectionConstant.PERSONAL_PROJECTS, md_prefix="##"),
        alias="personal_projects",
    )
    courses_and_certificates_sec: CourseOrCertificate = Field(
        default_factory=lambda: CourseOrCertificate(name=SectionConstant.COURSES_AND_CERTIFICATES, md_prefix="##"),
        alias="courses_and_certificates",
    )

    model_config = {
        "populate_by_name": True,
    }

    @classmethod
    def from_string(cls, s: str) -> "Body":
        from md_tools.parse import split_markdown_into_sections

        sections = split_markdown_into_sections(s)
        we = WorkExperience(name=SectionConstant.WORK_EXPERIENCE, md_prefix="##")
        pp = PersonalProjects(name=SectionConstant.PERSONAL_PROJECTS, md_prefix="##")
        cc = CourseOrCertificate(name=SectionConstant.COURSES_AND_CERTIFICATES, md_prefix="##")

        for sec in sections:
            sec_name = sec.name.lower()
            sec_text = "\n".join(l.raw_line for l in sec.raw_lines)
            if "work" in sec_name:
                we = WorkExperience.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)
            elif "project" in sec_name:
                pp = PersonalProjects.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)
            elif "course" in sec_name or "cert" in sec_name:
                cc = CourseOrCertificate.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)

        return cls(work_experience=we, personal_projects=pp, courses_and_certificates=cc)

    def to_string(self) -> str:
        parts = []
        if self.work_experience_sec and self.work_experience_sec.entries:
            parts.append(self.work_experience_sec.to_string().strip())
        if self.personal_projects_sec and self.personal_projects_sec.entries:
            parts.append(self.personal_projects_sec.to_string().strip())
        if self.courses_and_certificates_sec and self.courses_and_certificates_sec.entries:
            parts.append(self.courses_and_certificates_sec.to_string().strip())
        return "\n\n".join(parts) + ("\n" if parts else "")

    @property
    def work_experience(self) -> list[WorkExperienceEntry]:
        return self.work_experience_sec.entries

    @property
    def personal_projects(self) -> list[PersonalProjectsEntry]:
        return self.personal_projects_sec.entries

    @property
    def courses_and_certificates(self) -> list[CourseOrCertificateEntry]:
        return self.courses_and_certificates_sec.entries


class CV(BaseModel):
    """Pydantic model representing the entire CV structure."""

    header: Header | None = None
    summary: Summary | None = None
    skills: SkillGroup | None = None
    body: Body
    footer: Footer | None = None

    @classmethod
    def from_string(cls, s: str) -> "CV":
        from md_tools.parse import split_markdown_into_sections

        sections = split_markdown_into_sections(s)

        info = None
        summary = None
        skills = None

        we = WorkExperience(name=SectionConstant.WORK_EXPERIENCE, md_prefix="##")
        pp = PersonalProjects(name=SectionConstant.PERSONAL_PROJECTS, md_prefix="##")
        cc = CourseOrCertificate(name=SectionConstant.COURSES_AND_CERTIFICATES, md_prefix="##")

        edu = Education(name=SectionConstant.EDUCATION, md_prefix="##")
        lang = Language(name=SectionConstant.LANGUAGES, md_prefix="##")

        for sec in sections:
            sec_name = sec.name.lower()
            sec_text = "\n".join(l.raw_line for l in sec.raw_lines)

            if sec.md_prefix == "#":
                info = Info.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)
            elif "summary" in sec_name:
                summary = Summary.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)
            elif "skills" in sec_name:
                skills = SkillGroup.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)
            elif "work" in sec_name:
                we = WorkExperience.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)
            elif "project" in sec_name:
                pp = PersonalProjects.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)
            elif "course" in sec_name or "cert" in sec_name:
                cc = CourseOrCertificate.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)
            elif "education" in sec_name:
                edu = Education.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)
            elif "language" in sec_name:
                lang = Language.from_string(sec_text, filepath=sec.filepath, raw_lines=sec.raw_lines)

        header = Header(info=info) if info else None
        body = Body(work_experience=we, personal_projects=pp, courses_and_certificates=cc)
        footer = Footer(education=edu, language=lang) if (edu.degrees or lang.languages) else None

        return cls(header=header, summary=summary, skills=skills, body=body, footer=footer)

    def to_string(self) -> str:
        parts = []
        if self.header:
            parts.append(self.header.to_string().strip())
        if self.summary:
            parts.append(self.summary.to_string().strip())
        if self.skills:
            parts.append(self.skills.to_string().strip())
        if self.body:
            parts.append(self.body.to_string().strip())
        if self.footer:
            parts.append(self.footer.to_string().strip())
        return "\n\n".join(parts) + "\n"
