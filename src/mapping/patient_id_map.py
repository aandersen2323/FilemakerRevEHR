"""Patient ID mapping between FileMaker and RevolutionEHR.

This module manages the bidirectional mapping of patient IDs between
FileMaker and RevolutionEHR systems. Mappings are persisted to a JSON
file to maintain state between sync runs.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class PatientIdMapper:
    """Manages patient ID mappings between FileMaker and RevEHR.

    The mapper stores:
    - filemaker_id → revehr_id (forward lookup)
    - revehr_id → filemaker_id (reverse lookup)
    - Metadata (first/last name, DOB) for verification
    - Timestamps for auditing

    Example mapping file structure:
    {
        "mappings": {
            "7081608": {
                "revehr_id": "pat_abc123",
                "first_name": "John",
                "last_name": "Smith",
                "dob": "1990-01-15",
                "created_at": "2025-12-30T02:30:00",
                "updated_at": "2025-12-30T02:30:00"
            }
        },
        "reverse_index": {
            "pat_abc123": "7081608"
        },
        "stats": {
            "total_mappings": 1,
            "last_sync": "2025-12-30T02:30:00"
        }
    }
    """

    def __init__(self, mapping_file: str = "data/patient_id_map.json"):
        """Initialize the mapper.

        Args:
            mapping_file: Path to JSON file storing mappings
        """
        self.mapping_file = Path(mapping_file)
        self._data: Dict[str, Any] = {
            "mappings": {},
            "reverse_index": {},
            "stats": {
                "total_mappings": 0,
                "last_sync": None,
            }
        }
        self._load()

    def _load(self) -> None:
        """Load mappings from file if it exists."""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, "r") as f:
                    self._data = json.load(f)
                logger.info(f"Loaded {len(self._data['mappings'])} patient mappings")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Error loading mapping file, starting fresh: {e}")
                self._data = {
                    "mappings": {},
                    "reverse_index": {},
                    "stats": {"total_mappings": 0, "last_sync": None}
                }

    def _save(self) -> None:
        """Persist mappings to file."""
        self.mapping_file.parent.mkdir(parents=True, exist_ok=True)

        # Update stats
        self._data["stats"]["total_mappings"] = len(self._data["mappings"])
        self._data["stats"]["last_sync"] = datetime.now().isoformat()

        with open(self.mapping_file, "w") as f:
            json.dump(self._data, f, indent=2)

        logger.debug(f"Saved {len(self._data['mappings'])} mappings to {self.mapping_file}")

    def get_revehr_id(self, filemaker_id: str) -> Optional[str]:
        """Look up RevEHR patient ID from FileMaker ID.

        Args:
            filemaker_id: FileMaker patient ID

        Returns:
            RevEHR patient ID if found, None otherwise
        """
        mapping = self._data["mappings"].get(str(filemaker_id))
        if mapping:
            return mapping.get("revehr_id")
        return None

    def get_filemaker_id(self, revehr_id: str) -> Optional[str]:
        """Look up FileMaker patient ID from RevEHR ID.

        Args:
            revehr_id: RevolutionEHR patient ID

        Returns:
            FileMaker patient ID if found, None otherwise
        """
        return self._data["reverse_index"].get(str(revehr_id))

    def add_mapping(
        self,
        filemaker_id: str,
        revehr_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        dob: Optional[str] = None,
    ) -> None:
        """Add or update a patient ID mapping.

        Args:
            filemaker_id: FileMaker patient ID
            revehr_id: RevolutionEHR patient ID
            first_name: Patient first name (for verification)
            last_name: Patient last name (for verification)
            dob: Date of birth (for verification)
        """
        fm_id = str(filemaker_id)
        re_id = str(revehr_id)
        now = datetime.now().isoformat()

        # Check if updating existing mapping
        existing = self._data["mappings"].get(fm_id)

        self._data["mappings"][fm_id] = {
            "revehr_id": re_id,
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
        }

        # Update reverse index
        self._data["reverse_index"][re_id] = fm_id

        # Auto-save after each addition
        self._save()

        action = "Updated" if existing else "Added"
        logger.debug(f"{action} mapping: FM:{fm_id} → RevEHR:{re_id}")

    def remove_mapping(self, filemaker_id: str) -> bool:
        """Remove a patient mapping.

        Args:
            filemaker_id: FileMaker patient ID to remove

        Returns:
            True if mapping was removed, False if not found
        """
        fm_id = str(filemaker_id)
        mapping = self._data["mappings"].pop(fm_id, None)

        if mapping:
            # Remove from reverse index
            revehr_id = mapping.get("revehr_id")
            if revehr_id:
                self._data["reverse_index"].pop(revehr_id, None)
            self._save()
            logger.info(f"Removed mapping for FileMaker ID: {fm_id}")
            return True

        return False

    def get_mapping_details(self, filemaker_id: str) -> Optional[Dict[str, Any]]:
        """Get full mapping details for a FileMaker patient ID.

        Args:
            filemaker_id: FileMaker patient ID

        Returns:
            Full mapping dict or None if not found
        """
        return self._data["mappings"].get(str(filemaker_id))

    def has_mapping(self, filemaker_id: str) -> bool:
        """Check if a FileMaker ID has a mapping.

        Args:
            filemaker_id: FileMaker patient ID

        Returns:
            True if mapping exists
        """
        return str(filemaker_id) in self._data["mappings"]

    def get_unmapped_patients(self, filemaker_ids: List[str]) -> List[str]:
        """Find FileMaker IDs that don't have mappings yet.

        Args:
            filemaker_ids: List of FileMaker patient IDs to check

        Returns:
            List of IDs without mappings
        """
        return [
            fm_id for fm_id in filemaker_ids
            if str(fm_id) not in self._data["mappings"]
        ]

    def get_all_mappings(self) -> Dict[str, str]:
        """Get all FileMaker → RevEHR mappings.

        Returns:
            Dict of filemaker_id: revehr_id
        """
        return {
            fm_id: data["revehr_id"]
            for fm_id, data in self._data["mappings"].items()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get mapping statistics.

        Returns:
            Stats dict with total_mappings and last_sync
        """
        return self._data["stats"].copy()

    def export_csv(self, output_file: str) -> None:
        """Export mappings to CSV for review.

        Args:
            output_file: Path to output CSV file
        """
        import csv

        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "filemaker_id", "revehr_id", "first_name",
                "last_name", "dob", "created_at", "updated_at"
            ])

            for fm_id, data in self._data["mappings"].items():
                writer.writerow([
                    fm_id,
                    data.get("revehr_id", ""),
                    data.get("first_name", ""),
                    data.get("last_name", ""),
                    data.get("dob", ""),
                    data.get("created_at", ""),
                    data.get("updated_at", ""),
                ])

        logger.info(f"Exported {len(self._data['mappings'])} mappings to {output_file}")
