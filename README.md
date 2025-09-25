# nkInvoice

A Python automation tool for creating invoices in the Danish OPUS (KMD) system using Playwright browser automation. This tool automates the process of filling out invoice forms and uploading CSV files for accounting entries.

## Features

- **Automated OPUS Integration**: Automatically logs into the OPUS system and navigates to invoice creation
- **CSV Import**: Generates and uploads CSV files with accounting entries
- **File Attachments**: Supports attaching documents to invoices
- **Data Validation**: Comprehensive validation of invoice data using Pydantic models
- **Browser Automation**: Uses Playwright for reliable web automation
- **Error Handling**: Robust error handling with detailed logging
- **Headless Support**: Can run in both headless and visible browser modes

## Installation

### Prerequisites

- Python 3.12 or higher
- Chrome/Chromium browser (for Playwright)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/nkInvoice.git
cd nkInvoice
```

2. Install dependencies using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with your OPUS credentials:

```env
OPUS_USER=your_username
OPUS_USER_PASSWORD=your_password
```

### Database Configuration

The project uses `nkDatabase` for database operations. Configure your database settings in `database.ini`:

```ini
[postgresql]
host=localhost
database=your_database
user=your_user
password=your_password
```

## Usage

### Basic Example

```python
from Invoice.src.nkInvoice import nkInvoice, OpusConfig, InvoiceData
from datetime import date
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OPUS configuration
opus_config = OpusConfig(
    municipality_code=370,  # Your municipality code
    username="your_username",
    password="your_password"
)

# Invoice data
invoice_data = InvoiceData(
    Debet_PSP="XG-0000000204-00001",
    Kredit_PSP="XG-0000002473-00029", 
    Tekst="Invoice description",
    Reference="REF-001",
    Bogføringsdato="12.09.2025",  # Format: dd.mm.yyyy
    Kommentar="Additional comments",
    Debet_Artskonto="40000000",  # 8-digit account number
    Kredit_Artskonto="40000000",  # 8-digit account number
    Debet_PosteringsTekst="Debit posting text",
    Kredit_PosteringsTekst="Credit posting text",
    Kost=1000.0,  # Amount (must be > 0)
    BilagsFilePath="/path/to/attachment.pdf",  # Optional file attachment
    csv_filename="/path/to/output.csv"  # CSV file for accounting entries
)

# Create invoice
invoice = nkInvoice(
    opus_data=opus_config,
    invoice_data=invoice_data
)

# Optional: Configure logging and browser mode
invoice._logger = logger
invoice._headless = True  # Set to False for visible browser
invoice._verbose = True   # Enable detailed logging

# Create the invoice
result = invoice.create_invoice()
print(result)
```

### Advanced Configuration

```python
# Enable verbose logging for debugging
invoice._verbose = True

# Run in visible browser mode for debugging
invoice._headless = False

# Set custom logger
import logging
logger = logging.getLogger("custom_logger")
invoice._logger = logger
```

## Data Models

### OpusConfig

Configuration for OPUS system access:

- `municipality_code` (int): Your municipality code (required)
- `username` (str): OPUS username (required)
- `password` (str): OPUS password (required)
- `url` (str): OPUS URL (optional, defaults to KMD launchpad)

### InvoiceData

Invoice data with validation:

- `Debet_PSP` (str): Debit PSP element
- `Kredit_PSP` (str): Credit PSP element  
- `Tekst` (str): Invoice description (required, cannot be empty)
- `Reference` (str): Reference number
- `Bogføringsdato` (str): Booking date in format "dd.mm.yyyy"
- `Kommentar` (str): Comments
- `Debet_Artskonto` (str): Debit account (8 digits)
- `Kredit_Artskonto` (str): Credit account (8 digits)
- `Debet_PosteringsTekst` (str): Debit posting text
- `Kredit_PosteringsTekst` (str): Credit posting text
- `Kost` (float): Amount (must be > 0)
- `BilagsFilePath` (str): Path to attachment file (optional)
- `csv_filename` (str): Path for generated CSV file

### Validation Rules

- **PSP Elements**: Both `Debet_PSP` and `Kredit_PSP` must either both be empty or both filled
- **Tekst**: Cannot be empty
- **Bogføringsdato**: Must be in format "dd.mm.yyyy" or empty
- **Artskonto**: Must be exactly 8 digits
- **Kost**: Must be greater than 0
- **File Paths**: Must point to valid files if provided

## Return Values

The `create_invoice()` method returns a dictionary with:

```python
{
    "status": "Succes" | "Fejlet",
    "message": "Bilag oprettet" | "Bilag ikke oprettet", 
    "Bilag": "Omposteringsbilaget er kontrolleret og OK" | error_message
}
```

## Testing

Run the test suite:

```bash
python -m pytest test/
```

Or run specific tests:

```bash
python test/Invoice_test.py
```

## Dependencies

- **playwright**: Browser automation
- **pydantic**: Data validation and settings management
- **python-dotenv**: Environment variable loading
- **nkdatabase**: Database operations (from nkCommon/nkDatabase_Public)

## Error Handling

The tool includes comprehensive error handling:

- **Login Errors**: Detects and reports authentication failures
- **Validation Errors**: Validates all input data before processing
- **Browser Errors**: Handles browser automation failures
- **File Errors**: Validates file paths and attachments

## Troubleshooting

### Common Issues

1. **Login Failed**: Check your OPUS credentials and municipality code
2. **File Not Found**: Ensure all file paths are correct and files exist
3. **Browser Issues**: Make sure Playwright browsers are installed
4. **Validation Errors**: Check that all required fields are filled and formatted correctly

### Debug Mode

Enable verbose logging and visible browser for debugging:

```python
invoice._verbose = True
invoice._headless = False
```

## License

This project is part of the nkCommon suite. Please refer to the main project license.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For issues and questions, please create an issue in the repository or contact the development team.