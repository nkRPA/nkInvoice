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


def send_internal_email(
    receiver_email,
    subject,
    body,
    smtp_server='smtp.naestved.dk',
    smtp_port=25,
    sender_email="serviceChecker@naestved.dk",
    logger=None,
    attachments=None
):
    """
    Sends an email using the specified SMTP server.
    
    :param receiver_email: The email address of the receiver.
    :param subject: The subject of the email.
    :param body: The body content of the email.
    :param smtp_server: The SMTP server address.
    :param smtp_port: The port number for the SMTP server.
    :param sender_email: The email address of the sender.
    :param logger: Optional logger for error handling.
    :param attachments: List of file paths to attach.
    """
    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Add attachments if provided
    if attachments:
        for file_path in attachments:
            try:
                with open(file_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                msg.attach(part)
            except Exception as e:
                if logger:
                    logger.error(f"Could not attach file {file_path}: {e}")
                else:
                    print(f"Could not attach file {file_path}: {e}")

    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.send_message(msg)
        
    except Exception as e:
        if logger:
            logger.error(f"Failed to send email to {receiver_email}. Error: {e}")
        else:
            print(f"Failed to send email: {e}")

async def main():
    receiver_email = "lakas@naestved.dk"
    subject = "Test email from nkInvoice"
    body = "This is a test email sent from the nkInvoice script."
    
    bilags_file_path = "file_path.txt"
    csv_filename = "opus.csv"
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
    invoice_data = {
            "Debet_PSP":"",#"XG-0000000204-00001",
            "Kredit_PSP":"",#"XG-0000002473-00029",
            "Tekst":"Test af tekst",
            "Reference":"test af ref",
            "Bogføringsdato":date.today().strftime("%d.%m.%Y"), # -> "12.09.2025"
            "Kommentar":"test af comment",
            "Debet_Artskonto":"95910388",#"40000000",
            "Kredit_Artskonto":"95910388",#"40000000",
            "Debet_PosteringsTekst":"Test postering",
            "Kredit_PosteringsTekst":"Test postering",
            "Kost":1.0,
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
