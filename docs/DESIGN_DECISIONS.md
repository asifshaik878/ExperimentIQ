# ExperimentIQ — Design Decisions and Technical Reasoning

## 1. Project Overview

ExperimentIQ is a synthetic experimentation analytics platform designed to demonstrate how controlled experiments can be generated, validated and analyzed.

The platform generates 10 experiments with 50,000 eligible users in total. It models experiment assignments, exposures, conversions, metric definitions, guardrails and operational events.

The implementation also introduces labelled data-quality anomalies to evaluate experiment integrity.

## 2. Technology Choices

| Technology | Reason for selection |
|---|---|
| Python | Suitable for data generation, statistical calculations and application development |
| NumPy | Efficient random number generation and numerical operations |
| Pandas | Structured dataset manipulation and CSV exports |
| SciPy | Statistical calculations, including sample ratio mismatch testing |
| SQLite | Lightweight relational database with foreign-key and integrity support |
| SQL | Explicit schema design and relational data management |
| Streamlit | Rapid development of an interactive analytics dashboard |
| Plotly | Interactive charts for experiment results |
| pytest | Automated verification of database structure and integrity |
| Git and GitHub | Version control and public project collaboration |

## 3. Database Design

The database uses a relational structure with 12 tables:

1. experiments
2. variants
3. audience_members
4. assignments
5. exposure_events
6. conversion_events
7. metric_definitions
8. guardrail_metrics
9. experiment_results
10. experiment_state_events
11. support_events
12. refund_events

### Design rationale

The entities are separated to maintain clear responsibilities and relationships.

For example:

- Experiments define the configuration and lifecycle.
- Variants represent control and treatment groups.
- Assignments record the user's allocated group.
- Exposure events record experiment exposure.
- Conversion events record measured outcomes.
- Metric definitions preserve metric configuration and versions.
- Experiment results store the calculated analysis.
- Support and refund events provide operational guardrail data.

Primary keys identify individual records, while foreign keys maintain relationships between dependent entities.

SQLite was selected to keep the project self-contained and easy to execute without requiring an external database server.

## 4. Deterministic Data Generation

The generator uses a configurable random seed.

The default base seed is `20261022`.

Each experiment receives a deterministic experiment-specific seed calculated using:

`base_seed + experiment_number`

This allows each experiment to have reproducible random data while maintaining different experiment-specific random sequences.

The project was generated independently twice using the same configuration.

SHA-256 comparisons confirmed that all exported files, excluding the SQLite database file itself, were byte-for-byte identical. The comparison covered the CSV and JSON exports, manifest and validation summary.

## 5. Experiment Design

The dataset contains 10 experiments, each with 5,000 eligible users.

Each experiment includes control and treatment variants.

The generator covers scenarios including:

- Balanced allocation.
- Unbalanced allocation.
- Sample Ratio Mismatch.
- Guardrail regression.
- Refund regression.
- Low treatment effect.
- Delayed conversion outcomes.
- Multiple labelled data-quality anomalies.

The primary metric is conversion rate.

The outcome window is configured as 30 days.

## 6. Statistical Methodology

### Primary metric

Conversion rate is calculated as:

`Conversion Rate = Converted Users / Assigned Users`

The primary analysis uses intention-to-treat assignment groups.

### Treatment effect

Absolute lift:

`Treatment Conversion Rate - Control Conversion Rate`

Relative lift:

`(Treatment Conversion Rate - Control Conversion Rate) / Control Conversion Rate`

### Statistical significance

A two-sided two-proportion z-test is used to compare binary conversion outcomes between control and treatment.

The analysis also stores a 95% confidence interval for the absolute difference.

The significance threshold used for the decision logic is 0.05.

Statistical significance is not treated as sufficient evidence to ship a treatment. SRM and guardrail checks are considered in the decision process.

## 7. Sample Ratio Mismatch

Sample Ratio Mismatch checks whether observed experiment assignment counts differ significantly from the expected allocation.

The implementation uses a chi-square goodness-of-fit test.

The configured SRM significance level is 0.001.

An experiment with detected SRM receives a `HOLD_SRM` decision in the generator's decision logic.

This prevents a potentially unreliable experiment from being treated as a successful result merely because its primary metric appears positive.

## 8. Guardrail Monitoring

ExperimentIQ defines two operational guardrails.

| Guardrail | Threshold | Comparison |
|---|---:|---|
| Support Contact Rate | 8% | MAX |
| Refund Rate | 5% | MAX |

The generator calculates these rates separately for control and treatment using assignment-level binary outcomes.

Each assignment contributes either zero or one outcome for each guardrail.

