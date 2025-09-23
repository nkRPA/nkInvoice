import re
import csv
import sys
from playwright.sync_api import Playwright, sync_playwright, expect
from playwright.sync_api import Browser, BrowserContext, Page
# from setup.Constants import Constants
from pydantic import BaseModel, Field, ValidationError, computed_field, ConfigDict, PrivateAttr, field_validator
from typing import Optional

from Invoice.src._helpers import _exception_helper

OPUS_CSV_HEADERS = ["Artskonto", "Omkostningssted", "PSP-element", "Profitcenter", "Ordre", "Debet/kredit", "Beløb", "Næste agent", "Tekst", "Betalingsart", "Påligningsår", "Betalingsmodtagernr.", "Betalingsmodtagernr.kode", "Ydelsesmodtagernr.", "Ydelsesmodtagernr.kode", "Ydelsesperiode fra", "Ydelsesperiode til", "Oplysningspligtnr.", "Oplysningspligtmodtagernr.kode", "Oplysningspligtkode", "Netværk", "Operation", "Mængde", "Mængdeenhed", "Referencenøgle"] 
IFRAME_SELECTORS = [
                'iframe[name*="URLSPW"]',
                'iframe[name*="SPW"]',
                'iframe[name*="popup"]',
                'iframe[name*="dialog"]',
                'iframe[name*="modal"]',
                'iframe[name*="content"]',
                'iframe[name*="work"]',
                'iframe:visible'
            ]

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
    invoice_data: dict
    opus_data: OpusConfig
    headless: bool = False
    # Validation
    @field_validator("invoice_data")
    @classmethod
    def validate_invoice_data(cls, v):
        required_fields = [
            "Debet", "Kredit", "Tekst", "Reference", "Bogføringsdato",
            "Kommentar", "Artskonto", "PosteringsTekst", "Kost",
            "BilagsFilePath", "csv_filename"
        ]
        missing_fields = [field for field in required_fields if field not in v]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        return v

    ### ------------------------------------------------------------------------------------------------------
    ### Methods
    ### ------------------------------------------------------------------------------------------------------
    ### PUBLIC METHODS
    def create_invoice(self):
        """Create an invoice in the Opus system using Playwright."""        
        with sync_playwright() as playwright:
            self._create_csv()
            self._start_opus_rollebaseret(playwright)
            self._fill_opus_page()
            self._context.close()
            self._browser.close()
            return self._result
    ### ------------------------------------------------------------------------------------------------------
    ### PRIVATE METHODS
    @_exception_helper
    def _start_opus_rollebaseret(self, playwright)-> tuple[Browser, BrowserContext, Page]:
        self._browser = playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        url = self.opus_data.valid_url()
        self._page.goto(url)
        self._page.get_by_role("textbox", name="User Account").fill(self.opus_data.username)
        self._page.get_by_role("textbox", name="Password").fill(self.opus_data.password)
        self._page.get_by_role("button", name="Sign in").click()
        
        try:
            self._page.wait_for_load_state('networkidle', timeout=10000)
        except:
            pass
        
        error_message = self.check_login_error()
        if error_message:
            raise RuntimeError(f"Login failed: {error_message}")
        
        self._page.locator("#externalCol").get_by_role("button").click()
        self._page.get_by_text("Bilagsbehandling").click()
        self._page.get_by_text("Opret omposteringsbilag").click()
        
    def check_login_error(self):
        # Wait until the form is visible (ensures DOM is loaded)
        try:
            self._page.wait_for_selector("#loginForm")

            # Check if error element exists and is visible
            error_locator = self._page.locator("#errorText")

            if error_locator.is_visible():
                error_message = error_locator.inner_text()
                return error_message
            else:
                return None            
        except:
            return None
    ### ***********************************************************
    @_exception_helper
    def _create_csv(self):
        csv_data = [
            [
                self.invoice_data['Artskonto'],
                "",
                self.invoice_data['Debet'],
                "",
                "",
                "Debet",
                self.invoice_data['Kost'],
                "",
                self.invoice_data['PosteringsTekst'],
                "","","","","","","","","","","","","","",""
            ],
            [
                self.invoice_data['Artskonto'],
                "",
                self.invoice_data['Kredit'],
                "",
                "",
                "Kredit",
                self.invoice_data['Kost'],
                "",
                self.invoice_data['PosteringsTekst'],
                "","","","","","","","","","","","","","",""
            ]
        ]
        self._create_opus_csv(data=csv_data)

    @_exception_helper
    def _create_opus_csv(self, data):
        headers = OPUS_CSV_HEADERS
        
        with open(self.invoice_data['csv_filename'], 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile,delimiter=';')
            writer.writerow(headers)
            writer.writerows(data)
        
        # return f"CSV file '{filename}' created successfully with {len(data)} rows"
    ### ***********************************************************
    @_exception_helper
    def _fill_opus_page(self):
        # Fill the OPUS page with invoice data
        Invoice = False
        status_text = "Not runned"
        text = "Not runned"
        # Wait for page to load
        self._page.wait_for_load_state('networkidle')
        # bogføringsdato
        self._fill_value(label_name="Bogføringsdato", value=self.invoice_data['Bogføringsdato'])
        # Tekst
        self._fill_value(label_name="Tekst", value=self.invoice_data['Tekst'])
        # Reference
        self._fill_value(label_name="Reference", value=self.invoice_data['Reference'])
        # Kommentarer     
        self._fill_comments(value=self.invoice_data['Kommentar'])
        # Vedhæft bilag
        self._fill_attachment()
        # Indsæt csv posteringer
        self._fill_csv()
        # Kontroller bilag
        status_text = self._check_invoice()

        print(f"Status text: {status_text}")
        if status_text == 'Omposteringsbilaget er kontrolleret og OK':
            Invoice = True
            text = "Bilag oprettet"
        else:
            Invoice = False
            text = "Bilag ikke oprettet"
        # Opret bilag
        self._result = {"status": Invoice, "message": text, "Bilag": status_text}
    ### ***********************************************************
    @_exception_helper
    def _fill_value(self, label_name, value):
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        input = frame.get_by_text(label_name, exact=True)
        input.click()
        if sys.platform == "darwin":
            input.press("Meta+A")
        else:
            input.press("Control+A")
        
        input.press("Delete")
        input.type(value)
        input.press("Enter")
    ### ***********************************************************
    @_exception_helper
    def _fill_comments(self, value):
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        input = frame.get_by_text("Valuta", exact=True)
        input.click()
        input.press("Tab")
        input.type(value)
        input.press("Enter")
    ### ***********************************************************
    @_exception_helper
    def _fill_attachment(self):
        """Handle file attachment in popup window"""
        # Click the attachment button
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        attachment_button = frame.locator('div[title="Vedhæft et nyt dokument"]')
        attachment_button.click()
        
        # Wait longer for popup to appear and check for new windows/popups
        self._page.wait_for_timeout(3000)  # Wait 3 seconds for popup
        
        # Check all iframes for file input (SAP uses direct file input, not "Choose File" button)
        # Try each iframe selector
        attachment_file=False
        for iframe_selector in IFRAME_SELECTORS:
            try:
                iframe = self._page.frame_locator(iframe_selector)
                # Look for file input directly (SAP doesn't use "Choose File" button)
                file_input = iframe.locator('input[type="file"]').first
                if file_input.is_visible():
                    # Click the file input first to trigger file dialog
                    print("Clicking file input to trigger file dialog...")
                    with self._page.expect_file_chooser() as fc_info:
                        file_input.click()
                        file_chooser = fc_info.value
                        file_chooser.set_files(self.invoice_data['BilagsFilePath'])
                    attachment_file=True
                    break
            except Exception as e:
                print(f"Iframe {iframe_selector} failed: {e}")
                continue
            
        # Wait a moment for the file to be processed
        self._page.wait_for_timeout(2000)
        ok_button = iframe.locator("div.lsButton:has(span:has-text('OK'))")
        ok_button.press("Enter")                        
    ### ***********************************************************
    @_exception_helper
    def _fill_csv(self):
        """Handle file attachment in popup window"""
       
        # Click the attachment button
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        attachment_button = frame.locator('div[title="Importer konteringslinjer fra EXCEL"]')
        attachment_button.click()
        
        # Wait longer for popup to appear and check for new windows/popups
        self._page.wait_for_timeout(2000)  # Wait 3 seconds for popup
        
        attachment_file=False
        for iframe_selector in IFRAME_SELECTORS:
            try:
                # Try each iframe selector
                iframe = self._page.frame_locator(iframe_selector)
            
                # Look for file input directly (SAP doesn't use "Choose File" button)
                file_input = iframe.locator('input[type="file"]').first
                if file_input.is_visible():
                    # Click the file input first to trigger file dialog
                    print("Clicking file input to trigger file dialog...")
                    with self._page.expect_file_chooser() as fc_info:
                        file_input.click()
                        file_chooser = fc_info.value
                        file_chooser.set_files(self.invoice_data['csv_filename'])
                    
                    attachment_file=True
                    break
            except Exception as e:
                    print(f"Iframe {iframe_selector} failed: {e}")
                    continue
        
        # Wait a moment for the file to be processed
        self._page.wait_for_timeout(2000)
        ok_button = iframe.locator("div.lsButton:has(span:has-text('OK'))")
        ok_button.press("Enter")                        
    ### ***********************************************************
    @_exception_helper
    def _get_status_text(self, frame)->str:
        status_text= 'Not controlled'
        message_area = frame.locator("table.lsHTMLContainer.lsScrollContainer--positionscrolling")
        messages = message_area.locator("span.lsTextView").all_text_contents()
        if len(messages) > 0:
            status_text = messages[0]
        return status_text
    ### ***********************************************************
    @_exception_helper
    def _check_invoice(self)->bool:
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        control_button = frame.locator('div[title*="Kontroller bilag"]')
        control_button.click()
        self._page.wait_for_timeout(2000)
        status_text = self._get_status_text(frame)
        return  status_text
    ### ***********************************************************

if __name__ == '__main__':
    opus = OpusConfig(municipality_code=370, username="samdrift\JX00999998", password="VsDFYQhvgwKxqnerCM7RjfE2LXutbd#*-_aG4kp36JSmTc8HyP")
    invoice_data = {
            "Debet":"XG-0000000204-00001",
            "Kredit":"XG-0000002473-00029",
            "Tekst":"Test af tekst",
            "Reference":"test af reference",
            "Bogføringsdato":"12.09.2025",
            "Kommentar":"test af comment",
            "Artskonto":"40000000",
            "PosteringsTekst":"Test af posterings tekst",
            "Kost":4444.22,
            "BilagsFilePath":"/Users/lakas/tmp/file_path.txt",
            "csv_filename":"/Users/lakas/tmp/opus.csv"
        }
    try:
        invoice = nkInvoice(opus_data=opus, invoice_data=invoice_data, headless=True)
        result = invoice.create_invoice()
        print(result)
    except Exception as e:
        print(f"Error: {e}")





    #@computed_field
    #@property
    # def valid_opus_path(self) -> str:
    #     if not self.opus_path.endswith('/'):
    #         self.opus_path += '/'
    #     self.opus_path += f'?kommune={self.municipality_code}/'
    #     return self.opus_path
