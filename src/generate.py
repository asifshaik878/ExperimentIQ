
import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chisquare, norm


SEED = 20261022
BASE_DATE = datetime(2026, 10, 1)
EXPERIMENT_COUNT = 10

SCENARIOS = [
    "BALANCED",
    "UNBALANCED",
    "SAMPLE_RATIO_MISMATCH",
    "DELAYED_CONVERSION",
    "GUARDRAIL_REGRESSION",
    "NORMAL_EFFECT",
    "LOW_EFFECT",
    "REFUND_REGRESSION",
    "MISSING_TELEMETRY",
    "MULTIPLE_ANOMALIES"
]


def make_id(prefix, number, width=6):
    return f"{prefix}{number:0{width}d}"


def format_date(value):
    return value.isoformat(timespec="seconds")


def calculate_statistics(control, treatment):
    control = np.asarray(control, dtype=int)
    treatment = np.asarray(treatment, dtype=int)

    control_size = len(control)
    treatment_size = len(treatment)

    control_rate = float(control.mean())
    treatment_rate = float(treatment.mean())

    absolute_lift = treatment_rate - control_rate

    relative_lift = (
        absolute_lift / control_rate
        if control_rate > 0 else None
    )

    standard_error = np.sqrt(
        control_rate * (1 - control_rate) / control_size
        + treatment_rate * (1 - treatment_rate) / treatment_size
    )

    if standard_error == 0:
        p_value = 1.0
    else:
        z_score = absolute_lift / standard_error
        p_value = float(2 * norm.sf(abs(z_score)))

    margin = 1.96 * standard_error

    return {
        "control_rate": control_rate,
        "treatment_rate": treatment_rate,
        "absolute_lift": absolute_lift,
        "relative_lift": relative_lift,
        "p_value": p_value,
        "confidence_lower": absolute_lift - margin,
        "confidence_upper": absolute_lift + margin,
        "control_sample_size": control_size,
        "treatment_sample_size": treatment_size
    }


def check_sample_ratio(control_count, treatment_count, control_allocation):
    total = control_count + treatment_count

    expected = [
        total * control_allocation,
        total * (1 - control_allocation)
    ]

    observed = [control_count, treatment_count]

    statistic, p_value = chisquare(
        f_obs=observed,
        f_exp=expected
    )

    return {
        "srm_detected": bool(p_value < 0.001),
        "srm_p_value": float(p_value),
        "chi_square_statistic": float(statistic),
        "observed_control_ratio": control_count / total,
        "expected_control_ratio": control_allocation
    }


