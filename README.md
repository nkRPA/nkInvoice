# nkInvoice

Et Python-bibiliotek til at oprette fakturaer i OPUS (KMD)-systemet ved hjælp af Playwright browser-automatisering. Dette værktøj automatiserer processen med, at udfylde fakturaformularer og uploade CSV-filer til bogføringsposter.

## Funktioner

- **Automatiseret OPUS-integration**: Logger automatisk ind i OPUS-systemet med givet bruger, og navigerer til rollebaseret indgang.
- **CSV-import**: Genererer og uploader CSV-filer med bogføringsposter  
- **Filvedhæftninger**: Understøtter vedhæftning af bilag til fakturaer  
- **Datavalidering**: Indeholder validering af fakturadata ved hjælp af Pydantic-modeller  
- **Browserautomatisering**: Bruger Playwright til webautomatisering  
- **Fejlhåndtering**: Robust fejlhåndtering med detaljeret logning er mulig. 
- **Headless support**: Kan køre både i usynlig og synlig browsertilstand  

## Installation

### Forudsætninger

- Python 3.12 eller nyere  
- Chrome/Chromium-browser (til Playwright)  
- Playwright
- uv

### Opsætning

1. Klon repository’et:
```bash
git clone https://github.com/your-username/nkInvoice.git
cd nkInvoice
uv sync
````
### Brug af biblioteket

#### Standard installation
1. installer whl fil:
```uv
 uv add nkinvoice@git+https://github.com/nkRPA/nkInvoice.git
```

2. importer nkInvoice:
```python
from Invoice.src.nkInvoice import nkInvoice
```

3. Opret .env fil
```bash
OPUS_USER=bruger navnet på OPUS brugeren, som skal oprette bilaget eks. = "userjx"
OPUS_USER_PASSWORD=password for bruger navnet på OPUS brugeren, som skal oprette bilaget eks.= "Passw0rd"
OPUS_URL=KMD Url.. eks. ="https://ssolaunchpad.kmd.dk/"
OPUS_MUNICIPALITY_CODE=Kommune kode eks = 123
```

#### Docker installation og test
For at køre tests i en isoleret Docker-miljø:

1. **Klon repository'et og naviger til mappen:**
```bash
git clone https://github.com/your-username/nkInvoice.git
cd nkInvoice
```

2. **Opret .env fil fra template:**
```bash
cp env.example .env
# Rediger .env filen med dine faktiske OPUS credentials
nano .env
```

3. **Kør tests i Docker:**
```bash
# Interaktivt mode (kan se browser)
./run-docker-test.sh interactive

# Headless mode (usynlig browser)
./run-docker-test.sh headless
```

4. **Alternativt med docker-compose direkte:**
```bash
# Byg og kør container
docker-compose up --build nkinvoice-test

# Kør i headless mode
docker-compose up --build nkinvoice-headless
```

**Docker fordele:**
- Isoleret miljø uden konflikter med system dependencies
- Konsistent Playwright setup på alle platforme
- Nem cleanup efter tests
- Logs og output filer gemmes i `logs/` og `tmp/` mapper

#### Ubuntu Server Support
For Ubuntu server environments, use the optimized configuration:

```bash
# Ubuntu server optimized setup
./run-docker-ubuntu.sh headless

# Or with docker-compose directly
docker-compose -f docker-compose.ubuntu.yml up --build nkinvoice-headless
```

**Ubuntu server requirements:**
- Docker installed and running
- Docker Compose installed
- User in docker group: `sudo usermod -aG docker $USER`
- Virtual display support (Xvfb) for headless browser operation

**Quick Ubuntu server setup:**
```bash
# Install Docker Compose (if not already installed)
./install-docker-compose-ubuntu.sh

# Or install manually:
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again, or run: newgrp docker
```
### Eksempel kode
```python
import logging
from Invoice.src.nkInvoice import nkInvoice
import os
from dotenv import load_dotenv
from datetime import date
load_dotenv()
## Test and example usage
if __name__ == '__main__':
    ## Load environment variables    
    opus_username = os.getenv('OPUS_USER')
    opus_userpassword = os.getenv('OPUS_USER_PASSWORD')
    opus_url = os.getenv('OPUS_URL')
    opus_municipality_code = int(os.getenv('OPUS_MUNICIPALITY_CODE'))
    ## Setup logging if wanted                                           
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    

    ## Define the data for nkInvoice invoice creation    
    # Data for logging into OPUS
    opus_data = {
        "url":opus_url,
        "municipality_code":opus_municipality_code,
        "username":opus_username, 
        "password":opus_userpassword
    }
    # Data for creating the invoice
    invoice_data = {
            "Debet_PSP":"XG-0000000204-00001",
            "Kredit_PSP":"XG-0000002473-00029",
            "Tekst":"Test af tekst",
            "Reference":"test af reference",
            "Bogføringsdato":date.today().strftime("%d.%m.%Y"), # -> "12.09.2025"
            "Kommentar":"test af comment",
            "Debet_Artskonto":"40000000",
            "Kredit_Artskonto":"40000000",
            "Debet_PosteringsTekst":"Test af posterings tekst",
            "Kredit_PosteringsTekst":"Test af posterings tekst",
            "Kost":1.0,
            "BilagsFilePath":"/Users/lakas/tmp/file_path.txt",
            "csv_filename":"/Users/lakas/tmp/opus.csv"
        }
    try:
        # Create an instance of nkInvoice
        invoice = nkInvoice(opus_data=opus_data, invoice_data=invoice_data)
        # Set headless and verbose mode
        invoice._headless=False
        invoice._verbose=True
        ## Set logger if needed
        invoice._logger=logging.getLogger(__name__)
        ## Create the invoice
        result = invoice.create_invoice()
        # result is a dictionary with the result of the operation
        # eks. {"status": "success", "message": "Invoice created successfully", "bilag": "123456"}
        print(result)
    except Exception as e:
        print(f"Error: {e}")

```