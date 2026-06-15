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
## Work experience

**Software Engineer** | _CARIAD SE, Berlin, Germany_ | Oct 2023 \- Aug 2025

- Support build infrastructure with Bazel, Python scripting and GitHub Actions
- Slack firefighting and support for developers
- Bazel update from 5 to 6 version and document all findings
- Bazel profiling analysis in order to find best options/flags to improve overall build performance
- doxygen toolchain integration to Bazel target to have approach for all team for document generation
- Python improvements for testing, packaging, ZipApps
- Added Python project support to automatically upload Python packages to Artifactory
- Added ZipApp support to Bazel which gave an option to easy distribute Python projects
- Implemented Python version bumper tool to automate version updates based on Conventional commits
- Small fixes for conan packages
- Development environment support and improvements
- GitHub Actions workflows/job statistics using Python
- Integration version bumper into CI and release process
- GitHub Actions workflows support
- Conducted multiple Demos/workshops: Python package creation, Python project, version bumper, git rebase, bazel profiling
- Classic AUTOSAR development with C
- Optimized and upgraded core build infrastructure by successfully updating Bazel from Version 5 to Version 6, implementing performance enhancements through in-depth profiling analysis and integrating essential toolchains such as Doxygen and Conan to streamline build consistency and dependency management.
- Developed and enhanced CI/CD workflows by creating and maintaining robust pipelines and GitHub Actions workflows, including a custom Python-based Version Bumper tool that automated component version updates and integrated into critical release processes.
- Led Python development for critical internal tooling and automation, managing tests, packaging and ZipApp support and engineering tools for GitHub Actions statistics, significantly contributing to over 50 closed pull requests across core repositories.
- Contributed to Classic AUTOSAR embedded backend development using C/C++, involving timeclient development with EBtresos and setting up Robot Framework and Codebeamer test cases, while simultaneously providing comprehensive technical support and conducting workshops on Git and Bazel for team development and efficiency
- Skills: Python, Bazel, Conan, Docker, Linux, JIRA, Confluence, git, VSCode, C

_Reason for resignation: switch to wrong project and layoffs_

**Software Engineer** | _Argo AI GmbH, Munich, Germany_ | Feb 2022 \- Oct 2023

- Developed framework based on OpenHTF for testing hardware and flashing firmware in autonomous vehicle
- Improved log reviewing process by creating log viewer web application
- Supported vehicle preparation activities at the customer site with external and internal teams - for this received Argo Sport Award
- Support and improve testing framework base on OpenHTF which is used for testing hardware on autonomous vehicle
- Improve log reviewing process by creating log viewer web app
- Support vehicle preparation activities at customer site
- Separate web app for parsing OpenHTF logs
- Participate in car preparation process(flash proper software and check that devices are working as expected with our smoke tests)
- Learn about hardware that is used by the company, car networking/wiring, devices(sensors, cameras and lidars)
- Understand how our software is used with integration team
- Collect feedback from integration team and use it to improve our software
- Got Python readership \- can review any Python code is company code base
- Argo Spot Bonus for support and effort to finalize the automatization tool working in close collaboration with the integration team
- buddy for team mate \- support via slack and multiple online debugging sessions
- Expanded smoke test coverage from 33% to 78%.
- Boosted automated flashing processes for sensors, radar and lidar systems up to 86%
- Skills: Angular, TypeScript, Python, bazel, Docker, macOS, Linux, JIRA, Confluence, git, VSCode, pydantic

_Reason for resignation: company shut down_

**Integration Engineer** | _Airbus Operations GmbH, Hamburg, Germany_ | Aug 2019 \- Feb 2021

- Write, review, document software integration tests for cabin intercommunication data systems.
- Create Python script to automate review process
- Investigated Linux support for LDRA and test cases
- Test performance optimization for Windows and Linux
- Skills: C, Python, batch, ClearCase, ClearQuest, DOORS, LDRA, JIRA, Confluence, git, Eclipse, VSCode

_Reason for resignation: 80% management work and COVID layoffs_

**Software Test Engineer** | _ESR Labs AG, Munich, Germany_ | Sep 2018 \- Apr 2019

