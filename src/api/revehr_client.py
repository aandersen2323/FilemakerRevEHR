"""RevolutionEHR API client.

This module provides a client for interacting with the RevolutionEHR API.
Endpoints and authentication methods should be configured based on
RevolutionEHR's API documentation once available.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import requests

from .exceptions import (
    RevEHRAPIError,
    RevEHRAuthError,
    RevEHRNotFoundError,
    RevEHRValidationError,
    RevEHRRateLimitError,
)

logger = logging.getLogger(__name__)


class RevolutionEHRClient:
    """Client for RevolutionEHR API interactions.

    This client handles authentication and provides methods for
    CRUD operations on patients, prescriptions, and other entities.

    Note: Endpoint paths are placeholders and should be updated
    based on actual RevolutionEHR API documentation.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        timeout: int = 30,
    ):
        """Initialize the RevolutionEHR client.

        Args:
            base_url: Base URL for RevolutionEHR API
            api_key: API key for authentication (if using API key auth)
            client_id: OAuth client ID (if using OAuth)
            client_secret: OAuth client secret (if using OAuth)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout

        self._session = requests.Session()
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

        self._setup_session()

    def _setup_session(self) -> None:
        """Configure the requests session with default headers."""
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "FilemakerRevEHR/0.1.0",
        })

        if self.api_key:
            self._session.headers["Authorization"] = f"Bearer {self.api_key}"

    def _authenticate_oauth(self) -> None:
        """Authenticate using OAuth2 client credentials flow.

        Note: Implement based on RevolutionEHR's OAuth flow.
        """
        if not self.client_id or not self.client_secret:
            raise RevEHRAuthError("OAuth credentials not configured")

        # Placeholder - implement based on actual OAuth endpoint
        auth_url = f"{self.base_url}/oauth/token"

        try:
            response = self._session.post(
                auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self._token_expires = datetime.now().timestamp() + expires_in

            self._session.headers["Authorization"] = f"Bearer {self._access_token}"

        except requests.exceptions.RequestException as e:
            raise RevEHRAuthError(f"OAuth authentication failed: {e}")

    def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token."""
        if self.api_key:
            return  # Using API key auth

        if self._access_token and self._token_expires:
            if datetime.now().timestamp() < self._token_expires - 60:
                return  # Token still valid

        self._authenticate_oauth()

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            RevEHRAPIError: On API errors
            RevEHRAuthError: On authentication errors
            RevEHRNotFoundError: When resource not found
        """
        self._ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self._session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout,
            )

            if response.status_code == 401:
                raise RevEHRAuthError(
                    "Authentication failed",
                    status_code=401,
                    response=response.json() if response.text else None,
                )

            if response.status_code == 404:
                raise RevEHRNotFoundError(
                    "Resource not found",
                    status_code=404,
                    response=response.json() if response.text else None,
                )

            if response.status_code == 422:
                raise RevEHRValidationError(
                    "Validation error",
                    status_code=422,
                    response=response.json() if response.text else None,
                )

            if response.status_code == 429:
                raise RevEHRRateLimitError(
                    "Rate limit exceeded",
                    status_code=429,
                    response=response.json() if response.text else None,
                )

            response.raise_for_status()

            if response.text:
                return response.json()
            return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise RevEHRAPIError(f"Request failed: {e}")

    # =========================================================================
    # Patient Operations
    # =========================================================================

    def create_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new patient in RevolutionEHR.

        Args:
            patient_data: Patient data dictionary

        Returns:
            Created patient data with RevEHR ID
        """
        logger.info("Creating new patient in RevolutionEHR")
        return self._request("POST", "/api/v1/patients", data=patient_data)

    def get_patient(self, patient_id: str) -> Dict[str, Any]:
        """Get a patient by ID.

        Args:
            patient_id: RevolutionEHR patient ID

        Returns:
            Patient data
        """
        return self._request("GET", f"/api/v1/patients/{patient_id}")

    def update_patient(
        self, patient_id: str, patient_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing patient.

        Args:
            patient_id: RevolutionEHR patient ID
            patient_data: Updated patient data

        Returns:
            Updated patient data
        """
        logger.info(f"Updating patient {patient_id}")
        return self._request("PUT", f"/api/v1/patients/{patient_id}", data=patient_data)

    def search_patients(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        dob: Optional[str] = None,
        email: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for patients by criteria.

        Args:
            first_name: Patient first name
            last_name: Patient last name
            dob: Date of birth (YYYY-MM-DD)
            email: Email address

        Returns:
            List of matching patients
        """
        params = {}
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
        if dob:
            params["dob"] = dob
        if email:
            params["email"] = email

        result = self._request("GET", "/api/v1/patients/search", params=params)
        return result.get("patients", [])

    # =========================================================================
    # Contact Lens Prescription Operations
    # =========================================================================

    def create_contact_lens_rx(
        self, patient_id: str, rx_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a contact lens prescription.

        Args:
            patient_id: RevolutionEHR patient ID
            rx_data: Contact lens Rx data

        Returns:
            Created Rx with RevEHR ID
        """
        logger.info(f"Creating CL Rx for patient {patient_id}")
        return self._request(
            "POST",
            f"/api/v1/patients/{patient_id}/contact-lens-rx",
            data=rx_data,
        )

    def get_contact_lens_rx(self, patient_id: str, rx_id: str) -> Dict[str, Any]:
        """Get a contact lens prescription.

        Args:
            patient_id: RevolutionEHR patient ID
            rx_id: Prescription ID

        Returns:
            Contact lens Rx data
        """
        return self._request(
            "GET", f"/api/v1/patients/{patient_id}/contact-lens-rx/{rx_id}"
        )

    def list_contact_lens_rx(self, patient_id: str) -> List[Dict[str, Any]]:
        """List all contact lens prescriptions for a patient.

        Args:
            patient_id: RevolutionEHR patient ID

        Returns:
            List of CL prescriptions
        """
        result = self._request(
            "GET", f"/api/v1/patients/{patient_id}/contact-lens-rx"
        )
        return result.get("prescriptions", [])

    # =========================================================================
    # Glasses Prescription Operations
    # =========================================================================

    def create_glasses_rx(
        self, patient_id: str, rx_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a glasses prescription.

        Args:
            patient_id: RevolutionEHR patient ID
            rx_data: Glasses Rx data

        Returns:
            Created Rx with RevEHR ID
        """
        logger.info(f"Creating glasses Rx for patient {patient_id}")
        return self._request(
            "POST",
            f"/api/v1/patients/{patient_id}/glasses-rx",
            data=rx_data,
        )

    def get_glasses_rx(self, patient_id: str, rx_id: str) -> Dict[str, Any]:
        """Get a glasses prescription.

        Args:
            patient_id: RevolutionEHR patient ID
            rx_id: Prescription ID

        Returns:
            Glasses Rx data
        """
        return self._request(
            "GET", f"/api/v1/patients/{patient_id}/glasses-rx/{rx_id}"
        )

    def list_glasses_rx(self, patient_id: str) -> List[Dict[str, Any]]:
        """List all glasses prescriptions for a patient.

        Args:
            patient_id: RevolutionEHR patient ID

        Returns:
            List of glasses prescriptions
        """
        result = self._request("GET", f"/api/v1/patients/{patient_id}/glasses-rx")
        return result.get("prescriptions", [])

    # =========================================================================
    # Health Check
    # =========================================================================

    def health_check(self) -> bool:
        """Check if the API is accessible.

        Returns:
            True if API is healthy
        """
        try:
            self._request("GET", "/api/v1/health")
            return True
        except RevEHRAPIError:
            return False
