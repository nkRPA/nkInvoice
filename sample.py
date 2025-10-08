import logging
from Invoice.src.nkInvoice import nkInvoice
import os
from dotenv import load_dotenv
from datetime import date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import asyncio

load_dotenv()




async def main():
    receiver_email = "lakas@naestved.dk"
    subject = "Test email from nkInvoice"
    body = "This is a test email sent from the nkInvoice script."
    
    
    bilags_file_path = "/Users/lakas/tmp/file_path.txt"
    csv_filename = "/Users/lakas/tmp/opus.csv"
    log_filename="nkInvoice.log"
    # send_internal_email(receiver_email, subject, body, smtp_server='smtp.naestved.dk', smtp_port=2552, sender_email="InvoiceTester@naestved.dk")

    ## Load environment variables    
    opus_username = os.getenv('OPUS_USER')
    opus_userpassword = os.getenv('OPUS_USER_PASSWORD')
    opus_url = os.getenv('OPUS_URL')
    opus_municipality_code = int(os.getenv('OPUS_MUNICIPALITY_CODE'))
    ## Setup logging if wanted                                           
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
        #filename=log_filename,
        #filemode="w"
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
    cost1:float = 1.0
    cost2:float = 2.0

   
    cost_data_list = [
            {
                "Debet_Artskonto":"40000000",
                "Kredit_Artskonto":"40000000",
                "Debet_PSP_element":"XG-0000000204-00001",
                "Kredit_PSP_element":"XG-0000002473-00029",
                "Kost":cost1,
                "Debet_PosteringsTekst":"Test postering 1",
                "Kredit_PosteringsTekst":"Test postering 1"
            },
            {
                "Debet_Artskonto":"40000000",
                "Kredit_Artskonto":"40000000",
                "Debet_PSP_element":"XG-0000000204-00001",
                "Kredit_PSP_element":"XG-0000002473-00029",
                "Kost":cost2
                "Debet_PosteringsTekst":"Test postering 2",
                "Kredit_PosteringsTekst":"Test postering 2"
            }
        ]

    invoice_data = {
            "Tekst":"Test af tekst",
            "opus_cost_data":cost_data_list,
            "Reference":"test af ref",
            "Bogføringsdato":date.today().strftime("%d.%m.%Y"), # -> "12.09.2025"
            "Kommentar":"test af comment",
            "BilagsFilePath":bilags_file_path,
            "csv_filename":csv_filename
        }
    retries = 1
        # Try multiple times to find the correct iframe and attach the file
    for attempt in range(retries):
        try:
            print(f"** Create Invoice attempt {attempt + 1} of {retries}")
            logger.info(f"** Create Invoice attempt {attempt + 1} of {retries}")
            # Create an instance of nkInvoice
            invoice = nkInvoice(opus_data=opus_data, invoice_data=invoice_data)
            # Set headless and verbose mode
            invoice._headless=False
            invoice._verbose=True
            ## Set logger if needed
            invoice._logger=logging.getLogger(__name__)
            ## Create the invoice
            result = await invoice.create_invoice(max_retries=3, try_number=1) 
            # result is a dictionary with the result of the operation
            # eks. {"status": "success", "message": "Invoice created successfully", "bilag": "123456"}
            logger.info(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
            logger.error(f"Error: {e}")


    # send_internal_email(receiver_email, subject, body, smtp_server='smtp.naestved.dk', smtp_port=2552, sender_email="InvoiceTester@naestved.dk", attachments=[log_filename])
    
## Test and example usage
if __name__ == '__main__':
    asyncio.run(main())