- Develop, refactor and improve Ruby internal framework for testing automotive gateway
- Improve quality of the source code by introducing static code analysis into continuous integration pipeline(Jenkins)
- Develop, refactor and improve internal testing framework.
- Trainings:
  - Trace32
  - Functional Safety for software development
- Skills: Ruby, rspec, bundler, rubocop, simplecov, thor, ffi, rainbow, yard, childprocess, fakefs, git, gerrit, RubyMine, macOS, Windows, Linux, Jenkins. JIRA, Slack

_Reason for resignation: my partner found a job in Hamburg_

**Software Test Engineer** | _HERE Deutschland GmbH, Berlin, Germany_ | Mar 2016 \- Aug 2018

- Testing and DevOps activities within Agile/Scrum development of Map Matching algorithm team
- Improved quality by adding additional functional tests(functional tests 16 \-\> 290\)
- Optimize JIRA bug handling process, end to end testing using Python scripts
- Develop Django web application to store and query recorded traces and async process of these traces using Celery framework
- Helped to create initial KPIs for libraries
- Weekly end-to-end regression testing
- Field testing and data collection for further algorithm improvement
- Organize team’s Jenkins jobs to utilize Python/bash scripts used in Docker images
- Share knowledge via Confluence and keeping documentation up-to-date
- Additional
  - small UI fixes for C++ app
  - Created Python scripts for log extraction, log converions to use in automation pipelines
  - groovy CI jobs using Pipeline plugin to store CI scripts under version control
  - Helped with migration from C++ CppUnit to Google Test
  - Created Python scripts for report generation and integrated into CI so it would be easier for developer to compare multiple versions of algorithms
  - Created infrastructure between HIL and CI in order to play recorded trace and get camera video of the real hardwave
  - Used gitlfs to store binary data efficiently
  - Created separate Docker image for team's usage with preinstall/prebuilt internal tools these images used by developer and in CI to get same environment
  - Added support for linters \- html, css, javascript, python, ruby, groovy into CI and codebase to improve overall code quality
  - Created Spark Chat bot for team's usage to flash software automatically
  - Investigrated comparison between python/behave vs ruby/cucumber
  - Created Python services based on protobuffers and grpc
  - Created single page HTML app to quickly visualize recorded trace on map using JavaScript and leaflet
  - Helped with building AGL image, SDK compilation, crosscompilation a part prototyping project for another platform
  - Code reviews via gerrit for c++, ruby, python and groovy languages
  - Used CMake to build and debug application and run C++ unit test
- Skills: JIRA, Jenkins, Docker, repo, git, Python, bash, Ruby, rspec, Cucumber, BDD, Scrum, Agile, QtCreator, Django, gerrit, Cisco Spark, AGL, CMake

_Reason for resignation: my partner finished studies and we chose Munich as big hub of potential employers_

**QA Engineer** | _Helpling GmbH, Berlin, Germany_ | Sep 2015 \- Feb 2016

- Participated in Agile/Scrum development of web application for booking house cleaners
- Performed regression testing for new releases with manual and automated tests
- Joined stack conversion from PHP to Ruby on Rails
- Ruby on Rails introductory training
- Created multiple workshop to teach manual QAs how to automate tests and speed up quality assurance
- Skills: JIRA, Jenkins, Confluence, GitHub, Behat, PHP, Ruby, Rspec, Cucumber, Scrum, Firefox, Google Chrome, Internet Explorer

_Reason for resignation: found better opportunity in automotive_

**Automation QA Engineer** | _Satprof B.V. Eesti filiaal, Tallinn, Estonia_ | Jul 2014 \- Jun 2015

- Increase quality of satellite receiver’s library by adding automated test cases and tools for development
- Data-driven and keyword-driven development with Python and Robot Framework
- Created Python UI tool to faster debug binary data transmitted by receiver and use it in automated test cases
- Skills: Python 2.7, Robot Framework, RIDE, Eclipse, PyDev, Git, Jenkins, JIRA, Agile Board, Confluence, TestLink, Scrum

_Reason for resignation: wanted to get experience abroad_

**Software Developer** | _Betsson Group, Tallinn, Estonia_ | Aug 2013 \- Jul 2014

