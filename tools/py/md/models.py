"""Pydantic models representing structured sections and elements of a CV.

NOTE: This models are pure Markdown based and do not use any LaTeX or other formatting.

"""

import re
from pathlib import Path

from pydantic import BaseModel, Field

from md.parse import Heading, IndexedLine, Section, split_markdown_into_sections

_REGEXP_URL_GROUP = re.compile(r"\[(?P<text>.*?)\]\((?P<url>.*?)\)")
_REGEXP_MARKDOWN_STYLE = re.compile(r"^[*_-]+|[*_-]+$")


class TextConstant:
    PIPE = "|"
    COMMA = ","
    THESIS = "Thesis"
    HEADER1 = "#"
    HEADER2 = "##"


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


def is_root_section(sec: Section) -> bool:
    return sec.heading.heading_prefix == TextConstant.HEADER1


def clean_markdown_style(text: str) -> str:
    return _REGEXP_MARKDOWN_STYLE.sub("", text.strip()).strip()


class Duration(BaseModel):
    """Pydantic model representing duration with optional start date and end date."""

    start_date: str | None = None
    end_date: str

    @classmethod
    def from_string(cls, s: str) -> "Duration":
        s = s.strip()
        separators = ["to", "-"]
        for sep in separators:
            if sep in s:
                parts = s.split(sep, 1)
                return cls(start_date=parts[0].strip(), end_date=parts[1].strip())
        return cls(start_date=None, end_date=s)

    def to_string(self) -> str:
        if self.start_date:
            return f"{self.start_date} - {self.end_date}"
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

    heading: Heading = Field(
        default_factory=lambda: Heading(
            text=SectionConstant.SUMMARY,
            heading_prefix=TextConstant.HEADER2,
        ),
    )
    text: str = ""

    @classmethod
    def from_string(
        cls, s: str, filepath: Path | None = None, indexed_lines: list[IndexedLine] | None = None
    ) -> "Summary":
        """Parse summary section from a markdown string."""
        section = split_markdown_into_sections(s, filepath=filepath)[0]

        if not indexed_lines:
            indexed_lines = section.indexed_lines

        return cls(
            heading=section.heading,
            filepath=filepath,
            indexed_lines=indexed_lines,
            text="\n".join(l.line for l in section.indexed_lines if not l.line.startswith("#")).strip(),
        )

    def to_string(self) -> str:
        return f"{self.heading.heading_prefix} {self.heading.text}\n\n{self.text}"


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
            skills_list = [Skill.from_string(sk) for sk in skills_part.split(TextConstant.COMMA) if sk.strip()]
            return cls(name=name, skills=skills_list)
        return cls(name="", skills=[Skill.from_string(s)])

    def to_string(self) -> str:
        skills_str = ", ".join(sk.to_string() for sk in self.skills)
        return f"**{self.name}**: {skills_str}  "


class SkillGroup(Section):
    """Pydantic model representing a skills section containing a list of skill groups."""

    heading: Heading = Field(
        default_factory=lambda: Heading(text=SectionConstant.SKILLS, heading_prefix=TextConstant.HEADER2)
    )
    groups: list[SkillGroupEntry] = Field(default_factory=list)

    @classmethod
    def from_string(
        cls, s: str, filepath: Path | None = None, indexed_lines: list[IndexedLine] | None = None
    ) -> "SkillGroup":
        """Parse skill group section from a markdown string."""
        section = split_markdown_into_sections(s, filepath=filepath)[0]
        if not indexed_lines:
            indexed_lines = section.indexed_lines

        groups_list = []
        for l in section.indexed_lines:
            line_str = l.line
            if line_str.startswith("#"):
                continue
            if not line_str.strip():
                continue
            groups_list.append(SkillGroupEntry.from_string(line_str))

        return cls(
            heading=section.heading,
            filepath=filepath,
            indexed_lines=indexed_lines,
            groups=groups_list,
        )

    def to_string(self) -> str:
        groups_str = "\n".join(g.to_string() for g in self.groups)
        return f"{self.heading.heading_prefix} {self.heading.text}\n\n{groups_str}"


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

    heading: Heading = Field(
        default_factory=lambda: Heading(text=SectionConstant.LANGUAGES, heading_prefix=TextConstant.HEADER2)
    )
    languages: list[LanguageEntry] = Field(default_factory=list)

    @classmethod
    def from_string(
        cls, s: str, filepath: Path | None = None, indexed_lines: list[IndexedLine] | None = None
    ) -> "Language":
        """Parse language section from a markdown string."""
        section = split_markdown_into_sections(s, filepath=filepath)[0]
        if not indexed_lines:
            indexed_lines = section.indexed_lines

        lang_line = " ".join(l.line for l in section.indexed_lines if not l.line.startswith("#")).strip()
        lang_parts = [lp.strip() for lp in lang_line.split(TextConstant.COMMA) if lp.strip()]
        languages = [LanguageEntry.from_string(lp) for lp in lang_parts if lp.strip()]
        return cls(
            heading=section.heading,
            filepath=filepath,
            indexed_lines=indexed_lines,
            languages=languages,
        )

    def to_string(self) -> str:
        lang_strs = [lang.to_string() for lang in self.languages]
        return f"{self.heading.heading_prefix} {self.heading.text}\n\n" + ", ".join(lang_strs)


