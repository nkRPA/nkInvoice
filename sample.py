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
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="/Users/lakas/tmp/nkInvoice.log",
        filemode="w"
    )
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

