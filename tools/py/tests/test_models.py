"""Tests for CV tailoring Pydantic models."""

from pydantic_ai import Agent

from helpers.llm.gemini import _get_agent as get_gemini_agent
from helpers.llm.ollama import _get_agent as get_ollama_agent
from helpers.models import TailoredCVBody


def test_tailored_cv_parsing() -> None:
    """Test that a complete tailored CV parses successfully into Pydantic models."""
    sample_cv_data = {
        "summary": (
            "Highly motivated Software Engineer with robust experience architecting scalable, "
            "fault-tolerant infrastructure and enterprise tooling using C/C++, Rust, and Python."
        ),
        "skills": {
            "languages": ["Golang", "C", "C++", "Rust", "Python", "Java", "Kotlin", "Ruby", "SQL"],
            "databases_and_brokers": ["PostgreSQL", "MySQL", "Kafka", "NATS"],
            "infrastructure_and_cloud": ["Docker", "Kubernetes", "Google Kubernetes Engine (GKE)", "ArgoCD", "Helm"],
            "ci_cd_and_testing": ["Bazel", "GitHub Actions", "Jenkins", "Robot Framework", "OpenHTF", "Django"],
            "observability_and_apis": ["Prometheus", "Kibana", "Elasticsearch", "gRPC", "GraphQL", "REST"],
        },
        "work_experience": [
            {
                "title": "Software Engineer",
                "company": "CARIAD SE",
                "location": "Berlin, Germany",
                "dates": "Oct 2023 - Aug 2025",
                "bullet_points": [
                    "Engineered and maintained fault-tolerant build infrastructure and CI/CD "
                    "pipelines using Bazel, Python, and GitHub Actions to streamline enterprise-scale "
                    "software operations."
                ],
            }
        ],
        "projects": [
            {
                "name": "University of Helsinki DevOps Labs: Cloud-Native Microservices",
                "url": "https://github.com/kirillstrelkov/KubernetesSubmissions",
                "year": "2026",
                "bullet_points": [
                    "Developed a distributed, event-driven microservices application in Golang, "
                    "utilizing NATS as a message broker to asynchronously trigger notifications, "
                    "with state managed in PostgreSQL."
                ],
                "skills": ["Golang", "Kubernetes", "GKE", "NATS", "Prometheus", "PostgreSQL", "Helm", "Docker"],
            }
        ],
        "courses_and_certificates": [
            {
                "name": "Apache Kafka Fundamentals",
                "provider": "Confluent",
                "date": "May 2026",
            }
        ],
        "justification_report": {
            "reductions_and_omissions": [
                "Roles Removed: Completely removed the 'Junior Developer' and 'Tester' roles as strictly requested."
            ],
            "selections": [
                "Projects: Selected the 'Helsinki Cloud-Native Microservices' and 'Golang Web Services Playground'."
            ],
        },
        "additional_options": {
            "work_experience_overflow": [
                {
                    "role_identifier": "Software Engineer | CARIAD SE",
                    "bullet_point": "Created automated packaging and distribution tools for internal Python libraries.",
                }
            ],
            "courses_and_certificates_overflow": [
                {
                    "name": "Apache Flink Fundamentals",
                    "provider": "Confluent",
                    "date": "May 2026",
                    "description": "Highly relevant for stream processing requirements.",
                }
            ],
            "projects_overflow": [
                {
                    "name": "Csv2qif",
                    "url": "https://github.com/kirillstrelkov/csv2qif",
                    "year": "2020",
                    "bullet_points": [
                        "Engineered a high-performance, multithreaded CLI tool using Rust and "
                        "Rayon to parse and process large datasets."
                    ],
                    "skills": ["Rust", "Multithreading", "Data Transformation"],
                }
            ],
        },
    }

    # Verify parsing works without exceptions
    cv = TailoredCVBody(**sample_cv_data)

    # Asset fields match
    assert cv.summary.startswith("Highly motivated Software Engineer")
    assert "Golang" in cv.skills.languages
    assert cv.work_experience[0].company == "CARIAD SE"
    assert cv.projects[0].name.startswith("University of Helsinki DevOps Labs")
    assert cv.courses_and_certificates[0].provider == "Confluent"
    assert len(cv.justification_report.reductions_and_omissions) == 1
    assert cv.additional_options.courses_and_certificates_overflow[0].name == "Apache Flink Fundamentals"


def test_get_agent_gemini() -> None:
    """Test that get_agent for Gemini returns a valid Agent."""
    agent = get_gemini_agent("gemini-2.5-flash", TailoredCVBody, "test system prompt")
    assert isinstance(agent, Agent)
    assert agent.output_type == TailoredCVBody


def test_get_agent_ollama() -> None:
    """Test that get_agent for Ollama returns a valid Agent."""
    agent = get_ollama_agent("gemma4:e2b", TailoredCVBody, "test system prompt")
    assert isinstance(agent, Agent)
    assert agent.output_type == TailoredCVBody