def generate_experiment_data(users_per_experiment, seed):
    rng = np.random.default_rng(seed)

    data = {
        "experiments": [],
        "variants": [],
        "audience_members": [],
        "assignments": [],
        "exposure_events": [],
        "conversion_events": [],
        "metric_definitions": [],
        "guardrail_metrics": [],
        "experiment_results": [],
        "experiment_state_events": [],
        "support_events": [],
        "refund_events": [],
        "ground_truth": []
    }

    user_counter = 0
    exposure_counter = 0
    conversion_counter = 0
    support_counter = 0
    refund_counter = 0

    for experiment_number, scenario in enumerate(SCENARIOS, start=1):
        experiment_id = f"EXP-2026-{experiment_number:06d}"
        control_id = f"VAR-{experiment_id}-A"
        treatment_id = f"VAR-{experiment_id}-B"

        start_date = BASE_DATE + timedelta(
            days=(experiment_number - 1) * 2
        )

        end_date = start_date + timedelta(days=30)
        result_date = end_date + timedelta(days=31)

        control_allocation = (
            0.65 if scenario == "UNBALANCED" else 0.5
        )

        assignment_probability = control_allocation

        if scenario == "SAMPLE_RATIO_MISMATCH":
            assignment_probability = 0.62

        data["experiments"].append({
            "experiment_id": experiment_id,
            "experiment_name": scenario.replace("_", " ").title(),
            "hypothesis": (
                "The treatment experience will improve conversion "
                "without increasing customer support or refund rates."
            ),
            "primary_metric_key": "conversion_rate",
            "randomization_unit": "user",
            "outcome_window_days": 30,
            "allocation_ratio": control_allocation,
            "random_seed": seed + experiment_number,
            "start_date": format_date(start_date),
            "end_date": format_date(end_date),
            "status": "COMPLETED",
            "created_at": format_date(start_date - timedelta(days=2))
        })

        data["variants"].extend([
            {
                "variant_id": control_id,
                "experiment_id": experiment_id,
                "variant_name": "Control",
                "variant_type": "CONTROL",
                "allocation": control_allocation
            },
            {
                "variant_id": treatment_id,
                "experiment_id": experiment_id,
                "variant_name": "Treatment",
                "variant_type": "TREATMENT",
                "allocation": 1 - control_allocation
            }
        ])

        state_changes = [
            (None, "DRAFT", start_date - timedelta(days=2), "Experiment created"),
            ("DRAFT", "RUNNING", start_date, "Experiment launched"),
            ("RUNNING", "COMPLETED", end_date, "Outcome window closed")
        ]

        for event_number, (previous, new, changed_at, reason) in enumerate(
            state_changes, start=1
        ):
            data["experiment_state_events"].append({
                "state_event_id": (
                    f"STATE-{experiment_number:06d}-{event_number:02d}"
                ),
                "experiment_id": experiment_id,
                "previous_state": previous,
                "new_state": new,
                "changed_at": format_date(changed_at),
                "changed_by": "system",
                "reason": reason
            })

        metric_ids = {
            "conversion_rate": f"MET-{experiment_number:06d}-01",
            "support_rate": f"MET-{experiment_number:06d}-02",
            "refund_rate": f"MET-{experiment_number:06d}-03"
        }

        metric_specs = [
            ("conversion_rate", "Conversion Rate", "BINARY", "converted", "assigned", 1),
            ("support_rate", "Support Contact Rate", "BINARY", "support_contact", "assigned", 0),
            ("refund_rate", "Refund Rate", "BINARY", "refund", "assigned", 0)
        ]

        for key, name, metric_type, numerator, denominator, primary in metric_specs:
            data["metric_definitions"].append({
                "metric_definition_id": metric_ids[key],
                "experiment_id": experiment_id,
                "metric_key": key,
                "metric_name": name,
                "metric_type": metric_type,
                "numerator_field": numerator,
                "denominator_field": denominator,
                "metric_version": 1,
                "effective_from": format_date(start_date),
                "effective_to": None,
                "is_primary": primary
            })

        data["guardrail_metrics"].extend([
            {
                "guardrail_id": f"GR-{experiment_number:06d}-01",
                "experiment_id": experiment_id,
                "metric_definition_id": metric_ids["support_rate"],
                "guardrail_name": "Support Contact Rate",
                "threshold": 0.08,
                "comparison_operator": "MAX",
                "severity": "CRITICAL"
            },
            {
                "guardrail_id": f"GR-{experiment_number:06d}-02",
                "experiment_id": experiment_id,
                "metric_definition_id": metric_ids["refund_rate"],
                "guardrail_name": "Refund Rate",
                "threshold": 0.05,
                "comparison_operator": "MAX",
                "severity": "CRITICAL"
            }
        ])

        user_ids = []
        assignment_ids = []
        variant_types = []
        conversion_outcomes = []
        support_outcomes = []
        refund_outcomes = []
        assigned_dates = []

        for local_user in range(users_per_experiment):
            user_counter += 1

            user_id = make_id("USR-2026-", user_counter)

            is_control = rng.random() < assignment_probability

            variant_type = "CONTROL" if is_control else "TREATMENT"
            variant_id = control_id if is_control else treatment_id

            assigned_at = start_date + timedelta(
                seconds=int(rng.integers(0, 30 * 24 * 60 * 60))
            )

            assignment_id = f"ASG-{experiment_id}-{user_id}"

            data["audience_members"].append({
                "user_id": user_id,
                "country": rng.choice(["IN", "US", "UK", "CA", "AU"]),
                "platform": rng.choice(["WEB", "ANDROID", "IOS"]),
                "acquisition_channel": rng.choice([
                    "ORGANIC", "PAID", "REFERRAL", "EMAIL"
                ]),
                "eligibility_status": "ELIGIBLE",
                "created_at": format_date(assigned_at - timedelta(days=5))
            })

            exposure_draw = rng.random()

            if exposure_draw < 0.04:
                compliance_status = "NONCOMPLIANT"
                telemetry_status = None
            elif exposure_draw < 0.07:
                compliance_status = "MISSING_TELEMETRY"
                telemetry_status = "MISSING"
            else:
                compliance_status = "EXPOSED"
                telemetry_status = "RECORDED"

            data["assignments"].append({
                "assignment_id": assignment_id,
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "user_id": user_id,
                "assigned_at": format_date(assigned_at),
                "assignment_status": "ASSIGNED",
                "compliance_status": compliance_status,
                "issue_type": None
            })

            if compliance_status != "NONCOMPLIANT":
                exposure_counter += 1

                exposure_time = assigned_at + timedelta(
                    minutes=int(rng.integers(1, 1440))
                )

                data["exposure_events"].append({
                    "exposure_id": make_id("EXPOS-2026-", exposure_counter),
                    "assignment_id": assignment_id,
                    "user_id": user_id,
                    "experiment_id": experiment_id,
                    "variant_id": variant_id,
                    "exposed_at": format_date(exposure_time),
                    "telemetry_status": telemetry_status,
                    "issue_type": None
                })

            conversion_probability = 0.10

            if variant_type == "TREATMENT":
                if scenario == "LOW_EFFECT":
                    conversion_probability += 0.001
                else:
                    conversion_probability += 0.025

            converted = rng.random() < conversion_probability
            conversion_in_window = converted

            if converted:
                conversion_counter += 1

                conversion_days = int(rng.integers(1, 26))
                issue_type = None

                if scenario == "DELAYED_CONVERSION" and local_user % 100 == 0:
                    conversion_days = 40
                    issue_type = "OUTCOME_WINDOW_INCONSISTENT"
                    conversion_in_window = False

                conversion_time = assigned_at + timedelta(
                    days=conversion_days
                )

                data["conversion_events"].append({
                    "conversion_id": make_id("CONV-2026-", conversion_counter),
                    "assignment_id": assignment_id,
                    "user_id": user_id,
                    "experiment_id": experiment_id,
                    "converted_at": format_date(conversion_time),
                    "conversion_value": round(float(rng.uniform(10, 250)), 2),
                    "conversion_status": "CONVERTED",
                    "issue_type": issue_type
                })

                if issue_type:
                    data["ground_truth"].append({
                        "issue_id": make_id("ISSUE-", len(data["ground_truth"]) + 1),
                        "experiment_id": experiment_id,
                        "user_id": user_id,
                        "issue_type": issue_type,
                        "expected_decision": "EXCLUDE_FROM_PRIMARY_WINDOW",
                        "observed_decision": "FLAGGED_FOR_REVIEW",
                        "description": (
                            "Conversion occurred after the declared "
                            "30-day outcome window."
                        )
                    })

            support_probability = 0.035
            refund_probability = 0.015

            if variant_type == "TREATMENT" and scenario in (
                "GUARDRAIL_REGRESSION",
                "MULTIPLE_ANOMALIES"
            ):
                support_probability = 0.15

            if variant_type == "TREATMENT" and scenario == "REFUND_REGRESSION":
                refund_probability = 0.10

            has_support = rng.random() < support_probability
            has_refund = rng.random() < refund_probability

            if has_support:
                support_counter += 1

                data["support_events"].append({
                    "support_event_id": make_id("SUP-2026-", support_counter),
                    "assignment_id": assignment_id,
                    "user_id": user_id,
                    "experiment_id": experiment_id,
                    "occurred_at": format_date(
                        assigned_at + timedelta(days=2)
                    ),
                    "issue_category": rng.choice([
                        "DELIVERY", "PAYMENT", "PRODUCT", "ACCOUNT"
                    ])
                })

            if has_refund:
                refund_counter += 1

                data["refund_events"].append({
                    "refund_event_id": make_id("REF-2026-", refund_counter),
                    "assignment_id": assignment_id,
                    "user_id": user_id,
                    "experiment_id": experiment_id,
                    "occurred_at": format_date(
                        assigned_at + timedelta(days=5)
                    ),
                    "refund_amount": round(
                        float(rng.uniform(5, 150)), 2
                    )
                })

            user_ids.append(user_id)
            assignment_ids.append(assignment_id)
            variant_types.append(variant_type)
            conversion_outcomes.append(int(conversion_in_window))
            support_outcomes.append(int(has_support))
            refund_outcomes.append(int(has_refund))
            assigned_dates.append(assigned_at)

        control_mask = np.array(variant_types) == "CONTROL"
        treatment_mask = np.array(variant_types) == "TREATMENT"

        conversion_array = np.array(conversion_outcomes)
        support_array = np.array(support_outcomes)
        refund_array = np.array(refund_outcomes)

        control_count = int(control_mask.sum())
        treatment_count = int(treatment_mask.sum())

        statistics = calculate_statistics(
            conversion_array[control_mask],
            conversion_array[treatment_mask]
        )

        randomization = check_sample_ratio(
            control_count,
            treatment_count,
            control_allocation
        )

        control_support = float(support_array[control_mask].mean())
        treatment_support = float(support_array[treatment_mask].mean())

        control_refund = float(refund_array[control_mask].mean())
        treatment_refund = float(refund_array[treatment_mask].mean())

        support_failed = treatment_support > 0.08
        refund_failed = treatment_refund > 0.05

        guardrail_status = (
            "FAIL"
            if support_failed or refund_failed
            else "PASS"
        )

        if randomization["srm_detected"]:
            decision = "HOLD_SRM"
        elif guardrail_status == "FAIL":
            decision = "STOP_GUARDRAIL"
        elif statistics["p_value"] < 0.05 and statistics["absolute_lift"] > 0:
            decision = "SHIP"
        else:
            decision = "NO_CLEAR_WIN"

        data["experiment_results"].append({
            "result_id": f"RES-{experiment_number:06d}-01",
            "experiment_id": experiment_id,
            "metric_definition_id": metric_ids["conversion_rate"],
            "metric_version": 1,
            **statistics,
            "srm_detected": int(randomization["srm_detected"]),
            "guardrail_status": guardrail_status,
            "decision": decision,
            "analysis_plan": (
                "Intention-to-Treat; binary conversion; two-sided "
                "two-proportion z-test; 95% confidence interval; "
                "30-day outcome window; SRM significance level 0.001."
            ),
            "computed_at": format_date(result_date)
        })

        if scenario == "SAMPLE_RATIO_MISMATCH":
            data["ground_truth"].append({
                "issue_id": make_id("ISSUE-", len(data["ground_truth"]) + 1),
                "experiment_id": experiment_id,
                "user_id": None,
                "issue_type": "SAMPLE_RATIO_MISMATCH_IGNORED",
                "expected_decision": "HOLD_SRM",
                "observed_decision": "SHIP",
                "system_decision": decision,
                "description": (
                    "A simulated legacy recommendation ignored the "
                    "allocation mismatch. The validation engine must "
                    "block shipping and hold the experiment."
                )
            })

        if scenario == "MULTIPLE_ANOMALIES":
            duplicate_user = user_ids[0]
            original_assignment = assignment_ids[0]
            original_variant = variant_types[0]

            duplicate_variant = (
                treatment_id
                if original_variant == "CONTROL"
                else control_id
            )

            duplicate_assignment = (
                f"ASG-{experiment_id}-{duplicate_user}-ANOM-01"
            )

            data["assignments"].append({
                "assignment_id": duplicate_assignment,
                "experiment_id": experiment_id,
                "variant_id": duplicate_variant,
                "user_id": duplicate_user,
                "assigned_at": format_date(start_date),
                "assignment_status": "ASSIGNED",
                "compliance_status": "PENDING",
                "issue_type": "MULTIPLE_VARIANT_ASSIGNMENT"
            })

            original_assignment_date = assigned_dates[0]

            exposure_counter += 1

            data["exposure_events"].append({
                "exposure_id": make_id("EXPOS-2026-", exposure_counter),
                "assignment_id": original_assignment,
                "user_id": duplicate_user,
                "experiment_id": experiment_id,
                "variant_id": (
                    control_id if original_variant == "CONTROL"
                    else treatment_id
                ),
                "exposed_at": format_date(
                    original_assignment_date - timedelta(minutes=10)
                ),
                "telemetry_status": "RECORDED",
                "issue_type": "EXPOSURE_BEFORE_ASSIGNMENT"
            })

            data["ground_truth"].extend([
                {
                    "issue_id": make_id("ISSUE-", len(data["ground_truth"]) + 1),
                    "experiment_id": experiment_id,
                    "user_id": duplicate_user,
                    "issue_type": "MULTIPLE_VARIANT_ASSIGNMENT",
                    "expected_decision": "FLAG_AND_EXCLUDE_USER",
                    "observed_decision": "FLAGGED_FOR_REVIEW",
                    "description": (
                        "The same user has assignments to both experiment variants."
                    )
                },
                {
                    "issue_id": make_id("ISSUE-", len(data["ground_truth"]) + 2),
                    "experiment_id": experiment_id,
                    "user_id": duplicate_user,
                    "issue_type": "EXPOSURE_BEFORE_ASSIGNMENT",
                    "expected_decision": "FLAG_INVALID_EXPOSURE",
                    "observed_decision": "FLAGGED_FOR_REVIEW",
                    "description": (
                        "The exposure timestamp precedes the assignment timestamp."
                    )
                }
            ])

            data["metric_definitions"].append({
                "metric_definition_id": f"MET-{experiment_number:06d}-04",
                "experiment_id": experiment_id,
                "metric_key": "conversion_rate",
                "metric_name": "Conversion Rate Revised",
                "metric_type": "BINARY",
                "numerator_field": "converted",
                "denominator_field": "assigned",
                "metric_version": 2,
                "effective_from": format_date(
                    result_date + timedelta(days=1)
                ),
                "effective_to": None,
                "is_primary": 1
            })

            data["ground_truth"].append({
                "issue_id": make_id("ISSUE-", len(data["ground_truth"]) + 3),
                "experiment_id": experiment_id,
                "user_id": None,
                "issue_type": "METRIC_DEFINITION_CHANGED_AFTER_RESULTS",
                "expected_decision": "PRESERVE_VERSION_1_RESULT",
                "observed_decision": "VERSION_1_PRESERVED",
                "description": (
                    "Metric version 2 becomes effective after the version 1 "
                    "result has been calculated."
                )
            })

    return data


