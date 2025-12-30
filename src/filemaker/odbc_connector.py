"""ODBC connector for FileMaker Pro 9.

FileMaker Pro 9 supports ODBC connections which allows direct
database access from external applications.

Requirements:
- FileMaker ODBC driver installed
- ODBC Data Source configured
- FileMaker sharing enabled for ODBC/JDBC
"""

import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

try:
    import pyodbc

    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    logger.warning("pyodbc not installed - ODBC connectivity unavailable")


class ODBCConnector:
    """ODBC connector for FileMaker Pro 9 database.

    This class provides methods to connect to FileMaker via ODBC
    and execute queries to extract data.
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        host: Optional[str] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize ODBC connector.

        Can use either DSN or connection parameters.

        Args:
            dsn: ODBC Data Source Name
            host: FileMaker server host
            database: Database/file name
            username: FileMaker account username
            password: FileMaker account password
        """
        if not PYODBC_AVAILABLE:
            raise ImportError("pyodbc is required for ODBC connectivity")

        self.dsn = dsn
        self.host = host
        self.database = database
        self.username = username
        self.password = password

        self._connection = None

    def _build_connection_string(self) -> str:
        """Build ODBC connection string."""
        if self.dsn:
            conn_str = f"DSN={self.dsn}"
            if self.username:
                conn_str += f";UID={self.username}"
            if self.password:
                conn_str += f";PWD={self.password}"
            return conn_str

        # Build connection string for FileMaker ODBC driver
        parts = [
            "DRIVER={FileMaker ODBC}",
            f"Server={self.host or 'localhost'}",
            f"Database={self.database}",
        ]
        if self.username:
            parts.append(f"UID={self.username}")
        if self.password:
            parts.append(f"PWD={self.password}")

        return ";".join(parts)

    def connect(self) -> None:
        """Establish ODBC connection."""
        if self._connection:
            return

        conn_str = self._build_connection_string()
        logger.info("Connecting to FileMaker via ODBC")

        try:
            self._connection = pyodbc.connect(conn_str)
            logger.info("ODBC connection established")
        except pyodbc.Error as e:
            logger.error(f"ODBC connection failed: {e}")
            raise

    def disconnect(self) -> None:
        """Close ODBC connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("ODBC connection closed")

    @contextmanager
    def connection(self):
        """Context manager for ODBC connection."""
        self.connect()
        try:
            yield self._connection
        finally:
            self.disconnect()

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as dictionaries.

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            List of dictionaries with column names as keys
        """
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            columns = [column[0] for column in cursor.description]
            results = []

            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results

        finally:
            cursor.close()

    def get_table_names(self) -> List[str]:
        """Get list of tables in the FileMaker database.

        Returns:
            List of table names
        """
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()
        try:
            tables = cursor.tables(tableType="TABLE")
            return [table.table_name for table in tables]
        finally:
            cursor.close()

    def get_column_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a table.

        Args:
            table_name: Name of the table

        Returns:
            List of column info dictionaries
        """
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()
        try:
            columns = cursor.columns(table=table_name)
            return [
                {
                    "name": col.column_name,
                    "type": col.type_name,
                    "size": col.column_size,
                    "nullable": col.nullable,
                }
                for col in columns
            ]
        finally:
            cursor.close()

    # =========================================================================
    # Patient Data Queries
    # =========================================================================

    def get_patients(
        self,
        table_name: str = "Patients",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve patient records from FileMaker.

        Note: Adjust field names based on your FileMaker schema.

        Args:
            table_name: Name of the patients table
            limit: Maximum records to retrieve

        Returns:
            List of patient dictionaries
        """
        query = f'SELECT * FROM "{table_name}"'
        if limit:
            query += f" FETCH FIRST {limit} ROWS ONLY"

        return self.execute_query(query)

    def get_patient_by_id(
        self,
        patient_id: str,
        table_name: str = "Patients",
        id_field: str = "PatientID",
    ) -> Optional[Dict[str, Any]]:
        """Get a single patient by ID.

        Args:
            patient_id: Patient ID to look up
            table_name: Name of the patients table
            id_field: Name of the ID field

        Returns:
            Patient dictionary or None
        """
        query = f'SELECT * FROM "{table_name}" WHERE "{id_field}" = ?'
        results = self.execute_query(query, (patient_id,))
        return results[0] if results else None

    # =========================================================================
    # Prescription Data Queries
    # =========================================================================

    def get_contact_lens_rx(
        self,
        table_name: str = "ContactLensRx",
        patient_id: Optional[str] = None,
        patient_id_field: str = "PatientID",
    ) -> List[Dict[str, Any]]:
        """Retrieve contact lens prescriptions.

        Args:
            table_name: Name of the CL Rx table
            patient_id: Filter by patient ID (optional)
            patient_id_field: Name of patient ID field

        Returns:
            List of CL Rx dictionaries
        """
        query = f'SELECT * FROM "{table_name}"'
        params = None

        if patient_id:
            query += f' WHERE "{patient_id_field}" = ?'
            params = (patient_id,)

        return self.execute_query(query, params)

    def get_glasses_rx(
        self,
        table_name: str = "GlassesRx",
        patient_id: Optional[str] = None,
        patient_id_field: str = "PatientID",
    ) -> List[Dict[str, Any]]:
        """Retrieve glasses prescriptions.

        Args:
            table_name: Name of the glasses Rx table
            patient_id: Filter by patient ID (optional)
            patient_id_field: Name of patient ID field

        Returns:
            List of glasses Rx dictionaries
        """
        query = f'SELECT * FROM "{table_name}"'
        params = None

        if patient_id:
            query += f' WHERE "{patient_id_field}" = ?'
            params = (patient_id,)

        return self.execute_query(query, params)
