"""Main synchronization script for FileMaker to RevolutionEHR data transfer."""

import csv
import logging
import os
import re
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List

from .api.revehr_client import RevolutionEHRClient
from .api.exceptions import RevEHRAPIError
from .filemaker.extractor import FileMakerExtractor, ExtractionMethod
from .transformers.patient import PatientTransformer
from .transformers.contact_lens_rx import ContactLensRxTransformer
from .transformers.glasses_rx import GlassesRxTransformer
from .transformers.transaction import (
    row_to_transaction,
    transaction_to_revehr_cl_rx,
    filter_cl_transactions,
)
from .mapping.patient_id_map import PatientIdMapper

logger = logging.getLogger(__name__)


class FileMakerRevEHRSync:
    """Main synchronization class for FileMaker to RevolutionEHR."""

    def __init__(self, config_path: str = "config/settings.yaml", dry_run: Optional[bool] = None):
        """Initialize sync with configuration.

        Args:
            config_path: Path to YAML configuration file
            dry_run: Override dry_run setting (None = use config value)
        """
        self.config = self._load_config(config_path)
        self._setup_logging()

        # Sync settings (load early for dry_run check)
        sync_config = self.config.get("sync", {})
        self.batch_size = sync_config.get("batch_size", 50)
        self.continue_on_error = sync_config.get("continue_on_error", True)

        # Dry run mode - command line overrides config
        if dry_run is not None:
            self.dry_run = dry_run
        else:
            self.dry_run = sync_config.get("dry_run", False)

        if self.dry_run:
            logger.info("=" * 50)
            logger.info("DRY RUN MODE - No data will be uploaded to RevEHR")
            logger.info("=" * 50)

        # Initialize patient ID mapper
        data_dir = self.config.get("sync", {}).get("data_dir", "data")
        self.patient_mapper = PatientIdMapper(
            mapping_file=f"{data_dir}/patient_id_map.json"
        )

        # Initialize API client
        revehr_config = self.config.get("revolutionehr", {})
        self.client = RevolutionEHRClient(
            base_url=revehr_config.get("base_url", ""),
            api_key=revehr_config.get("api_key"),
            client_id=revehr_config.get("client_id"),
            client_secret=revehr_config.get("client_secret"),
            timeout=revehr_config.get("timeout", 30),
        )

        # Initialize extractor
        fm_config = self.config.get("filemaker", {})
        method = ExtractionMethod(fm_config.get("method", "file"))

        odbc_config = fm_config.get("odbc", {})
        export_config = fm_config.get("exports", {})

        self.extractor = FileMakerExtractor(
            method=method,
            odbc_dsn=odbc_config.get("dsn"),
            odbc_host=odbc_config.get("host"),
            odbc_database=odbc_config.get("database"),
            odbc_username=odbc_config.get("username"),
            odbc_password=odbc_config.get("password"),
            export_directory=export_config.get("directory"),
            file_encoding=export_config.get("encoding", "utf-8"),
        )

        # Initialize transformers
        mappings = self.config.get("field_mappings", {})
        self.patient_transformer = PatientTransformer(
            field_map=mappings.get("patient")
        )
        self.cl_rx_transformer = ContactLensRxTransformer(
            field_map=mappings.get("contact_lens_rx")
        )
        self.glasses_rx_transformer = GlassesRxTransformer(
            field_map=mappings.get("glasses_rx")
        )

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file with environment variable expansion."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r") as f:
            content = f.read()

        # Expand environment variables (${VAR} or $VAR syntax)
        content = self._expand_env_vars(content)

        return yaml.safe_load(content)

    def _expand_env_vars(self, content: str) -> str:
        """Expand environment variables in config content.

        Supports both ${VAR} and $VAR syntax.

        Args:
            content: Raw config file content

        Returns:
            Content with env vars expanded
        """
        # Pattern for ${VAR} or ${VAR:-default}
        pattern = r'\$\{([^}:]+)(?::-([^}]*))?\}'

        def replacer(match):
            var_name = match.group(1)
            default = match.group(2) or ""
            return os.environ.get(var_name, default)

        expanded = re.sub(pattern, replacer, content)

        # Also handle $VAR (without braces) but be careful with YAML
        # Only expand if followed by whitespace, quote, or end of line
        pattern2 = r'\$([A-Z_][A-Z0-9_]*)(?=[\s"\'\n]|$)'

        def replacer2(match):
            var_name = match.group(1)
            return os.environ.get(var_name, f"${var_name}")

        return re.sub(pattern2, replacer2, expanded)

    def _setup_logging(self):
        """Configure logging based on settings."""
        log_config = self.config.get("logging", {})
        level = getattr(logging, log_config.get("level", "INFO"))
        log_format = log_config.get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        logging.basicConfig(level=level, format=log_format)

        # File handler if specified
        if log_file := log_config.get("file"):
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(log_path)
            handler.setFormatter(logging.Formatter(log_format))
            logging.getLogger().addHandler(handler)

    def sync_patients(
        self,
        file_path: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Synchronize patient data from FileMaker to RevolutionEHR.

        Args:
            file_path: Path to export file (for file-based extraction)
            limit: Maximum patients to sync

        Returns:
            Summary of sync results
        """
        logger.info("Starting patient sync")

        # Get file path from config if not provided
        if not file_path:
            exports = self.config.get("filemaker", {}).get("exports", {})
            export_dir = exports.get("directory", "./exports")
            patients_file = exports.get("patients_file", "patients.csv")
            file_path = str(Path(export_dir) / patients_file)

        results = {
            "total": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "error_details": [],
            "dry_run": self.dry_run,
        }

        # Extract patients
        patients_raw = self.extractor.get_patients(file_path=file_path, limit=limit)
        results["total"] = len(patients_raw)
        logger.info(f"Extracted {len(patients_raw)} patients from FileMaker")

        for raw_patient in patients_raw:
            try:
                # Transform to model
                patient = self.patient_transformer.from_filemaker(raw_patient)
                filemaker_id = patient.filemaker_id

                # Convert to RevEHR format
                revehr_data = self.patient_transformer.to_revehr(patient)

                # Check if we already have a mapping
                existing_revehr_id = self.patient_mapper.get_revehr_id(filemaker_id)

                if existing_revehr_id:
                    # Update existing patient
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would update patient: {patient.full_name} (RevEHR: {existing_revehr_id})")
                        results["updated"] += 1
                    else:
                        self.client.update_patient(existing_revehr_id, revehr_data)
                        results["updated"] += 1
                        logger.debug(f"Updated patient: {patient.full_name}")
                else:
                    # Search for patient in RevEHR by name/DOB
                    if not self.dry_run:
                        try:
                            dob_str = patient.demographics.date_of_birth.isoformat() if patient.demographics.date_of_birth else None
                            existing = self.client.search_patients(
                                first_name=patient.demographics.first_name,
                                last_name=patient.demographics.last_name,
                                dob=dob_str,
                            )

                            if existing:
                                # Found existing - save mapping and update
                                revehr_id = existing[0].get("id")
                                self.patient_mapper.add_mapping(
                                    filemaker_id=filemaker_id,
                                    revehr_id=revehr_id,
                                    first_name=patient.demographics.first_name,
                                    last_name=patient.demographics.last_name,
                                    dob=dob_str,
                                )
                                self.client.update_patient(revehr_id, revehr_data)
                                results["updated"] += 1
                                logger.debug(f"Found and updated patient: {patient.full_name}")
                            else:
                                # Create new patient
                                response = self.client.create_patient(revehr_data)
                                revehr_id = response.get("id")
                                if revehr_id:
                                    self.patient_mapper.add_mapping(
                                        filemaker_id=filemaker_id,
                                        revehr_id=revehr_id,
                                        first_name=patient.demographics.first_name,
                                        last_name=patient.demographics.last_name,
                                        dob=dob_str,
                                    )
                                results["created"] += 1
                                logger.debug(f"Created patient: {patient.full_name}")
                        except RevEHRAPIError as e:
                            raise e
                    else:
                        logger.info(f"[DRY RUN] Would create patient: {patient.full_name} (FM: {filemaker_id})")
                        results["created"] += 1

            except Exception as e:
                results["errors"] += 1
                error_info = {
                    "patient": raw_patient.get("PatientID", "Unknown"),
                    "error": str(e),
                }
                results["error_details"].append(error_info)
                logger.error(f"Error syncing patient: {e}")

                if not self.continue_on_error:
                    raise

        logger.info(
            f"Patient sync complete: {results['created']} created, "
            f"{results['updated']} updated, {results['errors']} errors"
        )
        return results

    def sync_contact_lens_rx(
        self,
        file_path: Optional[str] = None,
        patient_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronize contact lens prescriptions.

        Args:
            file_path: Path to export file
            patient_id: Sync only for specific patient

        Returns:
            Summary of sync results
        """
        logger.info("Starting contact lens Rx sync")

        if not file_path:
            exports = self.config.get("filemaker", {}).get("exports", {})
            export_dir = exports.get("directory", "./exports")
            cl_file = exports.get("contact_lens_rx_file", "contact_lens_rx.csv")
            file_path = str(Path(export_dir) / cl_file)

        results = {
            "total": 0,
            "synced": 0,
            "errors": 0,
            "error_details": [],
        }

        # Extract prescriptions
        rx_records = self.extractor.get_contact_lens_rx(
            file_path=file_path, patient_id=patient_id
        )
        results["total"] = len(rx_records)
        logger.info(f"Extracted {len(rx_records)} CL Rx records")

        for raw_rx in rx_records:
            try:
                rx = self.cl_rx_transformer.from_filemaker(raw_rx)
                revehr_data = self.cl_rx_transformer.to_revehr(rx)

                # Need to resolve patient RevEHR ID
                # This assumes patient_revehr_id is set or can be looked up
                if rx.patient_revehr_id:
                    self.client.create_contact_lens_rx(rx.patient_revehr_id, revehr_data)
                    results["synced"] += 1
                else:
                    results["errors"] += 1
                    results["error_details"].append({
                        "rx_id": rx.filemaker_id,
                        "error": "Patient RevEHR ID not found",
                    })

            except Exception as e:
                results["errors"] += 1
                results["error_details"].append({
                    "rx_id": raw_rx.get("RxID", "Unknown"),
                    "error": str(e),
                })
                logger.error(f"Error syncing CL Rx: {e}")

                if not self.continue_on_error:
                    raise

        logger.info(
            f"CL Rx sync complete: {results['synced']} synced, "
            f"{results['errors']} errors"
        )
        return results

    def sync_glasses_rx(
        self,
        file_path: Optional[str] = None,
        patient_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronize glasses prescriptions.

        Args:
            file_path: Path to export file
            patient_id: Sync only for specific patient

        Returns:
            Summary of sync results
        """
        logger.info("Starting glasses Rx sync")

        if not file_path:
            exports = self.config.get("filemaker", {}).get("exports", {})
            export_dir = exports.get("directory", "./exports")
            glasses_file = exports.get("glasses_rx_file", "glasses_rx.csv")
            file_path = str(Path(export_dir) / glasses_file)

        results = {
            "total": 0,
            "synced": 0,
            "errors": 0,
            "error_details": [],
        }

        rx_records = self.extractor.get_glasses_rx(
            file_path=file_path, patient_id=patient_id
        )
        results["total"] = len(rx_records)
        logger.info(f"Extracted {len(rx_records)} glasses Rx records")

        for raw_rx in rx_records:
            try:
                rx = self.glasses_rx_transformer.from_filemaker(raw_rx)
                revehr_data = self.glasses_rx_transformer.to_revehr(rx)

                if rx.patient_revehr_id:
                    self.client.create_glasses_rx(rx.patient_revehr_id, revehr_data)
                    results["synced"] += 1
                else:
                    results["errors"] += 1
                    results["error_details"].append({
                        "rx_id": rx.filemaker_id,
                        "error": "Patient RevEHR ID not found",
                    })

            except Exception as e:
                results["errors"] += 1
                results["error_details"].append({
                    "rx_id": raw_rx.get("RxID", "Unknown"),
                    "error": str(e),
                })
                logger.error(f"Error syncing glasses Rx: {e}")

                if not self.continue_on_error:
                    raise

        logger.info(
            f"Glasses Rx sync complete: {results['synced']} synced, "
            f"{results['errors']} errors"
        )
        return results

    def sync_transactions(
        self,
        file_path: Optional[str] = None,
        patient_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronize contact lens Rx from Transactions export.

        This method reads the transactions_clean.csv file (41 columns)
        which contains embedded CL Rx data, transforms it, and uploads
        to RevolutionEHR.

        Args:
            file_path: Path to transactions CSV file
            patient_id: Filter to specific FileMaker patient ID

        Returns:
            Summary of sync results
        """
        logger.info("Starting transaction/CL Rx sync")

        # Get file path from config if not provided
        if not file_path:
            exports = self.config.get("filemaker", {}).get("exports", {})
            export_dir = exports.get("directory", "./exports")
            transactions_file = exports.get("transactions_file", "transactions_clean.csv")
            file_path = str(Path(export_dir) / transactions_file)

        results = {
            "total": 0,
            "with_cl_rx": 0,
            "synced": 0,
            "skipped_no_mapping": 0,
            "skipped_no_rx": 0,
            "errors": 0,
            "error_details": [],
            "dry_run": self.dry_run,
        }

        # Check file exists
        if not Path(file_path).exists():
            logger.warning(f"Transactions file not found: {file_path}")
            results["error_details"].append({
                "error": f"File not found: {file_path}"
            })
            return results

        # Read CSV with headers
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                transactions = list(reader)
        except Exception as e:
            logger.error(f"Error reading transactions file: {e}")
            results["error_details"].append({"error": str(e)})
            return results

        results["total"] = len(transactions)
        logger.info(f"Read {len(transactions)} transactions from {file_path}")

        # Process each transaction
        for row in transactions:
            try:
                # Filter by patient if specified
                fm_patient_id = row.get("Patient_ID", "")
                if patient_id and fm_patient_id != patient_id:
                    continue

                # Parse transaction
                transaction = row_to_transaction(row)

                # Skip if no CL Rx data (empty lens brand)
                if not transaction.cl_od.brand and not transaction.cl_os.brand:
                    results["skipped_no_rx"] += 1
                    continue

                results["with_cl_rx"] += 1

                # Look up RevEHR patient ID
                revehr_patient_id = self.patient_mapper.get_revehr_id(fm_patient_id)

                if not revehr_patient_id:
                    results["skipped_no_mapping"] += 1
                    results["error_details"].append({
                        "transaction": transaction.transaction_num,
                        "patient_id": fm_patient_id,
                        "error": "No RevEHR patient mapping found",
                    })
                    logger.warning(
                        f"No mapping for patient {fm_patient_id}, "
                        f"skipping transaction {transaction.transaction_num}"
                    )
                    continue

                # Transform to RevEHR CL Rx format
                revehr_data = transaction_to_revehr_cl_rx(transaction)

                if self.dry_run:
                    logger.info(
                        f"[DRY RUN] Would create CL Rx for patient {revehr_patient_id}: "
                        f"OD={transaction.cl_od.brand} OS={transaction.cl_os.brand}"
                    )
                    results["synced"] += 1
                else:
                    # Upload to RevEHR
                    self.client.create_contact_lens_rx(revehr_patient_id, revehr_data)
                    results["synced"] += 1
                    logger.debug(
                        f"Created CL Rx for patient {revehr_patient_id}: "
                        f"transaction {transaction.transaction_num}"
                    )

            except Exception as e:
                results["errors"] += 1
                results["error_details"].append({
                    "transaction": row.get("Transaction_Num", "Unknown"),
                    "error": str(e),
                })
                logger.error(f"Error syncing transaction: {e}")

                if not self.continue_on_error:
                    raise

        logger.info(
            f"Transaction sync complete: {results['total']} total, "
            f"{results['with_cl_rx']} with CL Rx, {results['synced']} synced, "
            f"{results['skipped_no_mapping']} skipped (no mapping), "
            f"{results['errors']} errors"
        )
        return results

    def run_full_sync(self) -> Dict[str, Any]:
        """Run full synchronization of all data types.

        Returns:
            Combined results for all sync operations
        """
        logger.info("Starting full sync")
        if self.dry_run:
            logger.info("Running in DRY RUN mode - no data will be uploaded")

        results = {
            "patients": self.sync_patients(),
            "transactions": self.sync_transactions(),  # CL Rx from transactions
            # "glasses_rx": self.sync_glasses_rx(),  # TODO: Enable when export ready
        }

        logger.info("Full sync complete")
        return results


def main():
    """Main entry point for sync script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Sync FileMaker data to RevolutionEHR"
    )
    parser.add_argument(
        "-c", "--config",
        default="config/settings.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode - log actions without uploading to RevEHR",
    )
    parser.add_argument(
        "--patients-only",
        action="store_true",
        help="Sync only patients",
    )
    parser.add_argument(
        "--transactions-only",
        action="store_true",
        help="Sync only transactions (CL Rx)",
    )
    parser.add_argument(
        "--glasses-rx-only",
        action="store_true",
        help="Sync only glasses Rx",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )

    args = parser.parse_args()

    # Set up verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize sync with dry_run override if specified
    sync = FileMakerRevEHRSync(
        config_path=args.config,
        dry_run=args.dry_run if args.dry_run else None
    )

    # Run appropriate sync
    if args.patients_only:
        results = {"patients": sync.sync_patients()}
    elif args.transactions_only:
        results = {"transactions": sync.sync_transactions()}
    elif args.glasses_rx_only:
        results = {"glasses_rx": sync.sync_glasses_rx()}
    else:
        results = sync.run_full_sync()

    # Print results
    print("\n" + "=" * 50)
    print("SYNC RESULTS")
    if sync.dry_run:
        print("(DRY RUN - no data uploaded)")
    print("=" * 50)

    for category, data in results.items():
        print(f"\n{category.upper()}:")
        for key, value in data.items():
            if key != "error_details":
                print(f"  {key}: {value}")

        # Show first few errors if any
        if data.get("error_details"):
            print(f"  --- First 3 errors ---")
            for err in data["error_details"][:3]:
                print(f"    {err}")
            if len(data["error_details"]) > 3:
                print(f"    ... and {len(data['error_details']) - 3} more")


if __name__ == "__main__":
    main()
