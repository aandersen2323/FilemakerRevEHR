"""Transformer for FileMaker Transaction data to RevEHR Contact Lens Rx format."""

from typing import Dict, Any, List, Optional
from datetime import date
from ..models.transaction import (
    Transaction,
    ContactLensRx,
    TRANSACTION_FIELD_MAPPING,
    parse_str,
    parse_date,
    parse_int,
)


def row_to_transaction(row: List[str]) -> Transaction:
    """
    Convert a CSV row (list of values) to a Transaction object.

    Args:
        row: List of string values from CSV (38 columns expected)

    Returns:
        Transaction object with parsed data
    """
    tx = Transaction(
        transaction_num='',
        patient_id='',
        cl_od=ContactLensRx(),
        cl_os=ContactLensRx(),
        cl_od_alt=ContactLensRx(),
        cl_os_alt=ContactLensRx(),
    )

    for idx, value in enumerate(row):
        if idx not in TRANSACTION_FIELD_MAPPING:
            continue

        field_path, parser = TRANSACTION_FIELD_MAPPING[idx]
        parsed_value = parser(value)

        # Handle nested fields (e.g., 'cl_od.lens_name')
        if '.' in field_path:
            obj_name, attr_name = field_path.split('.')
            obj = getattr(tx, obj_name)
            setattr(obj, attr_name, parsed_value)
        else:
            setattr(tx, field_path, parsed_value)

    return tx


def transaction_to_revehr_cl_rx(tx: Transaction) -> Optional[Dict[str, Any]]:
    """
    Transform a Transaction to RevEHR Contact Lens Rx format.

    Only returns data if the transaction has CL Rx information.

    Args:
        tx: Transaction object with CL data

    Returns:
        Dict formatted for RevEHR API, or None if no CL data
    """
    if not tx.has_cl_rx():
        return None

    # Build RevEHR CL Rx payload (field names from RevEHR API docs)
    # Note: patient_id is passed separately to API call in sync.py
    payload = {
        # Rx metadata
        'rx_date': tx.transaction_date.isoformat() if tx.transaction_date else None,
        'expiration_date': tx.expiration_date.isoformat() if tx.expiration_date else None,

        # OD (Right Eye) - RevEHR field names
        'od_product_name': tx.cl_od.lens_name,
        'od_base_curve': tx.cl_od.base_curve,
        'od_diameter': tx.cl_od.diameter,
        'od_sphere': tx.cl_od.sphere,
        'od_cylinder': tx.cl_od.cylinder,
        'od_axis': str(tx.cl_od.axis) if tx.cl_od.axis else None,
        'od_add': tx.cl_od.add_power,
        'od_lens_type': 'soft',  # Default; could detect from lens name

        # OS (Left Eye) - RevEHR field names
        'os_product_name': tx.cl_os.lens_name,
        'os_base_curve': tx.cl_os.base_curve,
        'os_diameter': tx.cl_os.diameter,
        'os_sphere': tx.cl_os.sphere,
        'os_cylinder': tx.cl_os.cylinder,
        'os_axis': str(tx.cl_os.axis) if tx.cl_os.axis else None,
        'os_add': tx.cl_os.add_power,
        'os_lens_type': 'soft',  # Default; could detect from lens name

        # External reference for deduplication
        'external_rx_id': tx.transaction_num,
    }

    # Add alternate lens data if present (secondary Rx in FileMaker)
    if tx.cl_od_alt.has_data():
        payload['od_alt_product_name'] = tx.cl_od_alt.lens_name
        payload['od_alt_base_curve'] = tx.cl_od_alt.base_curve
        payload['od_alt_diameter'] = tx.cl_od_alt.diameter
        payload['od_alt_sphere'] = tx.cl_od_alt.sphere
        payload['od_alt_cylinder'] = tx.cl_od_alt.cylinder
        payload['od_alt_axis'] = str(tx.cl_od_alt.axis) if tx.cl_od_alt.axis else None
        payload['od_alt_add'] = tx.cl_od_alt.add_power

    if tx.cl_os_alt.has_data():
        payload['os_alt_product_name'] = tx.cl_os_alt.lens_name
        payload['os_alt_base_curve'] = tx.cl_os_alt.base_curve
        payload['os_alt_diameter'] = tx.cl_os_alt.diameter
        payload['os_alt_sphere'] = tx.cl_os_alt.sphere
        payload['os_alt_cylinder'] = tx.cl_os_alt.cylinder
        payload['os_alt_axis'] = str(tx.cl_os_alt.axis) if tx.cl_os_alt.axis else None
        payload['os_alt_add'] = tx.cl_os_alt.add_power

    # Remove None and empty values
    return {k: v for k, v in payload.items() if v is not None and v != ''}


def filter_cl_transactions(transactions: List[Transaction]) -> List[Transaction]:
    """
    Filter transactions to only those with Contact Lens Rx data.

    Args:
        transactions: List of all transactions

    Returns:
        List of transactions that have CL data
    """
    return [tx for tx in transactions if tx.has_cl_rx()]


def transform_transactions_to_cl_rx(rows: List[List[str]]) -> List[Dict[str, Any]]:
    """
    Transform CSV rows to RevEHR CL Rx records.

    Main entry point for the transformer.

    Args:
        rows: List of CSV rows (each row is a list of values)

    Returns:
        List of RevEHR-formatted CL Rx records
    """
    results = []

    for row in rows:
        tx = row_to_transaction(row)

        if tx.has_cl_rx():
            revehr_data = transaction_to_revehr_cl_rx(tx)
            if revehr_data:
                results.append(revehr_data)

    return results
