import re
import csv
import sys
from playwright.sync_api import Playwright, sync_playwright, expect
from playwright.sync_api import Browser, BrowserContext, Page
from setup.Constants import Constants

class nkInvoice:
    def __init__(self, page: Page, constants) -> None:
        