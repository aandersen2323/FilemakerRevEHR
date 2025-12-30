"""Main FileMaker data extractor.

Provides a unified interface for extracting data from FileMaker Pro 9
using various methods (ODBC, XML, file exports).
"""

import logging
from typing import List, Dict, Any, Optional
from enum import Enum

from .odbc_connector import ODBCConnector
from .xml_parser import XMLParser
from .file_reader import FileReader

logger = logging.getLogger(__name__)


class ExtractionMethod(str, Enum):
    """Data extraction methods."""
    ODBC = "odbc"
    XML = "xml"
    FILE = "file"


class FileMakerExtractor:
    """Unified FileMaker data extractor.

    Provides a consistent interface for extracting data regardless
    of the underlying method (ODBC, XML export, or file export).
    """

    def __init__(
        self,
        method: ExtractionMethod = ExtractionMethod.FILE,
        # ODBC settings
        odbc_dsn: Optional[str] = None,
        odbc_host: Optional[str] = None,
        odbc_database: Optional[str] = None,
        odbc_username: Optional[str] = None,
        odbc_password: Optional[str] = None,
        # File/XML settings
        export_directory: Optional[str] = None,
        file_encoding: str = "utf-8",
        # Headerless CSV support (for FileMaker Pro exports without headers)
        no_header: bool = False,
    ):
        """Initialize extractor with configuration.

        Args:
            method: Extraction method to use
            odbc_dsn: ODBC Data Source Name
            odbc_host: FileMaker host
            odbc_database: Database name
            odbc_username: Database username
            odbc_password: Database password
            export_directory: Directory for export files
            file_encoding: Text encoding for files
            no_header: True if CSV files don't have header row
        """
        self.method = method
        self.export_directory = export_directory
        self.no_header = no_header

        # Initialize appropriate connector
        if method == ExtractionMethod.ODBC:
            self._odbc = ODBCConnector(
                dsn=odbc_dsn,
                host=odbc_host,
                database=odbc_database,
                username=odbc_username,
                password=odbc_password,
            )
        else:
            self._odbc = None

        self._xml_parser = XMLParser()
        self._file_reader = FileReader(encoding=file_encoding)

        # Field mapping configuration
        # For headerless CSVs: {entity: {column_index: field_name}}
        # For header CSVs: {entity: {fm_field_name: std_field_name}}
        self._field_mappings: Dict[str, Dict] = {}

    def set_field_mapping(self, entity_type: str, mapping: Dict[str, str]) -> None:
        """Set field name mapping for an entity type.

        Maps FileMaker field names to standard field names.

        Args:
            entity_type: Entity type (patient, contact_lens_rx, glasses_rx)
            mapping: Dict mapping FileMaker names to standard names
        """
        self._field_mappings[entity_type] = mapping

    def _apply_mapping(
        self, records: List[Dict[str, Any]], entity_type: str
    ) -> List[Dict[str, Any]]:
        """Apply field mapping to records.

        Args:
            records: List of raw records
            entity_type: Entity type for mapping lookup

        Returns:
            Records with mapped field names
        """
        mapping = self._field_mappings.get(entity_type)
        if not mapping:
            return records

        mapped_records = []
        for record in records:
            mapped = {}
            for fm_field, std_field in mapping.items():
                if fm_field in record:
                    mapped[std_field] = record[fm_field]
            # Include unmapped fields as-is
            for key, value in record.items():
                if key not in mapping:
                    mapped[key] = value
            mapped_records.append(mapped)

        return mapped_records

    # =========================================================================
    # Patient Extraction
    # =========================================================================

    def get_patients(
        self,
        file_path: Optional[str] = None,
        table_name: str = "Patients",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Extract patient records from FileMaker.

        Args:
            file_path: Path to export file (for XML/FILE methods)
            table_name: Table name (for ODBC method)
            limit: Maximum records to retrieve

        Returns:
            List of patient dictionaries
        """
        logger.info(f"Extracting patients using {self.method} method")

        if self.method == ExtractionMethod.ODBC:
            records = self._odbc.get_patients(table_name=table_name, limit=limit)

        elif self.method == ExtractionMethod.XML:
            if not file_path:
                raise ValueError("file_path required for XML extraction")
            records = self._xml_parser.parse_file(file_path)

        else:  # FILE method
            if not file_path:
                raise ValueError("file_path required for file extraction")

            # Use positional reading for headerless CSVs
            if self.no_header and "patient" in self._field_mappings:
                records = self._file_reader.read_csv_positional(
                    file_path,
                    field_mapping=self._field_mappings["patient"],
                    skip_empty_rows=True,
                )
                # Mapping already applied in positional read
                return records
            else:
                records = self._file_reader.read_csv(file_path)

        return self._apply_mapping(records, "patient")

    def get_patient_by_id(
        self,
        patient_id: str,
        file_path: Optional[str] = None,
        table_name: str = "Patients",
        id_field: str = "PatientID",
    ) -> Optional[Dict[str, Any]]:
        """Get a single patient by ID.

        Args:
            patient_id: Patient ID to find
            file_path: Path to export file
            table_name: Table name (ODBC)
            id_field: ID field name

        Returns:
            Patient dictionary or None
        """
        if self.method == ExtractionMethod.ODBC:
            record = self._odbc.get_patient_by_id(
                patient_id, table_name=table_name, id_field=id_field
            )
            if record:
                mapped = self._apply_mapping([record], "patient")
                return mapped[0]
            return None

        # For file-based methods, load all and filter
        all_patients = self.get_patients(file_path=file_path, table_name=table_name)
        for patient in all_patients:
            if str(patient.get(id_field)) == str(patient_id):
                return patient

        return None

    # =========================================================================
    # Contact Lens Rx Extraction
    # =========================================================================

    def get_contact_lens_rx(
        self,
        file_path: Optional[str] = None,
        table_name: str = "ContactLensRx",
        patient_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Extract contact lens prescriptions.

        Args:
            file_path: Path to export file
            table_name: Table name (ODBC)
            patient_id: Filter by patient ID

        Returns:
            List of CL Rx dictionaries
        """
        logger.info(f"Extracting contact lens Rx using {self.method} method")

        if self.method == ExtractionMethod.ODBC:
            records = self._odbc.get_contact_lens_rx(
                table_name=table_name, patient_id=patient_id
            )

        elif self.method == ExtractionMethod.XML:
            if not file_path:
                raise ValueError("file_path required for XML extraction")
            records = self._xml_parser.parse_file(file_path)
            if patient_id:
                records = [r for r in records if str(r.get("PatientID")) == str(patient_id)]

        else:  # FILE method
            if not file_path:
                raise ValueError("file_path required for file extraction")
            records = self._file_reader.read_csv(file_path)
            if patient_id:
                records = [r for r in records if str(r.get("PatientID")) == str(patient_id)]

        return self._apply_mapping(records, "contact_lens_rx")

    # =========================================================================
    # Glasses Rx Extraction
    # =========================================================================

    def get_glasses_rx(
        self,
        file_path: Optional[str] = None,
        table_name: str = "GlassesRx",
        patient_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Extract glasses prescriptions.

        Args:
            file_path: Path to export file
            table_name: Table name (ODBC)
            patient_id: Filter by patient ID

        Returns:
            List of glasses Rx dictionaries
        """
        logger.info(f"Extracting glasses Rx using {self.method} method")

        if self.method == ExtractionMethod.ODBC:
            records = self._odbc.get_glasses_rx(
                table_name=table_name, patient_id=patient_id
            )

        elif self.method == ExtractionMethod.XML:
            if not file_path:
                raise ValueError("file_path required for XML extraction")
            records = self._xml_parser.parse_file(file_path)
            if patient_id:
                records = [r for r in records if str(r.get("PatientID")) == str(patient_id)]

        else:  # FILE method
            if not file_path:
                raise ValueError("file_path required for file extraction")
            records = self._file_reader.read_csv(file_path)
            if patient_id:
                records = [r for r in records if str(r.get("PatientID")) == str(patient_id)]

        return self._apply_mapping(records, "glasses_rx")

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def test_connection(self) -> bool:
        """Test the extraction method connection/configuration.

        Returns:
            True if connection successful
        """
        if self.method == ExtractionMethod.ODBC:
            try:
                self._odbc.connect()
                self._odbc.disconnect()
                return True
            except Exception as e:
                logger.error(f"ODBC connection test failed: {e}")
                return False

        # For file-based methods, just verify parser/reader exist
        return True

    def get_available_tables(self) -> List[str]:
        """Get list of available tables (ODBC only).

        Returns:
            List of table names
        """
        if self.method != ExtractionMethod.ODBC:
            raise NotImplementedError("Table listing only available with ODBC")

        return self._odbc.get_table_names()

    def close(self) -> None:
        """Clean up resources."""
        if self._odbc:
            self._odbc.disconnect()
