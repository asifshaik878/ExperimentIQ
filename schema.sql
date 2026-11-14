
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    experiment_name TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    primary_metric_key TEXT NOT NULL,
    randomization_unit TEXT NOT NULL DEFAULT 'user',
    outcome_window_days INTEGER NOT NULL CHECK(outcome_window_days > 0),
    allocation_ratio REAL NOT NULL DEFAULT 0.5 CHECK(allocation_ratio > 0 AND allocation_ratio < 1),
    random_seed INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('DRAFT', 'RUNNING', 'COMPLETED', 'PAUSED')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS variants (
    variant_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    variant_name TEXT NOT NULL,
    variant_type TEXT NOT NULL CHECK(variant_type IN ('CONTROL', 'TREATMENT')),
    allocation REAL NOT NULL CHECK(allocation > 0 AND allocation < 1),
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    UNIQUE(experiment_id, variant_name)
);

CREATE TABLE IF NOT EXISTS audience_members (
    user_id TEXT PRIMARY KEY,
    country TEXT NOT NULL,
    platform TEXT NOT NULL,
    acquisition_channel TEXT NOT NULL,
    eligibility_status TEXT NOT NULL CHECK(eligibility_status IN ('ELIGIBLE', 'INELIGIBLE')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assignments (
    assignment_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    variant_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    assignment_status TEXT NOT NULL CHECK(assignment_status IN ('ASSIGNED', 'REVOKED')),
    compliance_status TEXT NOT NULL CHECK(compliance_status IN ('PENDING', 'EXPOSED', 'NONCOMPLIANT', 'MISSING_TELEMETRY')),
    issue_type TEXT,
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY(variant_id) REFERENCES variants(variant_id),
    FOREIGN KEY(user_id) REFERENCES audience_members(user_id)
);

CREATE TABLE IF NOT EXISTS exposure_events (
    exposure_id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    variant_id TEXT NOT NULL,
    exposed_at TEXT NOT NULL,
    telemetry_status TEXT NOT NULL CHECK(telemetry_status IN ('RECORDED', 'MISSING')),
    issue_type TEXT,
    FOREIGN KEY(assignment_id) REFERENCES assignments(assignment_id),
    FOREIGN KEY(user_id) REFERENCES audience_members(user_id),
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY(variant_id) REFERENCES variants(variant_id)
);

CREATE TABLE IF NOT EXISTS conversion_events (
    conversion_id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    converted_at TEXT NOT NULL,
    conversion_value REAL NOT NULL CHECK(conversion_value >= 0),
    conversion_status TEXT NOT NULL CHECK(conversion_status IN ('CONVERTED', 'REVERSED')),
    issue_type TEXT,
    FOREIGN KEY(assignment_id) REFERENCES assignments(assignment_id),
    FOREIGN KEY(user_id) REFERENCES audience_members(user_id),
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id)
);

CREATE TABLE IF NOT EXISTS metric_definitions (
    metric_definition_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_type TEXT NOT NULL CHECK(metric_type IN ('BINARY', 'CONTINUOUS', 'COUNT')),
    numerator_field TEXT NOT NULL,
    denominator_field TEXT NOT NULL,
    metric_version INTEGER NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    is_primary INTEGER NOT NULL CHECK(is_primary IN (0, 1)),
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    UNIQUE(experiment_id, metric_key, metric_version)
);

CREATE TABLE IF NOT EXISTS guardrail_metrics (
    guardrail_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    metric_definition_id TEXT NOT NULL,
    guardrail_name TEXT NOT NULL,
    threshold REAL NOT NULL,
    comparison_operator TEXT NOT NULL CHECK(comparison_operator IN ('MAX', 'MIN')),
    severity TEXT NOT NULL CHECK(severity IN ('WARNING', 'CRITICAL')),
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY(metric_definition_id) REFERENCES metric_definitions(metric_definition_id)
);

CREATE TABLE IF NOT EXISTS experiment_results (
    result_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    metric_definition_id TEXT NOT NULL,
    metric_version INTEGER NOT NULL,
    control_rate REAL NOT NULL,
    treatment_rate REAL NOT NULL,
    absolute_lift REAL NOT NULL,
    relative_lift REAL,
    p_value REAL,
    confidence_lower REAL,
    confidence_upper REAL,
    control_sample_size INTEGER NOT NULL,
    treatment_sample_size INTEGER NOT NULL,
    srm_detected INTEGER NOT NULL CHECK(srm_detected IN (0, 1)),
    guardrail_status TEXT NOT NULL,
    decision TEXT NOT NULL,
    analysis_plan TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id),
    FOREIGN KEY(metric_definition_id) REFERENCES metric_definitions(metric_definition_id)
);

CREATE TABLE IF NOT EXISTS experiment_state_events (
    state_event_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    previous_state TEXT,
    new_state TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id)
);

CREATE TABLE IF NOT EXISTS support_events (
    support_event_id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    issue_category TEXT NOT NULL,
    FOREIGN KEY(assignment_id) REFERENCES assignments(assignment_id),
    FOREIGN KEY(user_id) REFERENCES audience_members(user_id),
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id)
);

CREATE TABLE IF NOT EXISTS refund_events (
    refund_event_id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    refund_amount REAL NOT NULL CHECK(refund_amount >= 0),
    FOREIGN KEY(assignment_id) REFERENCES assignments(assignment_id),
    FOREIGN KEY(user_id) REFERENCES audience_members(user_id),
    FOREIGN KEY(experiment_id) REFERENCES experiments(experiment_id)
);

CREATE INDEX IF NOT EXISTS idx_assignments_experiment ON assignments(experiment_id);
CREATE INDEX IF NOT EXISTS idx_assignments_user ON assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_exposures_assignment ON exposure_events(assignment_id);
CREATE INDEX IF NOT EXISTS idx_conversions_assignment ON conversion_events(assignment_id);
CREATE INDEX IF NOT EXISTS idx_results_experiment ON experiment_results(experiment_id);
CREATE INDEX IF NOT EXISTS idx_metrics_experiment ON metric_definitions(experiment_id);