def validate_data(data):
    checks = {}

    primary_keys = {
        "experiments": "experiment_id",
        "variants": "variant_id",
        "audience_members": "user_id",
        "assignments": "assignment_id",
        "exposure_events": "exposure_id",
        "conversion_events": "conversion_id",
        "metric_definitions": "metric_definition_id",
        "guardrail_metrics": "guardrail_id",
        "experiment_results": "result_id",
        "experiment_state_events": "state_event_id",
        "support_events": "support_event_id",
        "refund_events": "refund_event_id"
    }

    for table, key in primary_keys.items():
        values = [record[key] for record in data[table]]
        checks[f"{table}_primary_key_unique"] = (
            len(values) == len(set(values))
        )

    experiment_ids = {
        item["experiment_id"] for item in data["experiments"]
    }

    variant_map = {
        item["variant_id"]: item["experiment_id"]
        for item in data["variants"]
    }

    user_ids = {
        item["user_id"] for item in data["audience_members"]
    }

    assignment_map = {
        item["assignment_id"]: item for item in data["assignments"]
    }

    metric_map = {
        item["metric_definition_id"]: item
        for item in data["metric_definitions"]
    }

    checks["variant_experiment_relationships"] = all(
        item["experiment_id"] in experiment_ids
        for item in data["variants"]
    )

    checks["assignment_foreign_keys"] = all(
        item["user_id"] in user_ids
        and item["experiment_id"] in experiment_ids
        and variant_map.get(item["variant_id"]) == item["experiment_id"]
        for item in data["assignments"]
    )

    checks["exposure_foreign_keys"] = all(
        item["assignment_id"] in assignment_map
        and item["user_id"] == assignment_map[item["assignment_id"]]["user_id"]
        and item["experiment_id"] == assignment_map[item["assignment_id"]]["experiment_id"]
        and item["variant_id"] == assignment_map[item["assignment_id"]]["variant_id"]
        for item in data["exposure_events"]
    )

    checks["conversion_foreign_keys"] = all(
        item["assignment_id"] in assignment_map
        and item["user_id"] == assignment_map[item["assignment_id"]]["user_id"]
        and item["experiment_id"] == assignment_map[item["assignment_id"]]["experiment_id"]
        for item in data["conversion_events"]
    )

    checks["metric_foreign_keys"] = all(
        item["experiment_id"] in experiment_ids
        for item in data["metric_definitions"]
    )

    checks["guardrail_foreign_keys"] = all(
        item["experiment_id"] in experiment_ids
        and item["metric_definition_id"] in metric_map
        for item in data["guardrail_metrics"]
    )

    checks["result_foreign_keys"] = all(
        item["experiment_id"] in experiment_ids
        and item["metric_definition_id"] in metric_map
        and item["metric_version"] == metric_map[item["metric_definition_id"]]["metric_version"]
        for item in data["experiment_results"]
    )

    checks["required_anomaly_types"] = {
        "MULTIPLE_VARIANT_ASSIGNMENT",
        "EXPOSURE_BEFORE_ASSIGNMENT",
        "OUTCOME_WINDOW_INCONSISTENT",
        "SAMPLE_RATIO_MISMATCH_IGNORED",
        "METRIC_DEFINITION_CHANGED_AFTER_RESULTS"
    }.issubset({
        item["issue_type"] for item in data["ground_truth"]
    })

    checks["result_sample_sizes_reconcile"] = all(
        item["control_sample_size"] + item["treatment_sample_size"]
        == sum(
            1 for assignment in data["assignments"]
            if assignment["experiment_id"] == item["experiment_id"]
            and assignment["issue_type"] is None
            and assignment["assignment_status"] == "ASSIGNED"
        )
        for item in data["experiment_results"]
    )

    checks["metric_versions_preserved"] = all(
        item["metric_version"] == 1
        for item in data["experiment_results"]
    )

    checks["guardrail_decisions_reconcile"] = all(
        not item["srm_detected"] or item["decision"] == "HOLD_SRM"
        for item in data["experiment_results"]
    )

    failed = [name for name, passed in checks.items() if not passed]

    if failed:
        raise ValueError(f"Data validation failed: {failed}")

    return checks


