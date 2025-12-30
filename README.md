# FilemakerRevEHR

Connector for integrating FileMaker Pro 9 local database with RevolutionEHR.

## Overview

This middleware application transfers data between a local FileMaker Pro 9 database and RevolutionEHR cloud-based EHR system.

### Supported Data Transfers

- **Patient Demographics** - Names, addresses, contact info, DOB, etc.
- **Contact Lens Prescriptions** - CL Rx with all parameters
- **Glasses Prescriptions** - Spectacle Rx with full details
- **Insurance Information** (planned)
- **Accounting/Billing** (planned)

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  FileMaker 9    │────▶│  FilemakerRevEHR │────▶│  RevolutionEHR  │
│  (Local DB)     │     │   (Middleware)   │     │   (Cloud API)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### FileMaker 9 Data Extraction Methods

FileMaker Pro 9 supports several methods for data extraction:

1. **ODBC Connection** - Direct database access via ODBC driver
2. **XML Export** - FileMaker can export data as XML
3. **File Export** - CSV/Tab-delimited file exports via FileMaker scripts

## Project Structure

```
FilemakerRevEHR/
├── src/
│   ├── api/              # RevolutionEHR API client
│   ├── models/           # Data models (Patient, Rx, etc.)
│   ├── filemaker/        # FileMaker data extraction
│   └── transformers/     # Data transformation logic
├── config/               # Configuration files
├── tests/                # Unit and integration tests
└── docs/                 # Documentation
```

## Installation

```bash
# Clone the repository
git clone https://github.com/aandersen2323/FilemakerRevEHR.git
cd FilemakerRevEHR

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure settings
cp config/settings.example.yaml config/settings.yaml
```

## Configuration

Edit `config/settings.yaml` with your credentials:

```yaml
revolutionehr:
  base_url: "https://api.revolutionehr.com"
  api_key: "your-api-key"

filemaker:
  method: "odbc"  # or "xml" or "file"
  dsn: "FileMaker_DSN"
  # ... additional settings based on method
```

## Usage

```python
from src.api.revehr_client import RevolutionEHRClient
from src.filemaker.extractor import FileMakerExtractor
from src.transformers.patient import PatientTransformer

# Extract from FileMaker
extractor = FileMakerExtractor()
patients = extractor.get_patients()

# Transform and send to RevolutionEHR
client = RevolutionEHRClient()
transformer = PatientTransformer()

for patient in patients:
    revehr_patient = transformer.to_revehr(patient)
    client.create_patient(revehr_patient)
```

## License

MIT License
