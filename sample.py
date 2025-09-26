## ********************************************************************************************************************
## ********************************************************************************************************************
## Test and example usage
## ********************************************************************************************************************
## ********************************************************************************************************************
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    from datetime import date
    load_dotenv()
    opus_username = os.getenv('OPUS_USER')
    opus_userpassword = os.getenv('OPUS_USER_PASSWORD')
    opus_url = os.getenv('OPUS_URL')
    opus_municipality_code = int(os.getenv('OPUS_MUNICIPALITY_CODE'))
                                           
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    d = date.today()
    
    opus_data = {
        "url":opus_url,
        "municipality_code":opus_municipality_code,
        "username":opus_username, 
        "password":opus_userpassword
    }
    invoice_data = {
            "Debet_PSP":"XG-0000000204-00001",
            "Kredit_PSP":"XG-0000002473-00029",
            "Tekst":"Test af tekst",
            "Reference":"test af reference",
            "Bogføringsdato":d.strftime("%d.%m.%Y"), # -> "12.09.2025"
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
        invoice = nkInvoice(opus_data=opus_data, invoice_data=invoice_data)
        ## For testing, set headless to False and verbose to True
        invoice._headless=False
        invoice._verbose=True
        ## Set logger if needed
        invoice._logger=logging.getLogger(__name__)
        ## Create the invoice
        result = invoice.create_invoice()
        print(result)
    except Exception as e:
        print(f"Error: {e}")