A treatment support rate above 8%, or treatment refund rate above 5%, causes the guardrail status to become `FAIL`.

The experiment decision logic prioritizes SRM detection, then guardrail failures, before evaluating whether the treatment has a statistically significant positive effect.

Possible decisions include:

- `HOLD_SRM`
- `STOP_GUARDRAIL`
- `SHIP`
- `NO_CLEAR_WIN`

## 9. Metric Versioning

Metric definitions include a version number and effective dates.

This supports the representation of metric changes over time and helps preserve the metric definition used when an experiment result was calculated.

The generated dataset includes a metric-version change scenario.

## 10. Data Quality and Edge Cases

The generator includes five labelled anomaly types:

1. `MULTIPLE_VARIANT_ASSIGNMENT`
2. `EXPOSURE_BEFORE_ASSIGNMENT`
3. `OUTCOME_WINDOW_INCONSISTENT`
4. `SAMPLE_RATIO_MISMATCH_IGNORED`
5. `METRIC_DEFINITION_CHANGED_AFTER_RESULTS`

These scenarios are included to evaluate how experiment systems handle assignment conflicts, event ordering, outcome-window violations, SRM and metric-version changes.

Ground-truth records are exported in CSV and JSON formats.

The ground-truth data helps distinguish intentionally injected anomalies from ordinary generated records.

## 11. Validation Strategy

The generator produces a validation summary containing 23 automated integrity checks.

The checks cover:

- Primary-key uniqueness across all 12 tables.
- Variant and experiment relationships.
- Assignment foreign keys.
- Exposure foreign keys.
- Conversion foreign keys.
- Metric and guardrail relationships.
- Experiment result relationships.
- Required anomaly coverage.
- Result sample-size reconciliation.
- Metric version preservation.
- Guardrail decision reconciliation.

The generated dataset passed all 23 checks.

## 12. Automated Testing

A pytest test suite contains nine tests.

The tests verify:

- Database existence.
- Expected database tables.
- Experiment count.
- Audience member count.
- Experiment result count.
- Experiment state event count.
- Primary-key uniqueness.
- Foreign-key integrity.
- Validation summary status.

All nine tests passed in the local development environment.

## 13. Dashboard Design

The Streamlit dashboard provides:

- Experiment selection.
- Platform-level overview.
- Selected experiment details and hypothesis.
- Control and treatment conversion rates.
- Absolute and relative treatment lift.
- P-values and confidence intervals.
- Sample sizes and SRM status.
- Stored experiment decisions.
- Variant allocation charts.
- Guardrail configurations.
- Metric definitions.
- Comparison of experiment results.

The dashboard uses the generated SQLite database as its data source.

## 14. Trade-offs and Limitations

### Synthetic data

The platform uses generated data rather than real production traffic. Therefore, the results demonstrate implementation behavior and statistical workflows, not actual business performance.

### Statistical assumptions

The two-proportion z-test is an approximate method for comparing binary outcomes. Real experimentation systems may require additional treatment of repeated measurements, clustering, covariates, sequential testing and multiple comparisons.

### SRM scope

The implementation demonstrates assignment-ratio validation using a chi-square test. A production platform would also investigate eligibility, exposure, telemetry loss and other causes of allocation imbalance.

### Guardrail analysis

Guardrail decisions are generated using assignment-level binary outcomes. The dashboard displays stored decisions and configured thresholds; it does not independently recompute the full guardrail decision from raw events.

### Database choice

SQLite keeps the project portable and simple to run. A production-scale experimentation platform would likely require a more scalable database and event-processing architecture.

### Dashboard scope

The Streamlit dashboard is an analytical demonstration rather than a production experiment-management application. It does not provide live traffic ingestion or experiment lifecycle controls.

## 15. Future Improvements

Potential improvements include:

- Recalculating guardrail metrics directly from raw events in the dashboard.
- Adding exposure-compliance and telemetry-quality analysis.
- Adding automated statistical regression tests.
- Supporting configurable outcome windows.
- Introducing additional statistical methods and multiple-testing corrections.
- Adding experiment lifecycle management.
- Supporting larger datasets and production database systems.
- Adding continuous integration for automated test execution.

## 16. Conclusion

ExperimentIQ demonstrates a reproducible workflow for synthetic experiment generation, relational data management, statistical analysis, integrity validation and interactive reporting.

The design emphasizes deterministic data generation, explicit experiment assumptions, data-quality scenarios and automated verification.

The implementation was tested locally, with 23 validation checks and nine automated tests passing.

Repository: https://github.com/asifshaik878/ExperimentIQ