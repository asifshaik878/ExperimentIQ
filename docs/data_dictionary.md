# ExperimentIQ — Data Dictionary

## Overview

ExperimentIQ uses a relational SQLite database to represent experiment configurations, user assignments, exposure events, conversion outcomes, metric definitions, experiment results, and operational guardrail events.

The database contains 12 tables connected through primary and foreign keys.

## 1. experiments

Stores the configuration and lifecycle information for each experiment.

| Field | Description |
|---|---|
| experiment_id | Unique experiment identifier and primary key |
| experiment_name | Name of the experiment |
| hypothesis | Hypothesis being evaluated |
| primary_metric_key | Key identifying the primary success metric |
| randomization_unit | Unit used for randomization, defaulting to user |
| outcome_window_days | Number of days used to measure outcomes |
| allocation_ratio | Expected treatment allocation ratio |
| random_seed | Seed used for deterministic assignment generation |
| start_date | Experiment start date |
| end_date | Experiment end date |
| status | Current experiment lifecycle status |
| created_at | Experiment creation timestamp |

## 2. variants

Defines the control and treatment groups associated with experiments.

| Field | Description |
|---|---|
| variant_id | Unique variant identifier and primary key |
| experiment_id | Reference to the associated experiment |
| variant_name | Variant display name |
| variant_type | CONTROL or TREATMENT |
| allocation | Expected allocation proportion |

## 3. audience_members

Stores user attributes and eligibility information.

| Field | Description |
|---|---|
| user_id | Unique user identifier and primary key |
| country | User country |
| platform | User platform |
| acquisition_channel | User acquisition source |
| eligibility_status | ELIGIBLE or INELIGIBLE |
| created_at | User creation timestamp |

## 4. assignments

Records which experiment variant each user is assigned to.

| Field | Description |
|---|---|
| assignment_id | Unique assignment identifier and primary key |
| experiment_id | Associated experiment |
| variant_id | Assigned experiment variant |
| user_id | Assigned user |
| assigned_at | Assignment timestamp |
| assignment_status | ASSIGNED or REVOKED |
| compliance_status | Assignment exposure and telemetry compliance state |
| issue_type | Label identifying an assignment anomaly, when applicable |

## 5. exposure_events

Records whether an assigned user was exposed to the experiment.

| Field | Description |
|---|---|
| exposure_id | Unique exposure event identifier and primary key |
| assignment_id | Related assignment |
| user_id | Exposed user |
| experiment_id | Associated experiment |
| variant_id | Exposed variant |
| exposed_at | Exposure timestamp |
| telemetry_status | RECORDED or MISSING |
| issue_type | Label identifying an exposure anomaly, when applicable |

## 6. conversion_events

Stores user conversion outcomes and associated values.

| Field | Description |
|---|---|
| conversion_id | Unique conversion identifier and primary key |
| assignment_id | Related assignment |
| user_id | User associated with the conversion |
| experiment_id | Associated experiment |
| converted_at | Conversion timestamp |
| conversion_value | Monetary or numerical conversion value |
| conversion_status | CONVERTED or REVERSED |
| issue_type | Label identifying an outcome anomaly, when applicable |

## 7. metric_definitions

Defines the metrics used to evaluate experiment performance.

| Field | Description |
|---|---|
| metric_definition_id | Unique metric definition identifier and primary key |
| experiment_id | Associated experiment |
| metric_key | Unique metric key within its versioned definition |
| metric_name | Human-readable metric name |
| metric_type | BINARY, CONTINUOUS, or COUNT |
| numerator_field | Field used as the metric numerator |
| denominator_field | Field used as the metric denominator |
| metric_version | Version number of the metric definition |
| effective_from | Date the metric definition becomes effective |
| effective_to | Date the metric definition stops being effective |
| is_primary | Indicates whether the metric is the primary metric |

## 8. guardrail_metrics

Defines operational thresholds used to monitor unintended experiment effects.

| Field | Description |
|---|---|
| guardrail_id | Unique guardrail identifier and primary key |
| experiment_id | Associated experiment |
| metric_definition_id | Related metric definition |
| guardrail_name | Name of the monitored guardrail |
| threshold | Configured guardrail threshold |
| comparison_operator | MAX or MIN comparison |
| severity | WARNING or CRITICAL |

## 9. experiment_results

Stores the calculated experiment analysis results.

| Field | Description |
|---|---|
| result_id | Unique result identifier and primary key |
| experiment_id | Associated experiment |
| metric_definition_id | Metric used in the analysis |
| metric_version | Metric definition version used |
| control_rate | Measured control group rate |
| treatment_rate | Measured treatment group rate |
| absolute_lift | Absolute difference between treatment and control |
| relative_lift | Relative difference between treatment and control |
| p_value | Statistical significance measure |
| confidence_lower | Lower confidence interval bound |
| confidence_upper | Upper confidence interval bound |
| control_sample_size | Number of control assignments included |
| treatment_sample_size | Number of treatment assignments included |
| srm_detected | Indicates whether Sample Ratio Mismatch was detected |
| guardrail_status | Overall guardrail evaluation status |
| decision | Experiment analysis decision |
| analysis_plan | Analysis configuration or plan |
| computed_at | Result computation timestamp |

## 10. experiment_state_events

Maintains the history of experiment lifecycle transitions.

| Field | Description |
|---|---|
| state_event_id | Unique state event identifier and primary key |
| experiment_id | Associated experiment |
| previous_state | Previous lifecycle state |
| new_state | New lifecycle state |
| changed_at | State transition timestamp |
| changed_by | Actor responsible for the change |
| reason | Explanation for the transition |

## 11. support_events

Records support-related events associated with experiment participants.

| Field | Description |
|---|---|
| support_event_id | Unique support event identifier and primary key |
| assignment_id | Related assignment |
| user_id | User associated with the event |
| experiment_id | Associated experiment |
| occurred_at | Event timestamp |
| issue_category | Support issue category |

## 12. refund_events

Records refund events for experiment participants.

| Field | Description |
|---|---|
| refund_event_id | Unique refund event identifier and primary key |
| assignment_id | Related assignment |
| user_id | User associated with the refund |
| experiment_id | Associated experiment |
| occurred_at | Refund timestamp |
| refund_amount | Refund amount |

## Relationships and Integrity

The database uses primary keys to uniquely identify records and foreign keys to maintain relationships between experiments, variants, users, assignments, and events.

Important relationships include:

- One experiment can contain multiple variants.
- One experiment can have multiple assignments.
- Each assignment references an experiment, variant, and user.
- Exposure and conversion events reference their associated assignments.
- Metric definitions belong to experiments and support guardrail configurations.
- Experiment results reference the metric definition used for analysis.
- Support and refund events are associated with experiment assignments.

## Data Quality Considerations

The generated dataset includes labelled edge cases designed to test experiment integrity and analysis reliability.

The validation process checks primary-key uniqueness, foreign-key relationships, variant consistency, anomaly coverage, sample-size reconciliation, metric version preservation, and guardrail decision consistency.

The current generated dataset passed all 23 automated validation checks.