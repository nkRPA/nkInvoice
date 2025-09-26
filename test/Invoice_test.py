import unittest
from Invoice.src.nkInvoice import nkInvoice, OpusConfig
from pydantic import ValidationError
import os
from dotenv import load_dotenv
from datetime import date

class TestInvoice(unittest.TestCase):
    def setUp(self):
        # Setup code: create resources needed for tests
        self.invoice_data = {
            "Debet_PSP":"XG-0000000204-00001",
            "Kredit_PSP":"XG-0000002473-00029",
            "Tekst":"Test af tekst",
            "Reference":"test af reference",
            "Bogføringsdato":"12.09.2025",
            "Kommentar":"test af comment",
            "Debet_Artskonto":"40000000",
            "Kredit_Artskonto":"40000000",
            "Debet_PosteringsTekst":"Test af posterings tekst",
            "Kredit_PosteringsTekst":"Test af posterings tekst",
            "Kost":1.0,
            "BilagsFilePath":"/Users/lakas/tmp/file_path.txt",
            "csv_filename":"/Users/lakas/tmp/opus.csv"
        }


        load_dotenv()
        self.opus_username = os.getenv('OPUS_USER')
        self.opus_userpassword = os.getenv('OPUS_USER_PASSWORD')
        self.opus_url = os.getenv('OPUS_URL')
        self.opus_municipality_code = int(os.getenv('OPUS_MUNICIPALITY_CODE'))

    def tearDown(self):
        # Teardown code: clean up resources
        # Example: del self.invoice
        pass
    def _testdata(self, key, value, new_data=None):
        if new_data:
            data = new_data
        else:
            data = self.invoice_data.copy()
        data[key] = value
        opus = OpusConfig(url=self.opus_url, municipality_code=self.opus_municipality_code, username="bruger", password="kode1234")
        invoice = nkInvoice(opus_data=opus, invoice_data=data)
    ########################################################################################################################
    ### Tests        
    ########################################################################################################################
    # *************************************************************************************************************
    def test_invoice_creation_opus_data(self):

        # test missing password
        try:
            opus = OpusConfig(url=self.opus_url, municipality_code=self.opus_municipality_code, username="username")
        except Exception as e:
            self.assertTrue("password" in str(e).lower() and "missing" in str(e).lower())
        # test missing username
        try:
            opus = OpusConfig(url=self.opus_url, municipality_code=self.opus_municipality_code, password="passseord")
        except Exception as e:
            self.assertTrue("username" in str(e).lower() and "missing" in str(e).lower())
        # test missing municipality_code
        try:
            opus = OpusConfig(url=self.opus_url, username="bruger", password="pasord")
        except Exception as e:
            self.assertTrue("municipality_code" in str(e).lower() and "missing" in str(e).lower())  
    # *************************************************************************************************************
    def test_invoice_Debet_PSP_data(self):
        # Normal cases
        try:
            self._testdata("Debet_PSP", "XG-0000000204-00001")
        except Exception as e:
            self.assertTrue(False)
        # Edge cases - both empty or both filled    
        try:
            self._testdata("Debet_PSP", "")
        except Exception as e:
            self.assertTrue("Value error, Debet_PSP and Kredit_PSP must either both be empty or both filled".lower() in str(e).lower())  
    # *************************************************************************************************************
    def test_invoice_Kredit_PSP_data(self):
        # Normal cases
        try:
            self._testdata("Kredit_PSP", "XG-0000000204-00001")
        except Exception as e:
            self.assertTrue(False)
        # Edge cases - both empty or both filled
        try:
            self._testdata("Kredit_PSP", "")
        except Exception as e:
            self.assertTrue("Value error, Debet_PSP and Kredit_PSP must either both be empty or both filled".lower() in str(e).lower())  
    # *************************************************************************************************************
    def test_invoice_Tekst_data(self):
        try:
            self._testdata("Tekst", "Some tekst")
        except Exception as e:
            self.assertTrue(False)
        try:
            self._testdata("Tekst", "")
        except Exception as e:
            self.assertTrue("Value error, Tekst must not be empty".lower() in str(e).lower())  
    # *************************************************************************************************************
    def test_invoice_Reference_data(self):
        try:
            self._testdata("Reference", "Some tekst")
            self._testdata("Reference", "")
        except Exception as e:
            self.assertTrue(False)
    # *************************************************************************************************************
    def test_invoice_Bookingdate_data(self):
        try:
            self._testdata("Bogføringsdato", "12.09.2025")
            self._testdata("Bogføringsdato", "")
        except Exception as e:
            self.assertTrue(False)
        # Edge cases - wrong format
        try:
            self._testdata("Bogføringsdato", "2025.09.12")
        except Exception as e:
            self.assertTrue("Value error, Bogføringsdato must be in format dd.mm.yyyy (e.g. 12.09.2025)".lower() in str(e).lower())  
    # *************************************************************************************************************
    def test_invoice_Kommentar_data(self):
        try:
            self._testdata("Kommentar", "Some tekst")
            self._testdata("Kommentar", "")
        except Exception as e:
            self.assertTrue(False)
    # *************************************************************************************************************
    def test_invoice_Debet_Artskonto_data(self):
        try:
            self._testdata("Debet_Artskonto", 40000000)
        except Exception as e:
            self.assertTrue(False)
        # Edge cases - wrong format
        
        try:
            self._testdata("Debet_Artskonto", "")
        except Exception as e:
            self.assertTrue("Input should be a valid integer, unable to parse string as an integer".lower() in str(e).lower())  
        
        try:
            self._testdata("Debet_Artskonto", 4000)
        except Exception as e:
            self.assertTrue("Input should be greater than 9999999".lower() in str(e).lower())  
    # *************************************************************************************************************
    def test_invoice_Kredit_Artskonto_data(self):
        try:
            self._testdata("Kredit_Artskonto", 40000000)
        except Exception as e:
            self.assertTrue(False)
        # Edge cases - wrong format
        
        try:
            self._testdata("Kredit_Artskonto", "")
        except Exception as e:
            self.assertTrue("Input should be a valid integer, unable to parse string as an integer".lower() in str(e).lower())  
        
        try:
            self._testdata("Kredit_Artskonto", 4000)
        except Exception as e:
            self.assertTrue("Input should be greater than 9999999".lower() in str(e).lower())  
    # *************************************************************************************************************
    def test_invoice_Debet_PosteringsTekst_data(self):
            try:
                self._testdata("Debet_PosteringsTekst", "Some tekst")
                self._testdata("Debet_PosteringsTekst", "")
            except Exception as e:
                self.assertTrue(False)
    # *************************************************************************************************************
    def test_invoice_Kredit_PosteringsTekst_data(self):
            try:
                self._testdata("Kredit_PosteringsTekst", "Some tekst")
                self._testdata("Kredit_PosteringsTekst", "")
            except Exception as e:
                self.assertTrue(False)
    # *************************************************************************************************************
    def test_invoice_Kost_data(self):
            try:
                self._testdata("Kost", 10.0)
                self._testdata("Kost", 20.0)
                self._testdata("Kost", "10")
            except Exception as e:
                self.assertTrue(False)

            # error cases
            try:
                self._testdata("Kost", "")
            except Exception as e:
                self.assertTrue("Input should be a valid number, unable to parse string as a number".lower() in str(e).lower())  

            try:
                self._testdata("Kost", 0.0)
            except Exception as e:
                self.assertTrue("Input should be greater than 0 ".lower() in str(e).lower())  
    # *************************************************************************************************************
    def test_invoice_creation_login(self):
        try:
            opus = OpusConfig(url=self.opus_url, municipality_code=self.opus_municipality_code, username="bruger", password="kode1234")
            invoice = nkInvoice(opus_data=opus, invoice_data=self.invoice_data)
            invoice.create_invoice()
        except Exception as e:
            print(e)
            #Error: Error in function '_start_opus_rollebaseret': Login failed: Enter your user ID in the format "domain\user" or "user@domain".
            self.assertTrue("_start_opus_rollebaseret" in str(e).lower() and "login failed" in str(e).lower())  
        try:
            opus = OpusConfig(url=self.opus_url, municipality_code=self.opus_municipality_code, username=self.opus_username, password="kode1234")
            invoice = nkInvoice(opus_data=opus, invoice_data=self.invoice_data)
            invoice.create_invoice()
        except Exception as e:
            print(e)
            #Error: Error in function '_start_opus_rollebaseret': Login failed: Enter your user ID in the format "domain\user" or "user@domain".
            self.assertTrue("_start_opus_rollebaseret" in str(e).lower() and "login failed" in str(e).lower() and "password" in str(e).lower())  
    # *************************************************************************************************************
    def test_invoice_creation_bilag_files(self):
        try:
            self._testdata("BilagsFilePath", "/users/lakas/tmp/opus.csv")
            self._testdata("BilagsFilePath", "")
        except Exception as e:
            self.assertTrue(False)
        try:
            self._testdata("BilagsFilePath", "LJHGILKHJCUYKJJG")
        except Exception as e:
            self.assertTrue("bilagsfilepath" in str(e).lower() and "path does not point to a file" in str(e).lower())  
    # *************************************************************************************************************
    def test_invoice_creation_csv_file(self):
        # Normal cases
        try:
            self._testdata("csv_filename", "/users/lakas/tmp/opus.csv")
        except Exception as e:
            self.assertTrue(False)
        # Edge cases - wrong format
        try:
            self._testdata("csv_filename", "")
        except Exception as e:
            self.assertTrue("csv_filename" in str(e).lower() and "path does not point to a file" in str(e).lower())  

        try:
            self._testdata("csv_filename", "987098457i23vrfadkjbsvklkweåf+qeyoi")
        except Exception as e:
            self.assertTrue("csv_filename" in str(e).lower() and "path does not point to a file" in str(e).lower())  
    # *************************************************************************************************************
    def test_invoice_creation_all_fields(self):
        d = date.today()
        opus = OpusConfig(url=self.opus_url, municipality_code=self.opus_municipality_code, username=self.opus_username, password=self.opus_userpassword)
        invoice_data = self.invoice_data.copy()
        invoice = nkInvoice(opus_data=opus, invoice_data=invoice_data)
        invoice._headless=False
        result = invoice.create_invoice()
        #{'status': 'Succes', 'message': 'Bilag oprettet', 'Bilag': 'Omposteringsbilaget er kontrolleret og OK'}
        self.assertTrue(result['status'] == "Succes")
        self.assertTrue("bilag oprettet" in result['message'].lower())
        self.assertTrue("bilaget er kontrolleret og ok" in result['bilag'].lower())

        invoice._headless=True
        result = invoice.create_invoice()
        #{'status': 'Succes', 'message': 'Bilag oprettet', 'Bilag': 'Omposteringsbilaget er kontrolleret og OK'}
        self.assertTrue(result['status'] == "Succes")
        self.assertTrue("bilag oprettet" in result['message'].lower())
        self.assertTrue("bilaget er kontrolleret og ok" in result['bilag'].lower())
    # *************************************************************************************************************
    def test_invoice_creation_all_fields_except_bilag(self):
        d = date.today()
        opus = OpusConfig(url=self.opus_url, municipality_code=self.opus_municipality_code, username=self.opus_username, password=self.opus_userpassword)
        invoice_data = self.invoice_data.copy()
        invoice_data["BilagsFilePath"] = ""
        invoice = nkInvoice(opus_data=opus, invoice_data=invoice_data)
        invoice._headless=False
        result = invoice.create_invoice()
        #{'status': 'Succes', 'message': 'Bilag oprettet', 'Bilag': 'Omposteringsbilaget er kontrolleret og OK'}
        self.assertTrue(result['status'] == "Succes")
        self.assertTrue("bilag oprettet" in result['message'].lower())
        self.assertTrue("bilaget er kontrolleret og ok" in result['bilag'].lower())

        invoice._headless=True
        result = invoice.create_invoice()
        #{'status': 'Succes', 'message': 'Bilag oprettet', 'Bilag': 'Omposteringsbilaget er kontrolleret og OK'}
        self.assertTrue(result['status'] == "Succes")
        self.assertTrue("bilag oprettet" in result['message'].lower())
        self.assertTrue("bilaget er kontrolleret og ok" in result['bilag'].lower())
    # *************************************************************************************************************
    def test_invoice_creation_all_fields_except_Reference_Comments(self):
        d = date.today()
        opus = OpusConfig(url=self.opus_url, municipality_code=self.opus_municipality_code, username=self.opus_username, password=self.opus_userpassword)
        invoice_data = self.invoice_data.copy()
        invoice_data["Reference"] = ""
        invoice_data["Kommentar"] = ""
        invoice = nkInvoice(opus_data=opus, invoice_data=invoice_data)
        invoice._headless=False
        result = invoice.create_invoice()
        #{'status': 'Succes', 'message': 'Bilag oprettet', 'Bilag': 'Omposteringsbilaget er kontrolleret og OK'}
        self.assertTrue(result['status'] == "Succes")
        self.assertTrue("bilag oprettet" in result['message'].lower())
        self.assertTrue("bilaget er kontrolleret og ok" in result['bilag'].lower())

        invoice._headless=True
        result = invoice.create_invoice()
        #{'status': 'Succes', 'message': 'Bilag oprettet', 'Bilag': 'Omposteringsbilaget er kontrolleret og OK'}
        self.assertTrue(result['status'] == "Succes")
        self.assertTrue("bilag oprettet" in result['message'].lower())
        self.assertTrue("bilaget er kontrolleret og ok" in result['bilag'].lower())

if __name__ == '__main__':
    unittest.main()