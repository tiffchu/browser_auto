"""Fail closed on uncertain metrics while retaining every company in output."""

from copy import deepcopy
from datetime import date
from math import isfinite


METRICS = ("revenue", "net_income", "total_assets")
MANUAL = "needs_manual_input"


def pending_record(company: dict, year: int, reason: str) -> dict:
    return {
        "company_id": company["company_id"], "company_name": company["company_name"],
        "fiscal_year": year, "fiscal_year_end": None, "publication_date": None,
        "audited": False, "original_verified": False, "auditor_evidence_pdf_page": None,
        "source_url": None, "pdf_filename": None, "status": MANUAL, "review_notes": reason,
        "net_income_measure": "unresolved", "net_income_basis": "unresolved", "net_income_derivation": "",
        **{metric: {"value": None, "currency": None, "unit_multiplier": None,
                    "pdf_page": None, "printed_page": None, "source_label": None,
                    "status": MANUAL, "review_note": reason} for metric in METRICS},
    }


def prepare_record(record: dict, target_year: int) -> dict:
    """Clear uncertain candidate values. Store candidates separately if needed.

    A ready flag is a review assertion, never a substitute for PDF verification.
    """
    result = deepcopy(record)
    global_reasons = []
    try:
        end = date.fromisoformat(result["fiscal_year_end"] or "")
    except (TypeError, ValueError):
        end = None
    if result["fiscal_year"] != target_year or end is None or end.year != target_year:
        global_reasons.append(f"Fiscal year end must fall in {target_year}.")
    if not result["audited"] or not result["auditor_evidence_pdf_page"]:
        global_reasons.append("Audited status needs evidence.")
    if not result["original_verified"]:
        global_reasons.append("Original statement version is unverified.")
    if not result["publication_date"] or not result["pdf_filename"]:
        global_reasons.append("Source PDF and original publication date are required.")
    for metric in METRICS:
        item = result[metric]
        reasons = list(global_reasons)
        if item["status"] != "ready":
            reasons.append(item["review_note"] or "Metric is uncertain.")
        value = item["value"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            reasons.append("No certain numeric value.")
        if any(item[key] is None or item[key] == "" for key in
               ("currency", "unit_multiplier", "pdf_page", "source_label")):
            reasons.append("Currency, units, or page/line evidence is missing.")
        if metric == "net_income":
            if result["net_income_measure"] != "reported_net_income":
                reasons.append("Use reported net income/loss; comprehensive income is excluded.")
            if "comprehensive" in (item["source_label"] or "").casefold():
                reasons.append("Source label refers to comprehensive income/loss; locate the net income/loss line.")
            if result["net_income_basis"] != "consolidated_total" or not result["net_income_derivation"].strip():
                reasons.append("Reported consolidated net income and a source-based explanation are required.")
        if reasons:
            item.update(value=None, status=MANUAL, review_note=" ".join(dict.fromkeys(reasons)))
    result["status"] = "ready" if all(result[key]["status"] == "ready" for key in METRICS) else MANUAL
    if result["status"] == MANUAL:
        notes = [result["review_notes"]] if result["review_notes"] else []
        notes.extend(f"{key}: {result[key]['review_note']}" for key in METRICS
                     if result[key]["status"] == MANUAL)
        result["review_notes"] = " ".join(dict.fromkeys(notes))
    return result
