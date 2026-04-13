import re
import csv
import sys
from pathlib import Path
from playwright.sync_api import Playwright, sync_playwright, expect
from playwright.sync_api import Browser, BrowserContext, Page
# from setup.Constants import Constants
from pydantic import BaseModel, Field, ValidationError, computed_field, ConfigDict, PrivateAttr, field_validator, model_validator, constr, FilePath, ValidationInfo, confloat
from typing import Optional, Union
from Invoice.src._helpers import _exception_helper
import logging
from enum import Enum, auto
import time
import asyncio
from playwright.async_api import async_playwright
from time import sleep
import locale

#### ********************************************************************************************************************

OPUS_CSV_HEADERS = ["Artskonto", "Omkostningssted", "PSP-element", "Profitcenter", "Ordre", "Debet/kredit", "Beløb", "Næste agent", "Tekst", "Betalingsart", "Påligningsår", "Betalingsmodtagernr.", "Betalingsmodtagernr.kode", "Ydelsesmodtagernr.", "Ydelsesmodtagernr.kode", "Ydelsesperiode fra", "Ydelsesperiode til", "Oplysningspligtnr.", "Oplysningspligtmodtagernr.kode", "Oplysningspligtkode", "Netværk", "Operation", "Mængde", "Mængdeenhed", "Referencenøgle"] 
IFRAME_SELECTORS = [
                'iframe[name*="URLSPW-0"]',
                'iframe[name*="URLSPW"]',
                'iframe[name*="SPW"]',
                'iframe[name*="URL"]',
                'iframe[name*="popup"]',
                'iframe[name*="dialog"]',
                'iframe[name*="modal"]'
            ]
#### ********************************************************************************************************************
#### ********************************************************************************************************************
class LogLevel(Enum):
    INFO = "INFO"#auto()
    ERROR = "ERROR"#auto()
    WARNING = "WARNING"#auto()
    DEBUG = "DEBUG"#auto()
#### ********************************************************************************************************************
#### ********************************************************************************************************************
####     
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

class eOpusCostType(Enum):
    DEBET = "DEBET"#auto()
    KREDIT = "KREDIT"#auto()
class OpusCostData(BaseModel):
    """ Class for handling Opus configuration. """
    # Attributes
    Artskonto: int = Field(gt=9999999, lt=100000000)
    PSP_element:str|None = ""
    SIO_element:str|None = ""
    Kost: float#confloat(gt=0.0)
    PosteringsTekst:str
    Type: eOpusCostType

