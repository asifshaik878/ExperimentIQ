# AI Usage and Prompt History

## 1. Purpose

This document explains how generative AI was used during the development of ExperimentIQ, where it accelerated implementation, and which development activities were personally executed and validated.

ChatGPT was used as a development assistant throughout the project. The objective was to use AI productively while maintaining responsibility for reviewing, running, testing, and understanding the resulting implementation.

## 2. AI Tools Used

| Tool | Purpose |
|---|---|
| ChatGPT | Project planning, Python code assistance, SQL schema design, debugging guidance, documentation and testing support |
| Visual Studio Code | Local development, editing, terminal execution and debugging |
| Python and pytest | Running the application and validating generated data |
| Git and GitHub | Version control and public project publication |

## 3. Prompt History

The following is a summarized record of representative prompts and development requests from the project collaboration.

### Phase 1: Project planning and architecture

Prompts and requests included:

- Help me build the candidate project from scratch within the available time.
- Break the implementation into small steps and verify each checkpoint before proceeding.
- Design a synthetic experimentation dataset with 50,000 users and 10 experiments.
- Include the required experiment entities, relationships and labelled edge cases.

AI assistance:
- Helped organize the project into implementation stages.
- Suggested a relational database structure.
- Helped translate project requirements into development tasks.

### Phase 2: Database and data generation

Prompts and requests included:

- Help me create the SQL schema for the experimentation platform.
- Provide the final Python data generator.
- Support deterministic generation using a configurable seed.
- Include balanced and unbalanced allocations, SRM, delayed conversions and guardrail regressions.
- Generate CSV, JSON and SQLite outputs.

AI assistance:
- Assisted with SQL schema and Python generator implementation.
- Helped structure data generation and validation logic.
- Identified the importance of inserting records into the existing SQLite schema without replacing its constraints.

### Phase 3: Validation and reproducibility

Prompts and requests included:

- Help me validate the generated database.
- Check whether all required anomaly types are present.
- Verify that the generated files are reproducible using the same seed.
- Help me write automated database tests.

AI assistance:
- Helped design integrity checks.
- Assisted with pytest test cases.
- Guided the SHA-256 comparison process.

### Phase 4: Dashboard development

Prompts and requests included:

- Help me build an interactive Streamlit experimentation dashboard.
- Display treatment effects, conversion rates, p-values and confidence intervals.
- Display SRM status, variant allocation and guardrail configurations.
- Help me inspect the actual database schema before implementing dashboard queries.

AI assistance:
- Assisted with the Streamlit application structure.
- Helped create database queries and Plotly visualizations.
- Helped interpret the generated experiment results.

### Phase 5: Documentation and publication

Prompts and requests included:

- Help me write the README and database data dictionary.
- Guide me through Git initialization and GitHub publication.
- Review the candidate project submission guidelines.
- Help document AI usage, engineering decisions and project limitations.

AI assistance:
- Helped prepare project documentation.
- Guided Git commands and repository publication.
- Helped organize the submission materials.

## 4. Where AI Accelerated Development

AI assistance was particularly useful for:

- Breaking a large project into manageable implementation stages.
- Drafting repetitive SQL and Python structures.
- Creating validation and automated testing logic.
- Developing dashboard layouts and database queries.
- Preparing technical documentation.
- Troubleshooting command-line and implementation issues.

## 5. Personal Contributions and Verification

The project was developed and executed locally by the candidate.

The candidate personally:

- Created the project directory and Python virtual environment.
- Installed dependencies and configured the development environment.
- Created and saved the project files in Visual Studio Code.
- Executed the database schema and data generator.
- Ran the generator independently using the same seed and configuration.
- Compared generated export files using SHA-256 checksums.
- Reviewed the validation summary containing 23 successful checks.
- Executed the automated test suite and verified all 9 tests passed.
- Launched the Streamlit dashboard and inspected its displayed results.
- Initialized the Git repository, committed the project and published it to GitHub.
- Reviewed the submission guidelines and prepared supporting documentation.

## 6. What Was Personally Reviewed

Particular attention was given to:

- Database relationships and foreign-key integrity.
- Sample-size reconciliation.
- Treatment and control allocation.
- SRM detection.
- Conversion measurement and outcome windows.
- Guardrail thresholds and stored decisions.
- Reproducibility of generated exports.
- Automated test results.
- Dashboard output against the generated database.

## 7. Limitations of AI Assistance

AI-generated code can contain incorrect assumptions, implementation defects or incomplete edge-case handling.

For that reason, generated code was executed and checked against the local project outputs. The successful validation and test results provide evidence of the checks performed, but do not establish that every possible behavior is defect-free.

The prompt history above is a summarized development record rather than a complete verbatim transcript.

## 8. Transparency Statement

Generative AI was an important development assistant for ExperimentIQ. It accelerated planning, code drafting, testing guidance and documentation.

The candidate remains responsible for the submitted implementation, its execution, validation, technical decisions and explanation of the solution.

Repository: https://github.com/asifshaik878/ExperimentIQ