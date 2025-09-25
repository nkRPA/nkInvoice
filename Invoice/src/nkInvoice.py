import re
import csv
import sys
from playwright.sync_api import Playwright, sync_playwright, expect
from playwright.sync_api import Browser, BrowserContext, Page
# from setup.Constants import Constants
from pydantic import BaseModel, Field, ValidationError, computed_field, ConfigDict, PrivateAttr, field_validator, model_validator, constr, FilePath, ValidationInfo, confloat
from typing import Optional, Union
from Invoice.src._helpers import _exception_helper
import logging
from enum import Enum, auto

OPUS_CSV_HEADERS = ["Artskonto", "Omkostningssted", "PSP-element", "Profitcenter", "Ordre", "Debet/kredit", "Beløb", "Næste agent", "Tekst", "Betalingsart", "Påligningsår", "Betalingsmodtagernr.", "Betalingsmodtagernr.kode", "Ydelsesmodtagernr.", "Ydelsesmodtagernr.kode", "Ydelsesperiode fra", "Ydelsesperiode til", "Oplysningspligtnr.", "Oplysningspligtmodtagernr.kode", "Oplysningspligtkode", "Netværk", "Operation", "Mængde", "Mængdeenhed", "Referencenøgle"] 
IFRAME_SELECTORS = [
                'iframe[name*="URLSPW"]',
                'iframe[name*="SPW"]',
                'iframe[name*="URL"]',
                'iframe[name*="popup"]',
                'iframe[name*="dialog"]',
                'iframe[name*="modal"]',
                'iframe[name*="content"]',
                'iframe[name*="work"]',
                'iframe:visible'
            ]
class LogLevel(Enum):
    INFO = auto()
    ERROR = auto()
    WARNING = auto()
    DEBUG = auto()
    
#### ********************************************************************************************************************
#### ********************************************************************************************************************
class OpusConfig(BaseModel):
    """ Class for handling Opus configuration. """
    # Attributes
    url: str = Field(default="https://ssolaunchpad.kmd.dk/")

    municipality_code: int  # required
    username: str           # required
    password: str           # required

    def valid_url(self) -> str:
        base_url = self.url.rstrip("/")
        return f"{base_url}/?kommune={self.municipality_code}"
#### ********************************************************************************************************************
#### ********************************************************************************************************************
class InvoiceData(BaseModel):
    Debet_PSP: str
    Kredit_PSP: str
    Tekst: str
    Reference: str
    Bogføringsdato: str
    Kommentar: str
    Debet_Artskonto: str
    Kredit_Artskonto: str
    Debet_PosteringsTekst: str
    Kredit_PosteringsTekst: str
    Kost: confloat(gt=0.0)
    BilagsFilePath: Union[FilePath, str] = ""
    csv_filename: FilePath

    # --- Validators ---

    @field_validator("Tekst")
    def validate_tekst_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Tekst must not be empty")
        return v

    @field_validator("Bogføringsdato")
    def validate_date_format(cls, v):
        if len(v.strip()) == 0:
            return v  # allow empty
        if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", v):
            raise ValueError("Bogføringsdato must be in format dd.mm.yyyy (e.g. 12.09.2025)")
        return v

    @field_validator("Debet_Artskonto", "Kredit_Artskonto")
    def validate_artskonto(cls, v, info: ValidationInfo):
        if not v.isdigit() or len(v) != 8:
            raise ValueError(f"{info.field_name} must be exactly 8 digits (e.g. 40000000)")
        return v
    
    @field_validator("BilagsFilePath")
    def allow_empty_or_valid_path(cls, v):
        if v == "":
            return v
        return FilePath(v) 
    
    # --- Cross-field validator ---
    @model_validator(mode="after")
    def validate_psp_pair(self):
        debet = self.Debet_PSP.strip()
        kredit = self.Kredit_PSP.strip()

        if (len(debet) == 0 and len(kredit) == 0) or (len(debet) > 0 and len(kredit) > 0):
            return self

        raise ValueError("Debet_PSP and Kredit_PSP must either both be empty or both filled")
        