class Degree(BaseModel):
    """Pydantic model representing an education degree, institution, duration, and optional thesis."""

    degree: str
    institution: str
    duration: Duration
    thesis: Thesis | None = None

    @classmethod
    def from_string(cls, s: str) -> "Degree":
        lines = s.strip().splitlines()
        if not lines:
            raise ValueError("Empty string for Degree")

        header_line = lines[0]
        parts = header_line.split(TextConstant.PIPE)
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
        for line in s.splitlines()[1:]:
            if TextConstant.THESIS in line or "thesis" in line.lower():
                thesis = Thesis.from_string(line)
                break

        return cls(degree=degree, institution=institution, duration=duration, thesis=thesis)

    def to_string(self) -> str:
        duration_str = self.duration.to_string()
        lines = [f"**{self.degree}** | _{self.institution}_ | {duration_str}"]
        if self.thesis:
            lines.append("")
            lines.append(self.thesis.to_string())
        return "\n".join(lines)


class Education(Section):
    """Pydantic model representing the education section."""

    heading: Heading = Field(
        default_factory=lambda: Heading(text=SectionConstant.EDUCATION, heading_prefix=TextConstant.HEADER2)
    )
    degrees: list[Degree] = Field(default_factory=list)

    @classmethod
    def from_string(
        cls, s: str, filepath: Path | None = None, indexed_lines: list[IndexedLine] | None = None
    ) -> "Education":
        """Parse education section from a markdown string."""
        sections = split_markdown_into_sections(s, filepath=filepath)
        section = sections[0]

        title_text = section.heading.text
        title_prefix = section.heading.heading_prefix

        if not indexed_lines:
            indexed_lines = section.indexed_lines

        content_lines = section.lines[1:]

        edu_blocks = []
        current_block_lines = []
        for line in content_lines:
            if line.strip().startswith("**") and len(current_block_lines) > 0:
                edu_blocks.append("\n".join(current_block_lines))
                current_block_lines = []
            current_block_lines.append(line)
        if current_block_lines:
            edu_blocks.append("\n".join(current_block_lines))

        degrees = [Degree.from_string(block) for block in edu_blocks if block.strip()]
        return cls(
            heading=Heading(text=title_text, heading_prefix=title_prefix),
            filepath=filepath,
            indexed_lines=indexed_lines,
            degrees=degrees,
        )

    def to_string(self) -> str:
        lines = [f"{self.heading.heading_prefix} {self.heading.text}", ""]
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
        lines = s.strip().splitlines()
        if not lines:
            raise ValueError("Empty string for WorkExperienceEntry")

        header_line = lines[0]
        parts = header_line.split(TextConstant.PIPE)
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {parts}"

        title = clean_markdown_style(parts[0])
        company_loc = clean_markdown_style(parts[1])
        duration_str = clean_markdown_style(parts[2])

        # Split on the first comma to support company and location
        company = company_loc
        location = None
        if TextConstant.COMMA in company_loc:
            c_part, l_part = company_loc.split(TextConstant.COMMA, 1)
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
                skill_names = [sk.strip() for sk in skills_part.split(TextConstant.COMMA) if sk.strip()]
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

    heading: Heading = Field(
        default_factory=lambda: Heading(text=SectionConstant.WORK_EXPERIENCE, heading_prefix=TextConstant.HEADER2)
    )
    entries: list[WorkExperienceEntry] = Field(default_factory=list)

    @classmethod
    def from_string(
        cls, s: str, filepath: Path | None = None, indexed_lines: list[IndexedLine] | None = None
    ) -> "WorkExperience":
        """Parse work experience section from a markdown string."""
        section = split_markdown_into_sections(s, filepath=filepath)[0]

        title_text = section.heading.text
        title_prefix = section.heading.heading_prefix

        indexed_lines = indexed_lines or section.indexed_lines

        content_lines = section.lines[1:]

        work_text = "\n".join(content_lines).strip()
        entries = []
        we_block = []
        for w_line in work_text.splitlines():
            stripped = w_line.strip()
            if stripped.startswith("**") and TextConstant.PIPE in stripped and we_block:
                entries.append(WorkExperienceEntry.from_string("\n".join(we_block)))
                we_block = []
            we_block.append(w_line)
        if we_block:
            entries.append(WorkExperienceEntry.from_string("\n".join(we_block)))
        return cls(
            heading=Heading(text=title_text, heading_prefix=title_prefix),
            filepath=filepath,
            indexed_lines=indexed_lines,
            entries=entries,
        )

    def to_string(self) -> str:
        lines = [f"{self.heading.heading_prefix} {self.heading.text}", ""]
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
        lines = s.splitlines()
        if not lines:
            raise ValueError("Empty string for PersonalProjectsEntry")

        header_line = lines[0]
        if TextConstant.PIPE in header_line:
            left, right = header_line.split(TextConstant.PIPE, 1)
            link_part = left.strip().strip("*").strip()
            duration_str = right.strip()
        else:
            link_part = header_line.strip().strip("*").strip()
            duration_str = ""

        name = link_part
        url = ""
        match_url = _REGEXP_URL_GROUP.search(link_part)
        if match_url:
            name = match_url.group("text").strip()
            url = match_url.group("url").strip()

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
                skill_names = [sk.strip() for sk in skills_part.split(TextConstant.COMMA) if sk.strip()]
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

    heading: Heading = Field(
        default_factory=lambda: Heading(text=SectionConstant.PERSONAL_PROJECTS, heading_prefix=TextConstant.HEADER2)
    )
    entries: list[PersonalProjectsEntry] = Field(default_factory=list)

    @classmethod
    def from_string(
        cls, s: str, filepath: Path | None = None, indexed_lines: list[IndexedLine] | None = None
    ) -> "PersonalProjects":
        """Parse personal projects section from a markdown string."""
        section = split_markdown_into_sections(s, filepath=filepath)[0]

        title_text = section.heading.text
        title_prefix = section.heading.heading_prefix

        if not indexed_lines:
            indexed_lines = section.indexed_lines

        content_lines = section.lines[1:]

        project_text = "\n".join(content_lines).strip()
        entries = []
        if project_text:
            pp_block = []
            for p_line in project_text.splitlines():
                stripped = p_line.strip()
                if stripped.startswith("**") and TextConstant.PIPE in stripped and pp_block:
                    entries.append(PersonalProjectsEntry.from_string("\n".join(pp_block)))
                    pp_block = []
                pp_block.append(p_line)
            if pp_block:
                entries.append(PersonalProjectsEntry.from_string("\n".join(pp_block)))
        return cls(
            heading=Heading(text=title_text, heading_prefix=title_prefix),
            filepath=filepath,
            indexed_lines=indexed_lines,
            entries=entries,
        )

    def to_string(self) -> str:
        lines = [f"{self.heading.heading_prefix} {self.heading.text}", ""]
        lines.append("\n\n".join(pp.to_string() for pp in self.entries))
        return "\n".join(lines)


