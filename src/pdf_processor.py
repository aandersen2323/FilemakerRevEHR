"""PDF Processor for FileMaker Internals Report"""

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import pdfplumber
import pandas as pd

logger = logging.getLogger(__name__)

SHEET_COLUMNS = [
    'Year', 'Month', 'Charges', 'Payments', 'Exams', 'Images', 'Image Fees',
    'CL evals', 'CL ann supply', 'cl units', 'walk in traffic', '99***',
    'Tot Service', 'Other Serv', 'Tot Balance', 'Patient Pd', 'OV fees',
    'CL fit fees', 'credit card', 'Insurance discount', 'check',
    'total CL fees', 'Period', 'Key'
]

MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']

@dataclass
class MonthlyRecord:
    year: int
    month: str
    charges: float
    payments: float
    exams: int
    images: int
    image_fees: float
    cl_evals: int
    cl_ann_supply: int
    cl_units: int
    walk_in_traffic: int
    code_99: int
    tot_service: float
    other_serv: float
    tot_balance: float
    patient_pd: float
    ov_fees: float
    cl_fit_fees: float
    credit_card: float
    insurance_discount: float
    check: float
    total_cl_fees: float

    @property
    def period(self) -> str:
        month_num = MONTH_NAMES.index(self.month) + 1
        return f"{self.year}-{month_num:02d}-01 0:00:00"

    @property
    def key(self) -> str:
        return self.period

    def to_sheet_row(self) -> list:
        return [self.year, self.month, self.charges, self.payments, self.exams,
                self.images, self.image_fees, self.cl_evals, self.cl_ann_supply,
                self.cl_units, self.walk_in_traffic, self.code_99, self.tot_service,
                self.other_serv, self.tot_balance, self.patient_pd, self.ov_fees,
                self.cl_fit_fees, self.credit_card, self.insurance_discount,
                self.check, self.total_cl_fees, self.period, self.key]

def parse_number(value: str) -> float:
    if not value or value.strip() in ('', '-', '?'): return 0.0
    cleaned = value.strip().replace(',', '')
    if cleaned.startswith('(') and cleaned.endswith(')'): cleaned = '-' + cleaned[1:-1]
    try: return float(cleaned)
    except ValueError: return 0.0

def parse_int(value: str) -> int:
    return int(parse_number(value))

class InternalsReportProcessor:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.records = []
        self.current_year = None

    def extract(self):
        logger.info(f"Processing PDF: {self.pdf_path}")
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    self._process_table(table)
        logger.info(f"Extracted {len(self.records)} records")
        return self.records

    def _process_table(self, table):
        if not table: return
        for row in table:
            if not row or len(row) < 5: continue
            first = (row[0] or '').strip()
            if first in ('', 'Date', 'Dr. Left') or 'Charges' in first: continue
            if first.startswith('Year') and len(first) == 8:
                try: self.current_year = int(first[4:])
                except: pass
                continue
            if first == 'Total': continue
            if first in MONTH_NAMES: self._process_month_row(first, row)

    def _process_month_row(self, month, row):
        if not self.current_year: return
        try:
            self.records.append(MonthlyRecord(
                year=self.current_year, month=month,
                charges=parse_number(row[2] if len(row)>2 else '0'),
                payments=parse_number(row[3] if len(row)>3 else '0'),
                exams=parse_int(row[4] if len(row)>4 else '0'),
                images=parse_int(row[5] if len(row)>5 else '0'),
                image_fees=parse_number(row[6] if len(row)>6 else '0'),
                cl_evals=parse_int(row[7] if len(row)>7 else '0'),
                cl_ann_supply=parse_int(row[8] if len(row)>8 else '0'),
                cl_units=parse_int(row[9] if len(row)>9 else '0'),
                walk_in_traffic=parse_int(row[10] if len(row)>10 else '0'),
                code_99=parse_int(row[11] if len(row)>11 else '0'),
                tot_service=parse_number(row[12] if len(row)>12 else '0'),
                other_serv=parse_number(row[13] if len(row)>13 else '0'),
                tot_balance=parse_number(row[14] if len(row)>14 else '0'),
                patient_pd=parse_number(row[15] if len(row)>15 else '0'),
                ov_fees=parse_number(row[16] if len(row)>16 else '0'),
                cl_fit_fees=parse_number(row[17] if len(row)>17 else '0'),
                credit_card=parse_number(row[18] if len(row)>18 else '0'),
                insurance_discount=parse_number(row[19] if len(row)>19 else '0'),
                check=parse_number(row[20] if len(row)>20 else '0'),
                total_cl_fees=parse_number(row[21] if len(row)>21 else '0')))
        except Exception as e:
            logger.warning(f"Error processing {month}: {e}")

    def to_dataframe(self):
        if not self.records: self.extract()
        return pd.DataFrame([r.to_sheet_row() for r in self.records], columns=SHEET_COLUMNS)

    def to_csv(self, output_path: str):
        df = self.to_dataframe()
        df.to_csv(output_path, index=False)
        return output_path

    def get_latest_month(self):
        if not self.records: self.extract()
        if not self.records: return None
        return max(self.records, key=lambda r: (r.year, MONTH_NAMES.index(r.month)))

def process_internals_report(pdf_path: str, output_csv=None, latest_only=False):
    processor = InternalsReportProcessor(pdf_path)
    processor.extract()
    if latest_only:
        latest = processor.get_latest_month()
        df = pd.DataFrame([latest.to_sheet_row()], columns=SHEET_COLUMNS) if latest else pd.DataFrame(columns=SHEET_COLUMNS)
    else:
        df = processor.to_dataframe()
    if output_csv: df.to_csv(output_csv, index=False)
    return df

if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python pdf_processor.py <pdf_path> [output.csv]")
        sys.exit(1)
    df = process_internals_report(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"Extracted {len(df)} records")