#### ********************************************************************************************************************
#### ********************************************************************************************************************
class nkInvoice(BaseModel):
    """ Class for handling invoices and interactions with the Opus system. """    
    # Private attributes
    _browser: Optional[Browser] = PrivateAttr(default=None)
    _context: Optional[BrowserContext] = PrivateAttr(default=None)
    _page: Optional[Page] = PrivateAttr(default=None)
    _result: Optional[dict] = PrivateAttr(default=None)
    

    # Attributes
    model_config = ConfigDict(extra='forbid', strict=True)
    invoice_data: InvoiceData
    opus_data: OpusConfig
    _headless: bool = False
    _verbose: bool = False    
    _logger: logging.Logger = None
    ### ------------------------------------------------------------------------------------------------------
    ### Methods
    ### ------------------------------------------------------------------------------------------------------
    ### PUBLIC METHODS
    def create_invoice(self):
        """Create an invoice in the Opus system using Playwright."""  
        self._log(message="Start creation of invoice", level=LogLevel.INFO)
        with sync_playwright() as playwright:
            self._create_csv()
            self._start_opus_rollebaseret(playwright)
            self._fill_opus_page()
            self._context.close()
            self._browser.close()
            self._log(message="End creation of invoice", level=LogLevel.INFO)
            return self._result
    ### ------------------------------------------------------------------------------------------------------
    ### PRIVATE METHODS
    def verbose_log_frames(self):
        if self._verbose:
            frames = self._page.frames
            self._log(message=f"Total frames found: {len(frames)}", level=LogLevel.DEBUG)
            for i, frame in enumerate(frames):
                self._log(message=f"Frame {i}: name='{frame.name}'", level=LogLevel.DEBUG)
                
    def _log_verbose(self, message: str):
        if self._verbose:
            self._log(message=message, level=LogLevel.DEBUG)

    def _log(self, message: str, level: LogLevel = LogLevel.INFO):
        if self._logger:
            if level == LogLevel.INFO:
                self._logger.info(message)
            elif level == LogLevel.ERROR:
                self._logger.error(message)
            elif level == LogLevel.WARNING:
                self._logger.warning(message)
            elif level == LogLevel.DEBUG:
                self._logger.debug(message)
        else:
            self._verbose = False
    ### ***********************************************************
    ### ***********************************************************
    @_exception_helper
    def _fill_opus_page(self):
        # Fill the OPUS page with invoice data
        self._log(message="Start filling data in OPUS page", level=LogLevel.INFO)
        Invoice = "Fejlet"
        status_text = "Ikke afviklet"
        text = "Ikke afviklet"
        # Wait for page to load
        self._log_verbose(message="Waiting for OPUS page to load")
        self._page.wait_for_load_state('networkidle')
        # bogføringsdato
        self._fill_value(label_name="Bogføringsdato", value=self.invoice_data.Bogføringsdato)
        # Tekst
        self._fill_value(label_name="Tekst", value=self.invoice_data.Tekst)
        # Reference
        self._fill_value(label_name="Reference", value=self.invoice_data.Reference)
        # Kommentarer     
        self._fill_comments(value=self.invoice_data.Kommentar)
        # Vedhæft bilag
        self._fill_attachment()
        # Indsæt csv posteringer
        self._fill_csv()
        # Kontroller bilag
        status_text = self._check_invoice()
        self._log_verbose(message=f"Status text after checking invoice: {status_text}")
        if status_text == 'Omposteringsbilaget er kontrolleret og OK':
            Invoice = "Succes"
            text = "Bilag oprettet"
        else:
            Invoice = "Fejlet"
            text = "Bilag ikke oprettet"
        # Opret bilag
        self._result = {"status": Invoice, "message": text, "Bilag": status_text}
        self._log_verbose(message=f"End filling data in OPUS page with result: {self._result}")
    ### ***********************************************************
    def check_login_error(self):
        # Wait until the form is visible (ensures DOM is loaded)
        try:
            self._log_verbose(message="Checking for login error messages")
            self._page.wait_for_selector("#loginForm", timeout=2000)

            # Check if error element exists and is visible
            error_locator = self._page.locator("#errorText")

            if error_locator.is_visible():
                error_message = error_locator.inner_text()
                self._log_verbose(message=f"Login error message found: {error_message}")
                return error_message
            else:
                return None            
        except:
            self._log_verbose(message="No login error message found")
            return None
    ### ***********************************************************
    @_exception_helper
    def _start_opus_rollebaseret(self, playwright)-> tuple[Browser, BrowserContext, Page]:
        self._browser = playwright.chromium.launch(headless=self._headless)
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        url = self.opus_data.valid_url()
        self._page.goto(url)
        self._page.get_by_role("textbox", name="User Account").fill(self.opus_data.username)
        self._page.get_by_role("textbox", name="Password").fill(self.opus_data.password)
        self._page.get_by_role("button", name="Sign in").click()
        
        try:
            self._log_verbose(message="Waiting for network to be idle after login")
            self._page.wait_for_load_state('networkidle', timeout=10000)
        except:
            pass
        
        error_message = self.check_login_error()
        if error_message:
            raise RuntimeError(f"Login failed: {error_message}")
        
        self._page.locator("#externalCol").get_by_role("button").click()
        self._page.get_by_text("Bilagsbehandling").click()
        self._page.get_by_text("Opret omposteringsbilag").click()
    ### ***********************************************************
    @_exception_helper
    def _create_csv(self):
        """Create a CSV file for Opus import based on invoice data."""
        self._log(message="Creating CSV file for Opus import", level=LogLevel.INFO)
        ### Verbose logging of data from invoice_data
        self._log_verbose(message=f"Debet arts konto: {self.invoice_data.Debet_Artskonto}")
        self._log_verbose(message=f"Kredit arts konto: {self.invoice_data.Kredit_Artskonto}")
        self._log_verbose(message=f"Debet PSP: {self.invoice_data.Debet_PSP}")
        self._log_verbose(message=f"Kredit PSP: {self.invoice_data.Kredit_PSP}")
        self._log_verbose(message=f"Kost: {self.invoice_data.Kost}")
        self._log_verbose(message=f"Debet posterings tekst: {self.invoice_data.Debet_PosteringsTekst}")
        self._log_verbose(message=f"Kredit posterings tekst: {self.invoice_data.Kredit_PosteringsTekst}")
        
        csv_data = [
            [
                self.invoice_data.Debet_Artskonto,
                "",
                self.invoice_data.Debet_PSP,
                "",
                "",
                "Debet",
                self.invoice_data.Kost,
                "",
                self.invoice_data.Debet_PosteringsTekst,
                "","","","","","","","","","","","","","",""
            ],
            [
                self.invoice_data.Kredit_Artskonto,
                "",
                self.invoice_data.Kredit_PSP,
                "",
                "",
                "Kredit",
                self.invoice_data.Kost,
                "",
                self.invoice_data.Kredit_PosteringsTekst,
                "","","","","","","","","","","","","","",""
            ]
        ]
        self._log_verbose(message=f"CSV data to write: {csv_data}")
        self._create_opus_csv(data=csv_data)
    ### ***********************************************************
    @_exception_helper
    def _create_opus_csv(self, data):
        self._log(message="Writing CSV file for Opus import", level=LogLevel.INFO)
        headers = OPUS_CSV_HEADERS
        with open(self.invoice_data.csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile,delimiter=';')
            writer.writerow(headers)
            writer.writerows(data)
        
        # return f"CSV file '{filename}' created successfully with {len(data)} rows"
    ### ***********************************************************
    @_exception_helper
    def _fill_value(self, label_name, value):
        if not value or len(value.strip()) == 0:
            return
        self._log(message=f"Filling value for {label_name}: {value}", level=LogLevel.INFO)
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        input = frame.get_by_text(label_name, exact=True)
        self._log_verbose(message="Clicking and filling input")
        input.click()
        if sys.platform == "darwin":
            input.press("Meta+A")
        else:
            input.press("Control+A")
        
        input.press("Delete")
        input.type(value)
        input.press("Enter")
        self._log_verbose(message=f"Filled value for {label_name}")
    ### ***********************************************************
    @_exception_helper
    def _fill_comments(self, value):
        if not value or len(value.strip()) == 0:
            return

        self._log(message=f"Filling comments: {value}", level=LogLevel.INFO)
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        input = frame.get_by_text("Valuta", exact=True)
        self._log_verbose(message="Clicking and filling input")
        input.click()
        input.press("Tab")
        input.type(value)
        input.press("Enter")
        self._log_verbose(message="Filled comments")
    ### ***********************************************************
    @_exception_helper
    def _fill_attachment(self):
        if self.invoice_data.BilagsFilePath is None or len(str(self.invoice_data.BilagsFilePath)) == 0:
            self._log_verbose(message="No attachment file path provided, skipping attachment step")
            return
        self._log(message="Filling attachment", level=LogLevel.INFO)
        """Handle file attachment in popup window"""
        # Click the attachment button
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        attachment_button = frame.locator('div[title="Vedhæft et nyt dokument"]')
        self._log_verbose(message="Clicking attachment button")
        attachment_button.click()
        
        # Wait longer for popup to appear and check for new windows/popups
        self._log_verbose(message="Waiting for attachment popup")
        self._page.wait_for_timeout(3000)  # Wait 3 seconds for popup
        
        # Check all iframes for file input (SAP uses direct file input, not "Choose File" button)
        # Try each iframe selector
        # verbose logging of frames
        self.verbose_log_frames()
                
        attachment_file=False
        for iframe_selector in IFRAME_SELECTORS:
            try:
                self._log(message=f"Trying iframe selector: {iframe_selector}")
                iframe = self._page.frame_locator(iframe_selector)
                # Look for file input directly (SAP doesn't use "Choose File" button)
                file_input = iframe.locator('input[type="file"]').first
                if file_input.is_visible():
                    # Click the file input first to trigger file dialog
                    self._log_verbose(message=f"Clicking file input to trigger file dialog...")
                    with self._page.expect_file_chooser() as fc_info:
                        file_input.click()
                        file_chooser = fc_info.value
                        file_chooser.set_files(self.invoice_data.BilagsFilePath)
                    attachment_file=True
                    self._log(message="File attached successfully", level=LogLevel.INFO)
                    break
            except Exception as e:
                self._log(message=f"Error with iframe {iframe_selector}: {e}", level=LogLevel.ERROR)
                continue
            
        # Wait a moment for the file to be processed
        self._log_verbose(message="Waiting for file to be processed")
        self._page.wait_for_timeout(4000)
        ok_button = iframe.locator("div.lsButton:has(span:has-text('OK'))")
        ok_button.press("Enter")                        
        self._log_verbose(message="Attachment process completed")
    ### ***********************************************************
    @_exception_helper
    def _fill_csv(self):
        """Handle file attachment in popup window"""
        self._log(message="Filling CSV attachment", level=LogLevel.INFO)   
        # Click the attachment button
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        attachment_button = frame.locator('div[title="Importer konteringslinjer fra EXCEL"]')
        attachment_button.click()
        self._log_verbose(message="Clicked CSV import button")
        # Wait longer for popup to appear and check for new windows/popups
        self._log_verbose(message="Waiting for CSV import popup")
        self._page.wait_for_timeout(2000)  # Wait 3 seconds for popup
        # verbose logging of frames
        self.verbose_log_frames()

        attachment_file=False
        for iframe_selector in IFRAME_SELECTORS:
            try:
                self._log(message=f"Trying iframe selector: {iframe_selector}")
                # Try each iframe selector
                iframe = self._page.frame_locator(iframe_selector)
            
                # Look for file input directly (SAP doesn't use "Choose File" button)
                file_input = iframe.locator('input[type="file"]').first
                if file_input.is_visible():
                    # Click the file input first to trigger file dialog
                    self._log_verbose(message=f"Clicking file input to trigger file dialog...")
                    with self._page.expect_file_chooser() as fc_info:
                        file_input.click()
                        file_chooser = fc_info.value
                        file_chooser.set_files(self.invoice_data.csv_filename)
                    
                    attachment_file=True
                    self._log(message="CSV file attached successfully", level=LogLevel.INFO)
                    break
            except Exception as e:
                    self._log(message=f"Error with iframe {iframe_selector}: {e}", level=LogLevel.ERROR)
                    continue
        
        # Wait a moment for the file to be processed
        self._log_verbose(message="Waiting for CSV file to be processed")
        self._page.wait_for_timeout(2000)
        ok_button = iframe.locator("div.lsButton:has(span:has-text('OK'))")
        ok_button.press("Enter")                        
        self._log_verbose(message="CSV attachment process completed")
    ### ***********************************************************
    @_exception_helper
    def _get_status_text(self, frame)->str:
        self._log(message="Getting status text after invoice check", level=LogLevel.INFO)
        status_text= 'Not controlled'
        message_area = frame.locator("table.lsHTMLContainer.lsScrollContainer--positionscrolling")
        messages = message_area.locator("span.lsTextView").all_text_contents()
        if len(messages) > 0:
            status_text = messages[0]
            
        self._log(message=f"Status text retrieved: {status_text}")
        return status_text
    ### ***********************************************************
    @_exception_helper
    def _check_invoice(self)->bool:
        self._log(message="Checking invoice", level=LogLevel.INFO)
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        control_button = frame.locator('div[title*="Kontroller bilag"]')
        self._log_verbose(message="Clicking control button")
        control_button.click()
        self._log_verbose(message="Waiting for control to complete")
        self._page.wait_for_timeout(2000)
        status_text = self._get_status_text(frame)
        return  status_text
    ### ***********************************************************

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
    
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    d = date.today()
    
    opus = OpusConfig(municipality_code=370, username=opus_username, password=opus_userpassword)
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
        invoice = nkInvoice(opus_data=opus, invoice_data=invoice_data)
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