def export_dataset(data, output_directory, seed, users_per_experiment):
    output_directory.mkdir(parents=True, exist_ok=True)

    database_path = output_directory / "experimentiq.db"
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    if database_path.exists():
        database_path.unlink()

    row_counts = {}

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            schema_path.read_text(encoding="utf-8")
        )

        for table_name, records in data.items():
            if table_name == "ground_truth":
                continue

            if not records:
                continue

            columns = list(records[0].keys())
            column_names = ", ".join(columns)
            placeholders = ", ".join("?" for _ in columns)

            query = (
                f"INSERT INTO {table_name} "
                f"({column_names}) VALUES ({placeholders})"
            )

            values = [
                tuple(record[column] for column in columns)
                for record in records
            ]

            connection.executemany(query, values)
            row_counts[table_name] = len(records)

        foreign_key_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if foreign_key_errors:
            raise ValueError(
                f"Foreign key errors: {foreign_key_errors[:5]}"
            )

        if integrity != "ok":
            raise ValueError(f"Database integrity failed: {integrity}")

        connection.commit()

    for table_name, records in data.items():
        frame = pd.DataFrame(records)
        frame.to_csv(
            output_directory / f"{table_name}.csv",
            index=False
        )

    ground_truth_frame = pd.DataFrame(data["ground_truth"])

    ground_truth_frame.to_csv(
        output_directory / "ground_truth.csv",
        index=False
    )

    with open(
        output_directory / "ground_truth.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(data["ground_truth"], file, indent=2)

    validation = validate_data(data)

    with open(
        output_directory / "validation_summary.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump({
            "status": "PASSED",
            "checks": validation
        }, file, indent=2)

    checksums = {}

    for path in sorted(output_directory.glob("*.csv")):
        checksums[path.name] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()

    checksums["ground_truth.json"] = hashlib.sha256(
        (output_directory / "ground_truth.json").read_bytes()
    ).hexdigest()

    manifest = {
        "project": "ExperimentIQ",
        "seed": seed,
        "users_per_experiment": users_per_experiment,
        "experiment_count": EXPERIMENT_COUNT,
        "total_eligible_users": len(data["audience_members"]),
        "database": database_path.name,
        "row_counts": row_counts,
        "source": "Deterministic synthetic data generator",
        "external_data_used": False,
        "validation_status": "PASSED",
        "checksums": checksums
    }

    with open(
        output_directory / "manifest.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(manifest, file, indent=2)

    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Generate the ExperimentIQ synthetic dataset"
    )

    parser.add_argument(
        "--out",
        default="outputs"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=SEED
    )

    parser.add_argument(
        "--users-per-experiment",
        type=int,
        default=5000
    )

    args = parser.parse_args()

    if args.users_per_experiment < 100:
        raise ValueError("Use at least 100 users per experiment")

    data = generate_experiment_data(
        args.users_per_experiment,
        args.seed
    )

    manifest = export_dataset(
        data,
        Path(args.out),
        args.seed,
        args.users_per_experiment
    )

    print("\nExperimentIQ data generation completed")
    print("---------------------------------------")
    print(f"Experiments: {manifest['experiment_count']}")
    print(f"Eligible users: {manifest['total_eligible_users']:,}")

    for table, count in manifest["row_counts"].items():
        print(f"{table}: {count:,}")

    print(f"Ground-truth anomalies: {len(data['ground_truth']):,}")
    print(f"Database: {args.out}/experimentiq.db")
    print("Validation: PASSED")


if __name__ == "__main__":
    main()