#### ********************************************************************************************************************
#### ********************************************************************************************************************
####
class InvoiceData(BaseModel):
    Tekst: str
    Reference: str|None = ""
    Bogføringsdato: str|None = ""
    Kommentar: str|None = ""
    BilagsFilePath: Union[FilePath, str] = ""
    csv_filename: Path
    opus_cost_data: list[OpusCostData]
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

    @field_validator("BilagsFilePath")
    def allow_empty_or_valid_path(cls, v):
        if v == "":
            return v
        return FilePath(v) 
    
    # --- Cross-field validator ---
    @model_validator(mode="after")
    def validate_psp_pair(self):
        debet = 0
        kredit = 0
        debet_psp = ""
        kredit_psp = ""
        for cost_data in self.opus_cost_data:
            if cost_data.Type == eOpusCostType.DEBET:
                debet_psp = cost_data.PSP_element.strip()
                debet += cost_data.Kost
            else:
                kredit_psp = cost_data.PSP_element.strip()
                kredit += cost_data.Kost

        if (debet == 0 or kredit == 0 or (debet != kredit)):
            raise ValueError("Debet and Kredit Kost must be equal")    
        
        if (len(debet_psp) == 0 and len(kredit_psp) == 0) or (len(debet_psp) > 0 and len(kredit_psp) > 0):
            return self
        
        raise ValueError("Debet and Kredit PSP must either both be empty or both filled")

        
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
    
    create_invoice_allowed:bool = False
    take_screenshot: bool = False
    screen_shot_fileprefix: str = ""
    _headless: bool = False
    _verbose: bool = False    
    _logger: logging.Logger = None
    _delete_files: bool = True
    ### ------------------------------------------------------------------------------------------------------
    ### Methods
    ### ------------------------------------------------------------------------------------------------------
    ### PUBLIC METHODS
    async def create_invoice(self, create_invoice_allowed:bool = False, max_retries: int = 3, try_number: int = 1) -> dict:
        
        """Create an invoice in the Opus system using Playwright.
            runs the full process of creating an invoice in Opus using the provided invoice data.
            retries try_number <= max_retries times in case of transient errors.
        Args:
            max_retries (int): Number of retries for transient errors. Default is 3.
            try_number (int): Current attempt number. Default is 1.
        Returns:
            dict: Result of the invoice creation process.
        Raises:
            ValueError: If there are validation errors in the input data.
            """  
        self.create_invoice_allowed=create_invoice_allowed
        await self._create_csv()
        
        for run in range(try_number, max_retries):
            try:
                self._log(message=f"Try invoice creation, attempt {try_number} of {max_retries} - FAILED", level=LogLevel.WARNING)
                self._log(message="Start creation of invoice -> _create_invoice()", level=LogLevel.INFO)
                return await self._create_invoice()
            except Exception as e:
                self._log(message=f"Try invoice creation exception: {e}", level=LogLevel.WARNING)
                # closing browser
                try:
                    sleep(1)
                    self._context.close()
                    self._browser.close()
                    sleep(1)
                except:
                    pass
                
                
        return await self._create_invoice()
        
    ### ------------------------------------------------------------------------------------------------------
    ### PRIVATE METHODS
    async def _create_invoice(self) -> dict:
        """Create an invoice in the Opus system using Playwright.
            runs the full process of creating an invoice in Opus using the provided invoice data.
            retries try_number <= max_retries times in case of transient errors.
        Args:
            
        Returns:
            dict: Result of the invoice creation process.
        Raises:
            ValueError: If there are validation errors in the input data.
            """  
        self._log(message="** >> Start creation of invoice", level=LogLevel.INFO)
        async with async_playwright() as playwright:
            # await self._create_csv()
            await self._start_opus_rollebaseret(playwright)
            await self._fill_opus_page()
            self._log(message="End creation of invoice", level=LogLevel.INFO)
            self._context.close()
            self._browser.close()
            return self._result
        
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
    ### Invoice creation steps
    @_exception_helper
    async def _fill_opus_page(self):
        # Fill the OPUS page with invoice data
        self._log(message="Start filling data in OPUS page", level=LogLevel.INFO)
        Invoice_status = "Fejlet"
        status_text = "Ikke afviklet"
        text = "Ikke afviklet"
        # Wait for page to load
        self._log_verbose(message="Waiting for OPUS page to load")
        await self._page.wait_for_load_state('networkidle')
        # bogføringsdato
        await self._fill_value(label_name="Bogføringsdato", value=self.invoice_data.Bogføringsdato)
        # Tekst
        await self._fill_value(label_name="Tekst", value=self.invoice_data.Tekst)
        # Reference
        await self._fill_value(label_name="Reference", value=self.invoice_data.Reference)
        # Kommentarer     
        await self._fill_comments(value=self.invoice_data.Kommentar)
        # Vedhæft bilag
        await self._fill_attachment()
        # Indsæt csv posteringer
        await self._fill_csv()
        # Kontroller bilag
        status_text = await self._check_invoice()
        self._log_verbose(message=f"Status text after checking invoice: {status_text}")
        if status_text == 'Omposteringsbilaget er kontrolleret og OK':
            if self.create_invoice_allowed:
                status_text = await self.create_actual_invoice()
                await self._takescreenshoot(take_screenshot=self.take_screenshot)
                text = "Bilag oprettet"
            else:
                text = "Bilag ikke oprettet"
                await self._takescreenshoot(take_screenshot=self.take_screenshot)
            Invoice_status = "Succes"
        else:
            Invoice_status = "Fejlet"
            text = "Bilag ikke oprettet"
        # Opret bilag
        self._result = {"status": Invoice_status, "message": text, "bilag": status_text}
        self._log_verbose(message=f"End filling data in OPUS page with result: {self._result}")
        
    ### ***********************************************************
    ### ***********************************************************
    async def _delete_files(self):
        try:
            if self._delete_files:
                if self.invoice_data.csv_filename.exists():
                    self.invoice_data.csv_filename.unlink()
                    self._log_verbose(message=f"Deleted temporary CSV file: {self.invoice_data.csv_filename}")
                if self.invoice_data.BilagsFilePath and Path(self.invoice_data.BilagsFilePath).exists():
                    Path(self.invoice_data.BilagsFilePath).unlink()
                    self._log_verbose(message=f"Deleted temporary attachment file: {self.invoice_data.BilagsFilePath}")
        except Exception as e:
            self._log(message=f"Error deleting temporary files: {e}", level=LogLevel.ERROR)

    async def _takescreenshoot(self, take_screenshot: bool = True):
        ## Take screenshot if enabled
        try:
            if take_screenshot:
                self._delete_files = False
                timestamp = time.strftime("%Y%m%d-%H%M%S") 
                if self.screen_shot_fileprefix and len(self.screen_shot_fileprefix.strip()) > 0:
                    prefix = self.screen_shot_fileprefix.strip()
                else:
                    prefix = "opus_screenshot"
                    
                screenshot_path = f"{prefix}_{timestamp}.png"
                await self._page.screenshot(path=screenshot_path)
                self._log(message=f"Screenshot taken: {screenshot_path}", level=LogLevel.INFO)
        except Exception as e:
            self._log(message=f"Failed to take screenshot: {e}", level=LogLevel.WARNING)
    
    async def check_login_error(self):
        # Wait until the form is visible (ensures DOM is loaded)
        try:
            self._log_verbose(message="Checking for login error messages")
            await self._page.wait_for_selector("#loginForm", timeout=2000)

            # Check if error element exists and is visible
            error_locator = await self._page.locator("#errorText")

            if error_locator.is_visible():
                error_message = await error_locator.inner_text()
                self._log_verbose(message=f"Login error message found: {error_message}")
                return error_message
            else:
                return None            
        except:
            self._log_verbose(message="No login error message found")
            return None
    ### ***********************************************************
    ### ***********************************************************
    @_exception_helper
    async def _start_opus_rollebaseret(self, playwright)-> tuple[Browser, BrowserContext, Page]:
        self._log(message=f"*********** Starting Opus rollebaseret ***********", level=LogLevel.INFO)
        self._browser = await playwright.chromium.launch(headless=self._headless)
        self._context = await self._browser.new_context()
        self._page = await self._context.new_page()
        url = self.opus_data.valid_url()
        await self._page.goto(url)
        await self._page.get_by_role("textbox", name="User Account").fill(self.opus_data.username)
        self._log_verbose(message=f"Filled username: {self.opus_data.username}")
        await self._page.get_by_role("textbox", name="Password").fill(self.opus_data.password)
        self._log_verbose(message=f"Filled password: {self.opus_data.password}")
        await self._page.get_by_role("textbox", name="Password").press("Enter")
        self._log_verbose(message="Pressed Enter after filling password")

        error_message = await self.check_login_error()
        if error_message:
            self._log(message=f"Login failed: {error_message}", level=LogLevel.ERROR)
            raise RuntimeError(f"Login failed: {error_message}")
        
        await self._page.locator("#externalCol").get_by_role("button").click()
        await self._page.get_by_text("Bilagsbehandling").click()
        await self._page.get_by_text("Opret omposteringsbilag").click()
    ### ***********************************************************
    ### ***********************************************************
    @_exception_helper
    async def _create_csv(self):
        """Create a CSV file for Opus import based on invoice data."""
        #40000000;;#PSP#;;#SIO#;Debet;#PRICE#;;#TXT#;;;;;;;;;;;;;;;;
        #40000000;;#PSP#;;;Kredit;#PRICE#;;#TXT#;;;;;;;;;;;;;;;;

        self._log(message="Creating CSV file for Opus import", level=LogLevel.INFO)
        csv_data = []
        
        for cost_data in self.invoice_data.opus_cost_data:
            self._log_verbose(message=f"arts konto: {cost_data.Artskonto}")
            self._log_verbose(message=f"PSP: {cost_data.PSP_element}")
            self._log_verbose(message=f"SIO: {cost_data.SIO_element}")
            self._log_verbose(message=f"Kost: {cost_data.Kost}")
            self._log_verbose(message=f"posterings tekst: {cost_data.PosteringsTekst}")
            csv_data.append(
                [
                    cost_data.Artskonto,
                    "",
                    cost_data.PSP_element if cost_data.PSP_element else "",
                    "",
                    cost_data.SIO_element if cost_data.SIO_element else "",
                    "Debet" if cost_data.Type == eOpusCostType.DEBET else "Kredit",
                    f"{cost_data.Kost:.1f}".replace(".", ","),
                        "",
                    cost_data.PosteringsTekst if cost_data.PosteringsTekst else "",
                    "","","","","","","","","","","","","","",""
                ])

        self._log_verbose(message=f"CSV data to write: {csv_data}")
        self._create_opus_csv(data=csv_data)
    ### ***********************************************************
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
    ### ***********************************************************
    @_exception_helper
    async def _fill_value(self, label_name, value):
        if not value or len(value.strip()) == 0:
            return
        self._log(message=f"Filling value for {label_name}: {value}", level=LogLevel.INFO)
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        input = frame.get_by_text(label_name, exact=True)
        self._log_verbose(message="Clicking and filling input")
        await input.click()
        if sys.platform == "darwin":
            await input.press("Meta+A")
        else:
            await input.press("Control+A")
        
        await input.press("Delete")
        await input.type(value)
        await input.press("Enter")
        self._log_verbose(message=f"Filled value for {label_name}")
    ### ***********************************************************
    ### ***********************************************************
    @_exception_helper
    async def _fill_comments(self, value):
        if not value or len(value.strip()) == 0:
            return

        self._log(message=f"Filling comments: {value}", level=LogLevel.INFO)
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        input = frame.get_by_text("Valuta", exact=True)
        self._log_verbose(message="Clicking and filling input")
        await input.click()
        await input.press("Tab")
        await input.type(value)
        await input.press("Enter")
        self._log_verbose(message="Filled comments")
    ### ***********************************************************
    ### ***********************************************************
    @_exception_helper
    async def _upload_file(self, locator:str, file_path: str):
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File to upload not found: {file_path}")
        
        self._log(message=f"Uploading file:{file_path}", level=LogLevel.INFO)
        """Handle file attachment in popup window"""
        # Click the attachment button
        self._log_verbose(message=f"Uploading file using locator: {locator}")
        
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        attachment_button = frame.locator(locator)
        self._log_verbose(message="Clicking attachment button")
        await attachment_button.click()
        
        # Wait longer for popup to appear and check for new windows/popups
        self._log_verbose(message="Waiting for attachment popup")
        await self._page.wait_for_timeout(3000)  # Wait 3 seconds for popup
        
        # Check all iframes for file input (SAP uses direct file input, not "Choose File" button)
        # Try each iframe selector
        # verbose logging of frames
        self.verbose_log_frames()
                
        attachment_file=False
        # Try multiple times to find the correct iframe and attach the file
        for iframe_selector in IFRAME_SELECTORS:
            try:
                self._log(message=f"Trying iframe selector: {iframe_selector}")
                iframe = self._page.frame_locator(iframe_selector)
                # Look for file input directly (SAP doesn't use "Choose File" button)
                file_input = iframe.locator('input[type="file"]').first
                if file_input.is_visible():
                    # Click the file input first to trigger file dialog
                    self._log_verbose(message=f"Clicking file input to trigger file dialog...")
                    async with self._page.expect_file_chooser() as fc_info:
                        await file_input.click()
                        file_chooser = await fc_info.value
                        await file_chooser.set_files(file_path)
                    attachment_file=True
                    self._log(message="File attached successfully", level=LogLevel.INFO)
                    break
            except Exception as e:
                print(e)
                self._log(message=f"Error with iframe {iframe_selector}: {e}", level=LogLevel.ERROR)
                continue
            
        # Wait a moment for the file to be processed
        if not attachment_file:
            raise RuntimeError("Failed to attach file: No suitable iframe or file input found")
        
        self._log_verbose(message=f'Attachment file set: {attachment_file}')
        self._log_verbose(message="Waiting for file to be processed")
        self._page.wait_for_timeout(4000)
        ok_button = iframe.locator("div.lsButton:has(span:has-text('OK'))")
        await ok_button.press("Enter")                        
        self._log_verbose(message="Attachment process completed")
    ### ***********************************************************
    ### ***********************************************************
    @_exception_helper
    async def _fill_attachment(self):
        self._log_verbose(message="Attachment process started")
        if self.invoice_data.BilagsFilePath is None or len(str(self.invoice_data.BilagsFilePath)) == 0:
            self._log_verbose(message="No attachment file path provided, skipping attachment step")
            return
        await self._upload_file(locator='div[title="Vedhæft et nyt dokument"]', file_path=str(self.invoice_data.BilagsFilePath))
        self._log_verbose(message="Attachment process completed")
    ### ***********************************************************
    ### ***********************************************************
    @_exception_helper
    async def _fill_csv(self):
        """Handle file attachment in popup window"""
        self._log_verbose(message="CSV attachment process started")
        await self._upload_file(locator='div[title="Importer konteringslinjer fra EXCEL"]', file_path=str(self.invoice_data.csv_filename))
        self._log_verbose(message="CSV attachment process completed")
    ### ***********************************************************
    ### ***********************************************************
    @_exception_helper
    async def _get_status_text(self, frame)->str:
        self._log(message="Getting status text after invoice check", level=LogLevel.INFO)
        status_text= 'Not controlled'
        message_area = frame.locator("table.lsHTMLContainer.lsScrollContainer--positionscrolling")
        messages = await message_area.locator("span.lsTextView").all_text_contents()
        if len(messages) > 0:
            status_text = messages[0]
            
        self._log(message=f"Status text retrieved: {status_text}")
        return status_text
    ### ***********************************************************
    ### ***********************************************************
    @_exception_helper
    async def _check_invoice(self)->str:
        self._log(message="Checking invoice", level=LogLevel.INFO)
        frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
        control_button = frame.locator('div[title*="Kontroller bilag"]')
        self._log_verbose(message="Clicking control button")
        await control_button.click()
        self._log_verbose(message="Waiting for control to complete")
        await self._page.wait_for_timeout(2000)
        status_text = await self._get_status_text(frame)
        return  status_text
    ### ***********************************************************
    ### ***********************************************************
    @_exception_helper
    async def create_actual_invoice(self):
        if self.create_invoice_allowed:
            self._log(message="Creating invoice", level=LogLevel.INFO)
            frame = self._page.frame_locator("#contentAreaFrame").frame_locator("#isolatedWorkArea")
            control_button = frame.locator('div[title*="Opret ompostering"]')
            self._log_verbose(message="Clicking create button")
            await control_button.click()
            self._log_verbose(message="Waiting for creation to complete")
            await self._page.wait_for_timeout(2000)
            status_text = "no_invoice"
            
            try:
                status_text = await self._get_status_text(frame)
            except Exception:
                await self._page.wait_for_timeout(2000)
                status_text = None
                
            if status_text is None:
                status_text = await self._get_status_text(frame)

            return status_text
        else:
            return "Not allowed!"
        
        