- Full stack web development of online gambling website with continuous deployment and code reviews
- Enrich website with additional features and new marketing campaign landing pages using HTML,jQuery and Javascript
- Added new features to backend with Python, twisted framework and PostgreSQL requests
- Used vagrant for local development to emulate whole system on local machine
- Was on duty several times to monitor that system is working as expected
- Bug triaging with Kibana and Elasticsearch and with logs on remote machines from terminal
- Participated in all stages of software development lifecycle with continuous deployment, code reviews and Agile practices
- Skills: Python 2.7, twisted, HTML, CSS, ClearSilver, JavaScript, PostgreSQL, SQL, Trac, Review Board, Kibana, Mercurial, Vagrant, PyCharm, Ubuntu, Scrum, Kanban

_Reason for resignation: migration from Python to .NET and opportunity in C/C++_

**Junior Developer** | _AS Tallink Group, Tallinn, Estonia_ | Jun 2013 \- Jun 2013

- 12-days practical work to finalize Java course
- Investigated and fixed bugs for Java XML/XSLT conversion engine and implemented additional unit tests
- Skills: XML, XSLT, TDD, Java, JUnit, Mockito, oXygen XML Editor

**Senior Test Automation Specialist** | _Ixonos Estonia OÜ, Tallinn, Estonia_ | Nov 2010 \- Apr 2013

- Participate in multiple project with different programming languages, technologies and tools, improve stability and reproducibility of the tests
  - Project 5: Developed Python web test automation framework from scratch using Selenium WebDriver and wxPython for GUI(Awarded for outstanding work in this project)
  - Project 4: Improved quality of web mapping service by adding additional JUnit functional tests based on Selenium WebDriver
  - Project 3: Performed regression testing for mobile device interfaces using Ruby scripts and TDriver
  - Project 2: Implement additional automated test cases for covering main synchronization functionality between the C++ application and mobile device, travel to finland to customer site for better project integration and knowledge sharing.
  - Project 1: Functional and non-functional testing of mobile OS using manual and automated tests. Run regressions tests for new software, report bugs.
- Skills: Aptana Studio, BugZilla, C++, CWiki, EGit, IntelliJ IDEA, Java, Jenkins, JIRA, Linux, Maven, MIN Test Framework, Minicom, Python 2.7, QC, Qt, Scratchbox, Selenium WebDriver, SVN, Ubuntu, Visual Studio 2008, Vlc Python bindings, wxPython

_Reason for resignation: hub in Tallinn was closed and layoffs_

**Assembler** | _Fabek Elektroonika OÜ, Tallinn, Estonia_ | Jun 2007 \- Aug 2007

- Assembled and packaged electronic devices
- Performed wire soldering for hardware devices

_Reason for resignation: studies_

## Personal projects

