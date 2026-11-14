
# ExperimentIQ

An experimentation data platform built to simulate, validate, and analyze controlled experiments at scale.

ExperimentIQ generates realistic A/B testing datasets and introduces controlled data-quality issues to evaluate experiment integrity, statistical reliability, and guardrail monitoring.

## Project Overview

ExperimentIQ simulates 10 experiments with 50,000 eligible users in total. Each experiment includes control and treatment groups, assignment records, exposure events, conversion outcomes, and operational guardrail events.

The platform also introduces labelled edge cases to test whether experiment analysis can identify data-quality and measurement problems before producing decisions.

## Key Capabilities

- Deterministic synthetic data generation using a configurable random seed.
- Control and treatment group allocation, including unbalanced allocation.
- Sample Ratio Mismatch (SRM) detection.
- Conversion measurement with configurable outcome windows.
- Treatment effect estimation and statistical significance testing.
- Guardrail monitoring using support and refund events.
- Versioned metric definitions.
- Labelled data-quality anomalies with ground-truth records.
- SQLite database and CSV/JSON exports.
- Automated integrity and consistency validation.
- Reproducibility verification using SHA-256 checksums.

## Technology Stack

- Python
- Pandas
- NumPy
- SciPy
- SQLite
- SQL
- Git

## Project Structure

```text
ExperimentIQ/
├── docs/
├── outputs/
├── src/
│   └── generate.py
├── tests/
├── schema.sql
├── requirements.txt
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd ExperimentIQ
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate the dataset

```bash
python src/generate.py --out outputs --seed 20261022 --users-per-experiment 5000
```

### 5. Run a reproducibility generation

```bash
python src/generate.py --out outputs_repro --seed 20261022 --users-per-experiment 5000
```

The second generation can be compared with the original exports using SHA-256 checksums.

## Generated Outputs

The generator produces:

| Output | Description |
|---|---|
| `experimentiq.db` | SQLite database containing the generated experiment data |
| `experiments.csv` | Experiment configurations |
| `variants.csv` | Control and treatment variants |
| `audience_members.csv` | User eligibility and audience attributes |
| `assignments.csv` | Experiment assignment records |
| `exposure_events.csv` | Experiment exposure records |
| `conversion_events.csv` | Conversion outcome events |
| `metric_definitions.csv` | Versioned metric definitions |
| `guardrail_metrics.csv` | Guardrail configurations |
| `experiment_results.csv` | Experiment analysis results |
| `experiment_state_events.csv` | Experiment lifecycle history |
| `support_events.csv` | Support-related events |
| `refund_events.csv` | Refund-related events |
| `ground_truth.csv` | Labelled anomaly records |
| `ground_truth.json` | Ground-truth anomaly details |
| `manifest.json` | Dataset generation and file-integrity metadata |
| `validation_summary.json` | Automated validation results |

## Data Integrity and Validation

The generator performs automated checks covering:

- Primary-key uniqueness.
- Foreign-key integrity.
- Experiment and variant relationships.
- Required anomaly coverage.
- Sample-size reconciliation.
- Metric version consistency.
- Guardrail decision consistency.

The current generated dataset passed all 23 validation checks.

## Reproducibility

The default random seed is `20261022`.

Two independent generations using the same seed and configuration produced identical exported files, verified using SHA-256 checksums.

## Project Objective

The objective of ExperimentIQ is to demonstrate how an experimentation platform can generate reliable datasets, detect experiment-integrity issues, measure treatment effects, and support data-driven product decisions.

