"""XML parser for FileMaker Pro 9 exports.

FileMaker can export data in FMPXMLRESULT format which can be
parsed to extract records.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from lxml import etree

    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    import xml.etree.ElementTree as etree

    logger.warning("lxml not installed - using standard library xml parser")


class XMLParser:
    """Parser for FileMaker XML exports.

    Supports FMPXMLRESULT format exported from FileMaker Pro 9.
    """

    # FileMaker XML namespaces
    FM_NAMESPACE = "http://www.filemaker.com/fmpxmlresult"
    NAMESPACES = {"fm": FM_NAMESPACE}

    def __init__(self):
        """Initialize XML parser."""
        pass

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse a FileMaker XML export file.

        Args:
            file_path: Path to XML file

        Returns:
            List of record dictionaries
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"XML file not found: {file_path}")

        logger.info(f"Parsing FileMaker XML: {file_path}")

        tree = etree.parse(str(path))
        root = tree.getroot()

        return self._parse_fmpxmlresult(root)

    def parse_string(self, xml_string: str) -> List[Dict[str, Any]]:
        """Parse FileMaker XML from string.

        Args:
            xml_string: XML content as string

        Returns:
            List of record dictionaries
        """
        if LXML_AVAILABLE:
            root = etree.fromstring(xml_string.encode())
        else:
            root = etree.fromstring(xml_string)

        return self._parse_fmpxmlresult(root)

    def _parse_fmpxmlresult(self, root) -> List[Dict[str, Any]]:
        """Parse FMPXMLRESULT format.

        Args:
            root: XML root element

        Returns:
            List of record dictionaries
        """
        records = []

        # Handle namespace
        ns = self.NAMESPACES if root.tag.startswith("{") else {}
        ns_prefix = "{" + self.FM_NAMESPACE + "}" if root.tag.startswith("{") else ""

        # Get field definitions
        metadata = root.find(f".//{ns_prefix}METADATA", ns) or root.find(".//METADATA")
        if metadata is None:
            logger.warning("No METADATA element found in XML")
            return records

        fields = []
        for field in metadata.findall(f"{ns_prefix}FIELD", ns) or metadata.findall("FIELD"):
            field_name = field.get("NAME")
            field_type = field.get("TYPE", "TEXT")
            fields.append({"name": field_name, "type": field_type})

        # Get result data
        resultset = root.find(f".//{ns_prefix}RESULTSET", ns) or root.find(".//RESULTSET")
        if resultset is None:
            logger.warning("No RESULTSET element found in XML")
            return records

        # Parse each row
        for row in resultset.findall(f"{ns_prefix}ROW", ns) or resultset.findall("ROW"):
            record = {}
            cols = row.findall(f"{ns_prefix}COL", ns) or row.findall("COL")

            for i, col in enumerate(cols):
                if i < len(fields):
                    field_name = fields[i]["name"]
                    field_type = fields[i]["type"]

                    # Get DATA element(s)
                    data_elements = col.findall(f"{ns_prefix}DATA", ns) or col.findall("DATA")

                    if not data_elements:
                        record[field_name] = None
                    elif len(data_elements) == 1:
                        record[field_name] = self._convert_value(
                            data_elements[0].text, field_type
                        )
                    else:
                        # Multiple values (repeating field)
                        record[field_name] = [
                            self._convert_value(d.text, field_type) for d in data_elements
                        ]

            records.append(record)

        logger.info(f"Parsed {len(records)} records from XML")
        return records

    def _convert_value(self, value: Optional[str], field_type: str) -> Any:
        """Convert XML text value based on field type.

        Args:
            value: Text value from XML
            field_type: FileMaker field type

        Returns:
            Converted Python value
        """
        if value is None or value == "":
            return None

        field_type = field_type.upper()

        if field_type == "NUMBER":
            try:
                if "." in value:
                    return float(value)
                return int(value)
            except ValueError:
                return value

        if field_type == "DATE":
            # FileMaker dates are typically MM/DD/YYYY
            return value  # Keep as string, transform later

        if field_type == "TIME":
            return value

        if field_type == "TIMESTAMP":
            return value

        return value

    def get_field_names(self, file_path: str) -> List[str]:
        """Get field names from FileMaker XML file.

        Args:
            file_path: Path to XML file

        Returns:
            List of field names
        """
        path = Path(file_path)
        tree = etree.parse(str(path))
        root = tree.getroot()

        ns_prefix = "{" + self.FM_NAMESPACE + "}" if root.tag.startswith("{") else ""
        ns = self.NAMESPACES if root.tag.startswith("{") else {}

        metadata = root.find(f".//{ns_prefix}METADATA", ns) or root.find(".//METADATA")
        if metadata is None:
            return []

        fields = metadata.findall(f"{ns_prefix}FIELD", ns) or metadata.findall("FIELD")
        return [f.get("NAME") for f in fields]