class CourseOrCertificateEntry(BaseModel):
    """Pydantic model representing a course or certificate entry."""

    name: str
    institution: str
    duration: Duration

    @classmethod
    def from_string(cls, s: str) -> "CourseOrCertificateEntry":
        lines = s.splitlines()
        assert lines
        first_line = lines[0].strip()
        if first_line.startswith(("- ", "* ")):
            first_line = first_line[2:].strip()

        parts = first_line.split(TextConstant.PIPE)
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}"
        name = clean_markdown_style(parts[0])
        institution = clean_markdown_style(parts[1])
        duration = Duration.from_string(parts[2].strip())
        return cls(name=name, institution=institution, duration=duration)

    def to_string(self) -> str:
        duration_str = self.duration.to_string()
        return f"- {self.name} | _{self.institution}_ | {duration_str}"


class CourseOrCertificate(Section):
    """Pydantic model representing the courses and certificates section."""

    heading: Heading = Field(
        default_factory=lambda: Heading(
            text=SectionConstant.COURSES_AND_CERTIFICATES, heading_prefix=TextConstant.HEADER2
        )
    )
    entries: list[CourseOrCertificateEntry] = Field(default_factory=list)

    @classmethod
    def from_string(
        cls, s: str, filepath: Path | None = None, indexed_lines: list[IndexedLine] | None = None
    ) -> "CourseOrCertificate":
        """Parse courses and certificates section from a markdown string."""
        section = split_markdown_into_sections(s, filepath=filepath)[0]
        title_text = section.heading.text
        title_prefix = section.heading.heading_prefix

        if not indexed_lines and section:
            indexed_lines = section.indexed_lines

        content_lines = section.lines[1:]

        course_text = "\n".join(content_lines).strip()
        entries = []
        if course_text:
            for c_line in course_text.splitlines():
                stripped = c_line.strip()
                if stripped.startswith(("- ", "* ")):
                    entries.append(CourseOrCertificateEntry.from_string(c_line))
        return cls(
            heading=Heading(text=title_text, heading_prefix=title_prefix),
            filepath=filepath,
            indexed_lines=indexed_lines,
            entries=entries,
        )

    def to_string(self) -> str:
        lines = [f"{self.heading.heading_prefix} {self.heading.text}", ""]
        lines.append("\n".join(cc.to_string() for cc in self.entries))
        return "\n".join(lines)