**[Golang Web Services Playground](https://github.com/kirillstrelkov/go-web-services)** | 2026

- Built a REST API for a blogging platform with CRUD operations, JWT authorization, Argon2 password hashing and custom routing middleware.
- Developed a gRPC server featuring access control (ACL) and request logging, alongside a separate GraphQL API for an e-commerce backend using gqlgen.
- Implemented concurrent data processing pipelines and a synchronized multiplayer game state, using pprof to identify and resolve performance bottlenecks.
- Created a CLI tool that automatically generates validation code from Go struct tags and utilized the reflect package for dynamic data mapping.
- Skills: Go, gRPC, GraphQL, REST, Concurrency, pprof, JWT, MySQL, Go Reflection.

**[Todo App GitOps Kubernetes Deployment Pipeline](https://github.com/kirillstrelkov/todo-app-gitops)** | 2026

- Engineered a declarative Continuous Delivery pipeline using ArgoCD to automatically synchronize and deploy application infrastructure to Kubernetes clusters.
- Architected scalable deployment configurations by isolating environments into base and app-specific directories, managing Kubernetes manifests as code to eliminate configuration drift.
- Streamlined developer workflows and local cluster orchestration by building comprehensive automation scripts using Makefile.
- Skills: Kubernetes, ArgoCD, GitOps, Continuous Delivery, Makefile, Infrastructure as Code.

**[University of Helsinki DevOps Labs: Cloud-Native Microservices](https://github.com/kirillstrelkov/KubernetesSubmissions)** | 2026

- Developed a distributed, event-driven microservices application in Go, utilizing NATS as a message broker to asynchronously trigger Telegram notifications, with state managed in PostgreSQL.
- Configured advanced progressive delivery utilizing Argo Rollouts, integrating automated canary rollbacks triggered by Prometheus CPU utilization metrics to ensure zero-downtime releases.
- Secured cluster configurations via SOPS for encrypted secrets management and integrated an Istio service mesh paired with Knative for serverless workload scaling.
- Deployed the architecture across local (k3d) and remote Google Kubernetes Engine (GKE) clusters, utilizing Helm for package management and a Grafana/Loki stack for observability.
- Skills: Kubernetes, Go, GKE, NATS, Prometheus, Istio, Knative, Helm, SOPS, Docker.

**[Advanzia2csv](https://github.com/kirillstrelkov/advanzia2csv)** | 2025 - ...

- Developed a robust Rust-based CLI utility to automate the extraction of credit card billing statements.
- Parsed complex PDF documents and converted unstructured financial data into structured, easy-to-analyze CSV formats.
- Skills: Rust, LoPDF (PDF Parsing), Clap (CLI architecture), Serde, Data Extraction, Workflow Automation.

**[Browser Extension: Summarize with AI](https://github.com/kirillstrelkov/browser-ext-gemini-summarize)** | 2025

- Engineered a cross-browser extension (Chrome & Firefox) utilizing the Gemini API to automatically summarize selected webpage text via a custom context menu.
- Implemented a responsive, dark-mode compatible UI using Pico.css and dynamically rendered structured AI responses into HTML using Showdown.js.
- Automated the extension's build, linting and cross-browser packaging processes using Makefile and Node.js scripts.
- Skills: JavaScript, Web Extensions API, Gemini API, Node.js, Showdown.js, Pico.css, Makefile, ESLint.

**[Car Search and Comparison Website](https://github.com/kirillstrelkov/vscar)** | 2024 - ...

- Architected and developed a full-stack car search and comparison platform utilizing vehicle data aggregated from ADAC.
- Engineered a dynamic frontend using Angular and RxJS and designed a polyglot backend ecosystem (microservices/API endpoints) to evaluate and benchmark multiple languages and frameworks (Rust, Go, Python, Java, Kotlin).
- Managed containerized deployments and cloud hosting across multiple platforms including Vercel, Render and Heroku.
- Skills: TypeScript, Angular, RxJS, NestJS, MongoDB, Docker, Microservices, Cloud Deployment (Vercel, Render, Heroku), Rust (Rocket), GoLang (Gin), Python (FastAPI), Java (Spring Boot), Kotlin (Ktor), Cursor.

**[Employee Polls Web App](https://github.com/kirillstrelkov/employee-pools)** | 2022

- Developed an interactive dashboard application allowing users to create, answer and visualize results for internal polls.
- Implemented a responsive UI with Material-UI (MUI) and managed complex application state using Redux and React Redux.
- Configured client-side routing and ensured application reliability through comprehensive unit testing.
- Skills: JavaScript (ES6+), React, React Redux, Redux Middleware/Thunk, React Router, Material-UI (MUI), Jest, HTML5/CSS3, Git.

**[Csv2qif](https://github.com/kirillstrelkov/csv2qif)** | 2020 - ...

- Engineered a high-performance, multithreaded Command-Line Interface (CLI) tool to parse financial CSV files and convert them into QIF format.
- Implemented a customizable configuration system to automatically categorize financial transactions during the parsing process.
- Leveraged Rust’s `rayon` crate for data parallelism and efficient processing of large transaction logs.
- Skills: Rust, Cargo, Rayon (Parallel Processing/Multithreading), Serde (Serialization), Clap (CLI), Data Transformation.

**[Estonian New Vehicle Market Analysis](https://github.com/kirillstrelkov/playground/tree/master/auto/mnt)** | 2020 - ...

- Extracted and processed historical vehicle registration data from the Estonian Transport Administration (MNT) to identify automotive market trends.
- Developed Jupyter Notebooks to perform Exploratory Data Analysis (EDA) on latest-year registration statistics, cleaning and visualizing large datasets.
- Skills: Python, Jupyter Notebooks, Pandas, Data Wrangling, Exploratory Data Analysis (EDA), Data Visualization.

**[ADAC Used Car Price Analysis](https://kirillstrelkov.medium.com/analysis-of-used-car-price-using-adac-c793ec4890e9)** | 2020

- Scraped and processed used car pricing data from ADAC reports to calculate and model vehicle depreciation over time.
- Performed Exploratory Data Analysis (EDA) and data wrangling on large datasets to uncover pricing trends across different car models and years.
- Skills: Python, Jupyter Notebooks, Pandas, NumPy, Selenium, MyPy, Data Scraping/Extraction, Exploratory Data Analysis (EDA), Data Visualization.

**[My Vocabulary](https://github.com/kirillstrelkov/my-vocabulary)** | 2016

- Architected an interactive Ruby on Rails quiz game platform that integrates the Yandex Dictionary API to help users learn and retain new vocabulary.
- Ensured high application reliability by implementing a robust Behavior-Driven Development (BDD) testing suite utilizing RSpec, Cucumber and Capybara.
- Skills: Ruby on Rails, PostgreSQL, Redis, Yandex API, Devise, RSpec, Cucumber, Capybara, Heroku.

**[Projects Overview](https://github.com/kirillstrelkov/projects_overview)** | 2016

- Developed a comprehensive Ruby on Rails project management application to track tasks, deadlines and calculate weekly milestone progress.
- Integrated third-party OAuth authentication (Google, Facebook) via Devise/OmniAuth and implemented a centralized admin dashboard for database management.
- Skills: Ruby on Rails (v7), PostgreSQL, Redis, Devise, OmniAuth, Bootstrap, RSpec, Cucumber, Capybara.

**[Easelenium Testing Framework](https://github.com/kirillstrelkov/easelenium)** | 2014 - ...

- Architected and developed an automated web testing wrapper framework built on top of Selenium WebDriver to simplify and accelerate UI testing workflows.
- Designed reusable test components and structured execution flows, reducing boilerplate code required for complex end-to-end (E2E) browser testing.
- Skills: Selenium WebDriver, Test Automation, QA Engineering, Framework Architecture, End-to-End (E2E) Testing.

**[ChoosePhone](https://github.com/kirillstrelkov/choosephone)** | 2014

- Created a comparison web tool allowing users to rank and sort smartphones based on aggregated benchmark scores.
- Configured a multi-browser automated acceptance testing pipeline (Chrome, Firefox, mobile emulators) using Cucumber, Selenium WebDriver and Capybara to ensure cross-platform compatibility.
- Skills: Ruby on Rails, Redis, Puma, Cucumber, Selenium WebDriver, Capybara, Travis CI, Heroku.

**[ChooseLaptop](https://github.com/kirillstrelkov/chooselaptop)** | 2014

- Built a web application that aggregates, sorts and filters laptop models based on external CPU/GPU benchmark ratings and pricing.
- Enhanced user search functionality by implementing fuzzy string matching via C-extension Levenshtein distance to handle complex hardware naming conventions.
- Skills: Ruby on Rails, PostgreSQL, Redis, CoffeeScript, Turbolinks, Levenshtein Distance, Heroku, Bootstrap.

## Courses and certificates

- Apache Flink Fundamentals, _Confluent_ | May 2026
- Apache Kafka Fundamentals, _Confluent_ | May 2026
- Building with the Claude API, _Coursera_ | May 2026
- Meta React, _Coursera_ | May 2026
- Claude Code in Action, _Coursera_ | Apr 2026
- Go Programming Language, _Coursera_ | Apr 2026
- Go Essentials: Concurrency, gRPC & More, _Coursera_ | Mar 2026
- Разработка веб-сервисов на Golang (Go), _Stepik_ | Mar 2026
- Certified Kubernetes Application Developer, _Cloud Native Computing Foundation_ | Feb 2026
- Kubernetes for developers(LFD259), _Linux Foundation_ | Feb 2026
- DevOps with Kubernetes, _University of Helsinki_ | Feb 2026
- Scalable Microservices for Developers, _Coursera_ | Oct 2025
- IBM Full Stack Software Developer, _Coursera/IBM_ | Sep 2025
- Google AI Essentials, _Coursera/Google_ | Sep 2025
- Architecting with Google Kubernetes Engine, _Coursera/Google_ | Sep 2025
- Algorithms on Strings, _Coursera_ | Sep 2025
- Scalable Microservices with Kubernetes, _Udacity​_ | Sep 2025
- Introduction to AI, _Coursera_ | Sep 2025
- Concurrent and Parallel Programming in Python, _Coursera_ | Aug 2025
- Amazon Junior Software Developer, _Coursera/Amazon_ | Aug 2025
- Microsoft Python Development, _Coursera/Microsoft_ | Aug 2025
- Rust Programming, _Coursera_ | Jun 2025
- Kotlin for Java Developers, _Coursera_ | May 2025
- Developing with GitHub Copilot and VS Code, _Coursera_ | Apr 2025
- Microsoft Certified: Azure Fundamentals, _Microsoft_ | Jan 2025
- Introduction to AutoSAR, _Coursera_ | Dec 2024
- RUST for Developers, _CARIAD​_ | Nov 2024
- Python and Rust with Linux Command Line Tools, _Coursera_ | May 2024
- Rust for DevOps, _Coursera_ | May 2024
- Data Engineering with Rust, _Coursera_ | Apr 2024
- GitHub Copilot, _Udacity​_ | Feb 2024
- Rust Fundamentals, _Coursera_ | Jan 2024
- C++ Nanodegree, _Udacity_ | Jun 2023
- Искусство разработки на C++: Коричневый пояс, _ФРОО_ | May 2023
- EB corbos Adaptive AUTOSAR, _Elektrobit_ | Mar 2023
- Programming with Google Go, _Coursera_ | Dec 2022
- React nanodegree, _Udacity_ | Sep 2022
- Algorithms on Graphs, _Coursera_ | May 2022
- Основы разработки на C++: красный пояс, _Coursera_ | Nov 2021
- AWS Machine Learning Foundations, _Udacity_ | Oct 2021
- Data Structures, _Coursera_ | Sep 2021
- Algorithmic Toolbox, _Coursera_ | Jul 2021
- GitLab Certified Associate, _GitLab_ | May 2021
- Financial Markets, _Coursera_ | Apr 2021
- Oracle Certified Professional: Java SE 11 Developer, _Oracle_ | Apr 2021
- Data Structure and Algorithms Nanodegree, _Udacity_ | Mar 2021
- SCADE Suite Basic Training, _Unknown_ | Sep 2020
- Data Structures & Algorithms in Python, _Udacity_ | Aug 2020
- Front End Frameworks, _Udacity_ | Aug 2020
- Rapid Prototyping, _Udacity_ | Jul 2020
- Kotlin Bootcamp for Programmers, _Udacity_ | Jun 2020
- ES6, _Udacity_ | Apr 2020
- JavaScript Promises, _Udacity_ | Mar 2020
- C Programming with Linux, _edX/DartmouthX and IMTx_ | Nov 2019
- ClearCase Fundamentals, _AERTEC Solutions GmbH_ | Sep 2019
- Functional Safety for SW-Development, _exida.com GmbH_ | Jan 2019
- Основы разработки на C++: жёлтый пояс, _Coursera_ | Jun 2018
- Intro to Self-Driving Cars, _Udacity_ | Jan 2018
- Основы разработки на C++: белый пояс, _Coursera_ | Oct 2017
- C++ For C Programmers, Part B, _Coursera_ | Jun 2017
- C++ For C Programmers, Part A, _Coursera_ | Feb 2017
- Website Performance Optimization, _Udacity_ | Sep 2016
- How to Use Git and GitHub, _Udacity_ | Jan 2016
- Introduction to C++, _Microsoft/edX_ | Dec 2015
- Ruby on Rails: An Introduction, _Coursera_ | Nov 2015
- Usable Security, _Coursera_ | Oct 2015
- QEMx: Quality Engineering and Management, _TUMx/edX_ | Sep 2015
- Bachelor of Science in Engineering, _TTÜ_ | Jun 2015
- Android mobile application programming for beginners, _IATI_ | Jun 2015
- Software Security, _Coursera_ | Apr 2015
- LFS101x Introduction to Linux, _Linux Foundation/edX_ | Dec 2014
- CS169.2x: Software as a Service, _Berkeley/edX_ | Jul 2014
- CS169.1x: Software as a Service, _Berkeley/edX_ | Jun 2014
- Web programming, _IATI_ | Apr 2014
- Introduction to Databases, _Stanford ONLINE/OpenEdX_ | Mar 2014
- M101P: MongoDB for Developers, _MongoDB Inc_ | Feb 2014
- Oracle Certified Expert, EE 6 Web Services Developer, _Oracle_ | Jun 2013
- Oracle Certified Professional, Java SE 6 Programmer, _Oracle_ | Jun 2013
- 6.00x: Introduction to Computer Science and Programming, _MITx/edX_ | Jun 2013
- Tallinna ja Harjumaa noorte töötute koolitamine JAVA programmeerijateks, _IT Koolituskesku- OÜ_ | May 2013-
- ISEB Intermediate Certificate in Software Testing, _Prometric_ | Mar 2012
- ISTQB - ISEB Certified Tester Foundation Level, _Prometric_ | Dec 2011

</master_cv>

<job_description>
Software Engineer – Golang (m/w/d) - Gigafactory Berlin-Brandenburg
Job-Kategorie	Engineering & Information Technology
Standort	Grünheide (Mark), Brandenburg
Anforderungs-ID	265604
Arbeitsverhältnis	Full-time
Was Sie erwartet
Tesla is accelerating the world's transition to sustainable energy. We continuously develop revolutionary strategies and products within shortest time, and successfully launch them on a large scale. This is only possible through extraordinary speed, innovation, and efficiency.
Gigafactory Berlin forms the perfect basis for rolling out Tesla's incredible success story in Europe. The most important pillar for this is our employees. Their passion, motivation and engagement ensure that we consistently achieve our goals. 



The Role

We are currently looking for highly motivated Golang developers (all seniorities) to join the Factory Software Engineering team. 

Our engineers are hands-on and encouraged to own their own projects, contribute to innovative ideas, and make an impact on the way our company operates. The mission of our team is to streamline factory operations by building world-class scalable software systems, decrease business costs, and solve engineering challenges from both development and support perspective.

Was zu tun ist
Participate in requirements gathering, technical specification, and design of complex software systems
Define an architecture for fault-tolerant, distributed, and adaptive automation applications 
Implement, deploy, and maintain enterprise-scale manufacturing execution software 
Work closely with Operations, Manufacturing Engineering, Quality, and Supply Chain teams. Collaborate with teams of engineers from multiple disciplines.
Build tools, test-automation, and documentation 
Be flexible, responsive, and adaptive to ever changing business requirements 
Was mitzubringen ist
Good understanding of software development fundamentals including software design, algorithms, data structures, modularity, and code maintainability
Degree in Computer Science or related field, or equivalent experience
Working experience as a software engineer from 3+ years
Hands-on software development experience using Go, or a multi-year experience with another programming language (especially Java, Scala, Kotlin, C#, C++, Rust) and a willingness to learn Go
Efficient knowledge of SQL and relational databases (MySQL, PostgreSQL, etc.)
Full professional proficiency in English; German is a plus
Experience with Docker and/or Kubernetes a big plus
Kafka knowledge and stream processing is nice to have
Debugging complex systems using centralized logging (Prometheus, Splunk, etc.)
Knowledge of distributed computing and data storage systems
Proficiency in working in a high-impact, responsive, and collaborative team environment
Smart but humble, with a bias for action
Candidates are expected to uphold and actively promote sustainability principles in their daily work, operating in line with Tesla Global Environmental, Health, Safety & Security (EHS&S) Policy and EMAS requirements, fostering a culture of continuous environmental improvement.

What we offer

You will be working in our state-of-the-art Gigafactory, where you’ll solve the world's most interesting problems with the best and brightest people who share a passion to change the world. Tesla’s compensation package includes competitive salary and Tesla shares or bonuses. Typical benefits that are offered are a pension program, 30 vacation days, flexible work arrangements, corporate benefits, employee insurances, relocation, and commuting support.


</job_description>
