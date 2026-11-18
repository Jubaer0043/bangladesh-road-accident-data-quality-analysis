"""Descriptive effects and explicitly conditional resampling; no population-risk inference."""

import numpy as np
import pandas as pd
from scipy import stats


def contingency_effect(frame, predictor):
    complete = frame[[predictor, "fatal_record"]].dropna()
    table = pd.crosstab(complete[predictor], complete.fatal_record).reindex(
        columns=[0, 1], fill_value=0
    )
    if min(table.shape) < 2:
        return {"field": predictor, "estimable": False}
    chi2, _, dof, expected = stats.chi2_contingency(table.to_numpy(), correction=False)
    n = table.to_numpy().sum()
    return {
        "field": predictor,
        "estimable": True,
        "records": int(n),
        "chi_square_discrepancy": float(chi2),
        "degrees_of_freedom": int(dof),
        "min_expected_cell": float(expected.min()),
        "cramers_v": float(
            np.sqrt(chi2 / (n * min(table.shape[0] - 1, table.shape[1] - 1)))
        ),
        "p_value_reported": False,
        "reason": "Independent verified incident units and measurement validity are not established; descriptive effect only",
    }


def night_day_effect(frame, field="lighting"):
    group = frame.groupby(field).fatal_record.agg(["sum", "count"])
    if not {"Day", "Night"}.issubset(group.index):
        raise ValueError("Both Day and Night groups are needed")
    p_day, p_night = (
        float(group.loc[k, "sum"] / group.loc[k, "count"]) for k in ["Day", "Night"]
    )
    return {
        "field": field,
        "day_records": int(group.loc["Day", "count"]),
        "night_records": int(group.loc["Night", "count"]),
        "day_fatal_record_share": p_day,
        "night_fatal_record_share": p_night,
        "difference_night_minus_day": p_night - p_day,
    }


def conditional_cluster_interval(frame, repetitions=2000, seed=42):
    """Conditional 95% bootstrap interval for the file's Night−Day association.

    Descriptor groups are computational clusters, not verified accidents. This interval
    does not quantify uncertainty in true accidents, reporting accuracy, or population risk.
    """
    d = frame.loc[frame.lighting.isin(["Day", "Night"])].copy()
    d["n_night"] = d.lighting.eq("Night").astype(int)
    d["f_night"] = d.n_night * d.fatal_record
    d["n_day"] = d.lighting.eq("Day").astype(int)
    d["f_day"] = d.n_day * d.fatal_record
    totals = (
        d.groupby("descriptor_group")[["n_night", "f_night", "n_day", "f_day"]]
        .sum()
        .to_numpy()
    )
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(repetitions):
        nn, fn, nd, fd = totals[rng.integers(0, len(totals), len(totals))].sum(axis=0)
        if nn and nd:
            estimates.append(fn / nn - fd / nd)
    if len(estimates) < repetitions * 0.95:
        raise ValueError("Too few usable descriptor-cluster resamples")
    lower, upper = np.quantile(estimates, [0.025, 0.975])
    return {
        "confidence_level_conditional_model": 0.95,
        "lower": float(lower),
        "upper": float(upper),
        "descriptor_clusters": len(totals),
        "repetitions": repetitions,
        "seed": seed,
        "interpretation": "Conditional percentile bootstrap for published descriptor groups; NOT a validated incident-level or population-risk confidence interval",
    }


def descriptor_bounds(frame):
    """If each descriptor group were one incident, conflicting values give identification bounds.

    This is an explicit what-if assumption; endpoints are not confidence limits or estimated unique accidents.
    """
    groups = frame.groupby("descriptor_group").fatal_record.agg(["min", "max"])
    return {
        "descriptor_groups": len(groups),
        "fatal_share_lower": float(groups["min"].mean()),
        "fatal_share_upper": float(groups["max"].mean()),
        "interpretation": "Conditional min/max bounds if each descriptor group represented one incident; NOT confidence limits",
    }