class Info(Section):
    """Pydantic model representing the personal contact info section."""

    heading: Heading = Field(default_factory=lambda: Heading(text=SectionConstant.INFO, heading_prefix="#"))
    address: str = ""
    email: str = ""
    telephone: str = ""
    linkedin: str = ""
    github: str = ""

    @classmethod
    def from_string(
        cls, s: str, filepath: Path | None = None, indexed_lines: list[IndexedLine] | None = None
    ) -> "Info":
        """Parse contact info section from a markdown string."""
        section = split_markdown_into_sections(s, filepath=filepath)[0]

        title_text = section.heading.text
        title_prefix = section.heading.heading_prefix

        if not indexed_lines and section:
            indexed_lines = section.indexed_lines

        address = ""
        email = ""
        telephone = ""
        linkedin = ""
        github = ""

        def get_md_link_url(text: str) -> str:
            match = _REGEXP_URL_GROUP.search(text)
            assert match is not None
            return match.group("url").strip()

        if section:
            for l in section.indexed_lines:
                line = l.line
                if line.strip().startswith(title_prefix) or "---" in line:
                    continue
                if "|" in line:
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
            heading=Heading(text=title_text, heading_prefix=title_prefix),
            filepath=filepath,
            indexed_lines=indexed_lines,
            address=address,
            email=email,
            telephone=telephone,
            linkedin=linkedin,
            github=github,
        )

    def to_string(self) -> str:
        lines = []
        lines.append(f"{self.heading.heading_prefix} {self.heading.text}")
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
    def from_string(
        cls, s: str, filepath: Path | None = None, indexed_lines: list[IndexedLine] | None = None
    ) -> "Header":
        """Parse CV header from a markdown string."""
        lines = s.splitlines()
        info = Info.from_string("\n".join(lines), filepath=filepath, indexed_lines=indexed_lines)
        return cls(info=info)

    def to_string(self) -> str:
        return self.info_sec.to_string()

    @property
    def name(self) -> str:
        return self.info_sec.heading.text

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

    education_sec: Education = Field(default_factory=Education, alias="education")
    language_sec: Language = Field(default_factory=Language, alias="language")

    model_config = {
        "populate_by_name": True,
    }

    @classmethod
    def from_string(
        cls, s: str, filepath: Path | None = None, indexed_lines: list[IndexedLine] | None = None
    ) -> "Footer":
        """Parse CV footer from a markdown string."""
        sections = split_markdown_into_sections(s, filepath=filepath)
        assert len(sections) == 2, f"Only two sections supported in footer. Found: {len(sections)}"
        edu_sec, lang_sec = sections
        edu = Education.from_string(str(edu_sec), filepath=filepath, indexed_lines=edu_sec.indexed_lines)
        lang = Language.from_string(str(lang_sec), filepath=filepath, indexed_lines=lang_sec.indexed_lines)

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
        default_factory=WorkExperience,
        alias="work_experience",
    )
    personal_projects_sec: PersonalProjects = Field(
        default_factory=PersonalProjects,
        alias="personal_projects",
    )
    courses_and_certificates_sec: CourseOrCertificate = Field(
        default_factory=CourseOrCertificate,
        alias="courses_and_certificates",
    )

    model_config = {
        "populate_by_name": True,
    }

    @classmethod
    def from_string(
        cls, s: str, filepath: Path | None = None, indexed_lines: list[IndexedLine] | None = None
    ) -> "Body":
        """Parse CV body from a markdown string."""
        sections = split_markdown_into_sections(s)
        we = WorkExperience(filepath=filepath, indexed_lines=indexed_lines)
        pp = PersonalProjects(filepath=filepath, indexed_lines=indexed_lines)
        cc = CourseOrCertificate(filepath=filepath, indexed_lines=indexed_lines)

        for sec in sections:
            sec_name = sec.heading.text.lower()
            sec_text = "\n".join(l.line for l in sec.indexed_lines)
            if sec_name == SectionConstant.WORK_EXPERIENCE.lower():
                we = WorkExperience.from_string(sec_text, filepath=sec.filepath, indexed_lines=sec.indexed_lines)
            elif sec_name == SectionConstant.PERSONAL_PROJECTS.lower():
                pp = PersonalProjects.from_string(sec_text, filepath=sec.filepath, indexed_lines=sec.indexed_lines)
            elif sec_name == SectionConstant.COURSES_AND_CERTIFICATES.lower():
                cc = CourseOrCertificate.from_string(sec_text, filepath=sec.filepath, indexed_lines=sec.indexed_lines)

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
    def from_string(cls, s: str, filepath: Path | None = None, indexed_lines: list[IndexedLine] | None = None) -> "CV":
        """Parse entire CV from a markdown string."""
        sections = split_markdown_into_sections(s)

        info = None
        summary = None
        skills = None

        we = WorkExperience()
        pp = PersonalProjects()
        cc = CourseOrCertificate()

        edu = Education()
        lang = Language()

        for sec in sections:
            sec_name = sec.heading.text.lower()
            sec_text = "\n".join(l.line for l in sec.indexed_lines)

            if sec.heading.heading_prefix == "#":
                info = Info.from_string(sec_text, filepath=sec.filepath, indexed_lines=sec.indexed_lines)
            elif sec_name == SectionConstant.SUMMARY.lower():
                summary = Summary.from_string(sec_text, filepath=sec.filepath, indexed_lines=sec.indexed_lines)
            elif sec_name == SectionConstant.SKILLS.lower():
                skills = SkillGroup.from_string(sec_text, filepath=sec.filepath, indexed_lines=sec.indexed_lines)
            elif sec_name == SectionConstant.WORK_EXPERIENCE.lower():
                we = WorkExperience.from_string(sec_text, filepath=sec.filepath, indexed_lines=sec.indexed_lines)
            elif sec_name == SectionConstant.PERSONAL_PROJECTS.lower():
                pp = PersonalProjects.from_string(sec_text, filepath=sec.filepath, indexed_lines=sec.indexed_lines)
            elif sec_name == SectionConstant.COURSES_AND_CERTIFICATES.lower():
                cc = CourseOrCertificate.from_string(sec_text, filepath=sec.filepath, indexed_lines=sec.indexed_lines)
            elif sec_name == SectionConstant.EDUCATION.lower():
                edu = Education.from_string(sec_text, filepath=sec.filepath, indexed_lines=sec.indexed_lines)
            elif sec_name == SectionConstant.LANGUAGES.lower():
                lang = Language.from_string(sec_text, filepath=sec.filepath, indexed_lines=sec.indexed_lines)

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
            parts.append(self.skills.to_string())  # No strip - skills can contain trailing spaces
        if self.body:
            parts.append(self.body.to_string().strip())
        if self.footer:
            parts.append(self.footer.to_string().strip())
        return "\n\n".join(parts) + "\n"


def parse(text: str) -> CV:
    """Parse CV markdown text into a CV Pydantic model.

    Args:
        text: The raw markdown content of the CV.

    Returns:
        CV: The parsed CV Pydantic model.

    """
    return CV.from_string(text)
