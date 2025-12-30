"""File reader for FileMaker CSV/Tab exports.

FileMaker Pro 9 can export records as CSV or Tab-delimited files
which can be read and processed.
"""

import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class FileReader:
    """Reader for FileMaker file exports (CSV, Tab-delimited).

    Provides methods to read exported files and convert to
    dictionaries for processing.
    """

    def __init__(self, encoding: str = "utf-8"):
        """Initialize file reader.

        Args:
            encoding: File encoding (default utf-8, FileMaker may use others)
        """
        self.encoding = encoding

    def read_csv(
        self,
        file_path: str,
        delimiter: str = ",",
        has_header: bool = True,
        field_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Read a CSV file exported from FileMaker.

        Args:
            file_path: Path to CSV file
            delimiter: Field delimiter (comma, tab, etc.)
            has_header: Whether first row contains headers
            field_names: Custom field names (if no header)

        Returns:
            List of record dictionaries
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Reading file: {file_path}")
        records = []

        with open(path, "r", encoding=self.encoding, newline="") as f:
            if has_header:
                reader = csv.DictReader(f, delimiter=delimiter)
            else:
                reader = csv.DictReader(
                    f, fieldnames=field_names, delimiter=delimiter
                )

            for row in reader:
                # Clean up values
                clean_row = {}
                for key, value in row.items():
                    if key is not None:  # Skip None keys from malformed rows
                        clean_row[key.strip()] = self._clean_value(value)
                records.append(clean_row)

        logger.info(f"Read {len(records)} records from {file_path}")
        return records

    def read_tab_delimited(
        self,
        file_path: str,
        has_header: bool = True,
        field_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Read a tab-delimited file exported from FileMaker.

        Args:
            file_path: Path to file
            has_header: Whether first row contains headers
            field_names: Custom field names (if no header)

        Returns:
            List of record dictionaries
        """
        return self.read_csv(
            file_path,
            delimiter="\t",
            has_header=has_header,
            field_names=field_names,
        )

    def read_with_pandas(
        self,
        file_path: str,
        delimiter: str = ",",
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Read file using pandas (if available).

        Pandas provides more robust handling of edge cases.

        Args:
            file_path: Path to file
            delimiter: Field delimiter
            **kwargs: Additional pandas read_csv arguments

        Returns:
            List of record dictionaries
        """
        if not PANDAS_AVAILABLE:
            logger.warning("pandas not available, falling back to csv module")
            return self.read_csv(file_path, delimiter=delimiter)

        logger.info(f"Reading file with pandas: {file_path}")

        df = pd.read_csv(
            file_path,
            delimiter=delimiter,
            encoding=self.encoding,
            **kwargs,
        )

        # Convert NaN to None
        df = df.where(pd.notnull(df), None)

        records = df.to_dict("records")
        logger.info(f"Read {len(records)} records from {file_path}")

        return records

    def _clean_value(self, value: Any) -> Any:
        """Clean and normalize a field value.

        Args:
            value: Raw value from file

        Returns:
            Cleaned value
        """
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()
            if value == "" or value.lower() == "null":
                return None

        return value

    def detect_delimiter(self, file_path: str, sample_lines: int = 5) -> str:
        """Attempt to detect the file delimiter.

        Args:
            file_path: Path to file
            sample_lines: Number of lines to sample

        Returns:
            Detected delimiter character
        """
        path = Path(file_path)

        with open(path, "r", encoding=self.encoding) as f:
            sample = "".join([f.readline() for _ in range(sample_lines)])

        # Count potential delimiters
        delimiters = {
            ",": sample.count(","),
            "\t": sample.count("\t"),
            ";": sample.count(";"),
            "|": sample.count("|"),
        }

        # Return most common
        detected = max(delimiters, key=delimiters.get)
        logger.info(f"Detected delimiter: {repr(detected)}")

        return detected

    def get_headers(self, file_path: str, delimiter: str = None) -> List[str]:
        """Get column headers from first row.

        Args:
            file_path: Path to file
            delimiter: Field delimiter (auto-detect if None)

        Returns:
            List of header names
        """
        if delimiter is None:
            delimiter = self.detect_delimiter(file_path)

        with open(file_path, "r", encoding=self.encoding) as f:
            reader = csv.reader(f, delimiter=delimiter)
            headers = next(reader)

        return [h.strip() for h in headers]

    def read_csv_positional(
        self,
        file_path: str,
        delimiter: str = ",",
        field_mapping: Optional[Dict[int, str]] = None,
        skip_empty_rows: bool = True,
    ) -> List[Dict[str, Any]]:
        """Read CSV without headers, mapping columns by position.

        Designed for FileMaker exports that don't include header rows.
        Field mapping uses column index (0-based) to field name.

        Args:
            file_path: Path to CSV file
            delimiter: Field delimiter (comma, tab, etc.)
            field_mapping: Dict mapping column index to field name
                          e.g., {0: "age", 5: "date_of_birth", 21: "first_name"}
            skip_empty_rows: Skip rows where all mapped fields are empty

        Returns:
            List of record dictionaries with mapped field names
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if field_mapping is None:
            field_mapping = {}

        logger.info(f"Reading file (positional): {file_path}")
        records = []
        skipped_empty = 0

        with open(path, "r", encoding=self.encoding, newline="") as f:
            reader = csv.reader(f, delimiter=delimiter)

            for row_num, row in enumerate(reader, start=1):
                # Map columns by position
                record = {}
                has_data = False

                for col_index, field_name in field_mapping.items():
                    if col_index < len(row):
                        value = self._clean_value(row[col_index])
                        record[field_name] = value
                        if value is not None and value != "":
                            has_data = True
                    else:
                        record[field_name] = None

                # Skip empty rows if configured
                if skip_empty_rows and not has_data:
                    skipped_empty += 1
                    continue

                # Add row number for debugging
                record["_row_number"] = row_num
                records.append(record)

        logger.info(
            f"Read {len(records)} records from {file_path} "
            f"(skipped {skipped_empty} empty rows)"
        )
        return records

    def count_columns(self, file_path: str, delimiter: str = ",") -> int:
        """Count the number of columns in a file.

        Args:
            file_path: Path to file
            delimiter: Field delimiter

        Returns:
            Number of columns in first non-empty row
        """
        with open(file_path, "r", encoding=self.encoding) as f:
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                if row:  # First non-empty row
                    return len(row)
        return 0
