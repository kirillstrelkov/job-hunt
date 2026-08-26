# How to create resume with Markdown

## Split your resume

Split your resume into 3 pars:

- Header - contains personal and contact information
- Body - contains information that might change due based on job description
- Footer - contains information about education and languages

Why? - Header and footer usually same for resumes only body is changed/tailored to each job description,
you can safely paste body to AI tool without giving any personal information.

### Header

```markdown
# John Doe

Berlin, Germany | <john.doe@example.com> | +49 123 4567890
[linkedin.com/in/johndoe](https://www.linkedin.com/in/johndoe/) | [github.com/johndoe](https://github.com/johndoe)

---
```

Last horizontal line is optional

### Body

Possible sections:

- Summary
- Skills
- Work experience
- Personal projects
- Courses and certificates

```markdown
## Summary

Software Engineer with extensive experience developing backend systems, microservices, and automated testing frameworks. Proven track record of optimizing build infrastructure, managing containerized deployments, and scaling applications using Go, Docker, and Kubernetes. Experienced with relational databases like PostgreSQL and MySQL, as well as NoSQL solutions like MongoDB. Skilled in troubleshooting, debugging, and collaborating across distributed teams to ship reliable solutions.

## Skills

**Languages**: Go, Python, TypeScript, JavaScript, C, C++, Ruby  
**Cloud & Infrastructure**: Docker, Kubernetes, AWS, Google Kubernetes Engine (GKE), CI/CD, microservices  
**Databases**: PostgreSQL, MySQL, MongoDB, Redis, SQLite  
**Frameworks & Tools**: gRPC, REST, Bazel, GitHub Actions, GraphQL, Jenkins

## Work experience

**Senior Software Engineer** | _Global Tech Solutions Inc., Berlin, Germany_ | Jan 2024 - Present

- Lead the development of distributed backend services using Python, Go, and PostgreSQL
- Architect and maintain robust CI/CD pipelines utilizing GitHub Actions, Docker, and Kubernetes
- Optimize application performance, reducing API response times by 35% through query optimization and caching
- Mentor junior and mid-level engineers, establishing coding standards and conducting regular code reviews
- Skills: Python, Go, Docker, Kubernetes, PostgreSQL, Git, CI/CD, AWS

**Software Engineer** | _Innovate Web Corp, Munich, Germany_ | Jun 2021 - Dec 2023

...

## Personal projects

**[Cloud-Native API Gateway](https://github.com/johndoe/cloud-gateway)** | Jun 2025

- Built a high-performance API gateway in Go supporting rate limiting, request forwarding, and JWT authentication
- Configured automated deployment manifests for Kubernetes clusters using Helm
- Skills: Go, Kubernetes, Helm, Docker, JWT

...

## Courses and certificates

- Certified Kubernetes Application Developer | _Cloud Native Computing Foundation_ | Feb 2026
- Advanced System Design & Architecture | _Coursera_ | 2024
  ...
```

### Footer

```markdown
## Education

**Bachelor of Science in Computer Science** | _Technical University of Munich, Germany_ | Sep 2010 - Jun 2014

- Thesis: [Automated web test framework development](https://example.com/thesis.pdf)

## Languages

**English**: Native, **German**: B2 (Upper Intermediate), **Spanish**: A2 (Elementary)
```

## TODO

- use | to split into group - comma, is bad
- \break
- \hfill
- issues with non egnlish chars
- use pandoc with latext support for formatting
- add screenshots
