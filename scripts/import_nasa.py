# backend/scripts/import_nasa.py
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Dict
from sqlalchemy import select

from app.db.session import db_manager
from app.models.dev2_models import NasaResearchObservation, NasaResearchStudy


def import_osdr_csv(
    csv_path: str,
    osdr_accession: str,
    title: str,
    domain: str,
    source_url: str = "https://osdr.nasa.gov/",
) -> Dict[str, Any]:
    """
    Imports real NASA OSDR research records strictly into `nasa_research_studies` and
    `nasa_research_observations` with SHA-256 provenance. Never writes to crew telemetry tables.
    """
    path = Path(csv_path)
    raw_bytes = path.read_bytes()
    provenance_hash = hashlib.sha256(raw_bytes).hexdigest()

    db_manager.init_local_schema()
    inserted_obs = 0

    with db_manager.session_scope() as db:
        study = db.scalars(
            select(NasaResearchStudy).where(NasaResearchStudy.osdr_accession == osdr_accession)
        ).first()
        if not study:
            study = NasaResearchStudy(
                id=f"STUDY-{osdr_accession}",
                osdr_accession=osdr_accession,
                title=title,
                domain=domain,
                source_url=source_url,
                provenance_hash=provenance_hash,
                evidence_classification="NASA_OSDR_RESEARCH_ONLY",
            )
            db.add(study)
            db.flush()

        reader = csv.DictReader(raw_bytes.decode("utf-8").splitlines())
        for row in reader:
            db.add(
                NasaResearchObservation(
                    study_id=study.id,
                    metric_code=row["metric_code"].strip(),
                    summary_value=float(row["summary_value"]),
                    unit=row["unit"].strip(),
                    cohort_label=row.get("cohort_label", "OSDR_COHORT").strip(),
                    notes=row.get("notes", "").strip(),
                    evidence_classification="NASA_OSDR_RESEARCH_ONLY",
                )
            )
            inserted_obs += 1

    return {
        "osdr_accession": osdr_accession,
        "study_id": f"STUDY-{osdr_accession}",
        "provenance_hash": provenance_hash,
        "observations_imported": inserted_obs,
        "evidence_classification": "NASA_OSDR_RESEARCH_ONLY",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Segregated NASA OSDR Research Evidence Importer")
    parser.add_argument("--csv", required=True, help="Path to normalized OSDR CSV file")
    parser.add_argument("--accession", required=True, help="e.g. OSD-258")
    parser.add_argument("--title", required=True)
    parser.add_argument("--domain", required=True)
    args = parser.parse_args()
    print(json.dumps(import_osdr_csv(args.csv, args.accession, args.title, args.domain), indent=2))