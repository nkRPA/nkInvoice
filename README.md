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
1. installer whl fil:
```uv
uv add 
```
eller
```pip
pip install 
```

2. importer whl fil:
```python
from 
```
3. Opret .env fil
### Eksempel