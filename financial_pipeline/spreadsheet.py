from pathlib import Path


METRICS = ("revenue", "net_income", "total_assets")


def write_workbook(records: list[dict], destination: Path) -> None:
    """Export reviewed records to a new workbook; retain per-metric evidence.

    Callers must validate records against schemas/financial_record.schema.json.
    Existing-workbook updates and template mapping remain out of scope.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font

    if not records:
        raise ValueError("No reviewed financial records to export.")
    for record in records:
        if record["status"] != "ready":
            raise ValueError("Only ready records may be exported.")
        required = ("fiscal_year_end", "publication_date", "auditor_evidence_pdf_page")
        if any(record[key] is None for key in required):
            raise ValueError("Report date, fiscal year end, and auditor evidence are required.")
        if not record["audited"] or not record["latest_verified"]:
            raise ValueError("Audited status and report recency must be verified.")
        for metric in METRICS:
            fields = ("value", "currency", "unit_multiplier", "pdf_page", "source_label")
            if any(record[metric][key] is None for key in fields):
                raise ValueError(f"Missing required evidence for {metric}.")

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Financials"
    base = ["company_id", "company_name", "fiscal_year", "fiscal_year_end",
            "publication_date", "auditor_evidence_pdf_page", "source_url", "pdf_filename"]
    fields = ["value", "currency", "unit_multiplier", "pdf_page", "printed_page", "source_label"]
    sheet.append(base + [f"{metric}_{field}" for metric in METRICS for field in fields])
    for record in records:
        row = [record[key] for key in base]
        row += [record[metric][field] for metric in METRICS for field in fields]
        sheet.append(row)
    # Treat issuer names, paths, and extracted labels as literal text.
    for row in sheet.iter_rows():
        for cell in row:
            if isinstance(cell.value, str):
                cell.data_type = "s"
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    sheet.freeze_panes = "C2"
    sheet.auto_filter.ref = sheet.dimensions
    for column in sheet.columns:
        sheet.column_dimensions[column[0].column_letter].width = 24
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        workbook.save(stream)
