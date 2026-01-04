"""Monthly Report Automation Orchestrator"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

import yaml

from src.pdf_processor import InternalsReportProcessor, SHEET_COLUMNS, MONTH_NAMES
from src.google_sheets_integration import GoogleSheetsClient

logger = logging.getLogger(__name__)

class MonthlyReportSync:
    def __init__(self, config_path: str = 'config/settings.yaml'):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.sheets_client = None
        self.dry_run = False

    def _load_config(self):
        if not self.config_path.exists(): return {}
        with open(self.config_path) as f:
            return yaml.safe_load(f) or {}

    def _get_sheets_client(self):
        if self.sheets_client is None:
            gs = self.config.get('monthly_report', {}).get('google_sheets', {})
            self.sheets_client = GoogleSheetsClient(
                credentials_file=gs.get('credentials_file', 'config/google-sheets-credentials.json'),
                spreadsheet_id=gs.get('spreadsheet_id'),
                sheet_name=gs.get('sheet_name', 'Data'))
        return self.sheets_client

    def process_pdf(self, pdf_path: str, latest_only: bool = False):
        processor = InternalsReportProcessor(pdf_path)
        records = processor.extract()
        if not records: return []
        if latest_only:
            latest = max(records, key=lambda r: (r.year, MONTH_NAMES.index(r.month)))
            return [latest.to_sheet_row()]
        return [r.to_sheet_row() for r in records]

    def upload_to_sheets(self, rows: list, upsert: bool = True):
        if not rows: return {'uploaded': 0}
        if self.dry_run:
            logger.info(f"[DRY RUN] Would upload {len(rows)} rows")
            for r in rows: logger.info(f"  {r[0]} {r[1]}: Charges={r[2]}")
            return {'uploaded': 0, 'dry_run': True}
        client = self._get_sheets_client()
        for row in rows:
            if upsert: client.upsert_monthly_data(row[0], row[1], row)
            else: client.append_row(row)
        return {'uploaded': len(rows)}

    def run(self, pdf_path: str, latest_only: bool = True, dry_run: bool = False, upsert: bool = True):
        self.dry_run = dry_run
        rows = self.process_pdf(pdf_path, latest_only)
        if not rows: return {'success': False, 'error': 'No data extracted'}
        result = self.upload_to_sheets(rows, upsert)
        return {'success': True, 'rows': len(rows), **result}

def main():
    parser = argparse.ArgumentParser(description='Sync FileMaker report to Google Sheets')
    parser.add_argument('--pdf', required=True, help='Path to PDF')
    parser.add_argument('--config', default='config/settings.yaml')
    parser.add_argument('--latest-only', action='store_true', default=True)
    parser.add_argument('--all-months', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    syncer = MonthlyReportSync(args.config)
    result = syncer.run(args.pdf, latest_only=not args.all_months, dry_run=args.dry_run)

    if result['success']:
        print(f"Success! Rows: {result['rows']}")
    else:
        print(f"Failed: {result.get('error')}")
        sys.exit(1)

if __name__ == '__main__':
    main()
