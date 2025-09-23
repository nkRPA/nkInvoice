import unittest
from Invoice.src.nkInvoice import nkInvoice, OpusConfig
from pydantic import ValidationError

class TestInvoice(unittest.TestCase):
    def setUp(self):
        # Setup code: create resources needed for tests
        self.correct_invoice_data = {
            "Debet":"XG-0000000204-00001",
            "Kredit":"XG-0000002473-00029",
            "Tekst":"Test af tekst",
            "Reference":"test af reference",
            "Bogføringsdato":"12.09.2025",
            "Kommentar":"test af comment",
            "Artskonto":"40000000",
            "PosteringsTekst":"Test af posterings tekst",
            "Kost":4444.22,
            "BilagsFilePath":"/Users/lakas/git/playwright_test/file_path.txt",
            "csv_filename":"/Users/lakas/git/playwright_test/opus.csv"
        }
        
        self.error_missing_kost_invoice_data = {
            "Debet":"XG-0000000204-00001",
            "Kredit":"XG-0000002473-00029",
            "Tekst":"Test af tekst",
            "Reference":"test af reference",
            "Bogføringsdato":"12.09.2025",
            "Kommentar":"test af comment",
            "Artskonto":"40000000",
            "PosteringsTekst":"Test af posterings tekst",
            "BilagsFilePath":"/Users/lakas/git/playwright_test/file_path.txt",
            "csv_filename":"/Users/lakas/git/playwright_test/opus.csv"
        }
        self.error_missing_debet_invoice_data = {
            "Kredit":"XG-0000002473-00029",
            "Tekst":"Test af tekst",
            "Reference":"test af reference",
            "Bogføringsdato":"12.09.2025",
            "Kommentar":"test af comment",
            "Artskonto":"40000000",
            "PosteringsTekst":"Test af posterings tekst",
            "Kost":4444.22,
            "BilagsFilePath":"/Users/lakas/git/playwright_test/file_path.txt",
            "csv_filename":"/Users/lakas/git/playwright_test/opus.csv"
        }
        self.error_missing_kredit_invoice_data = {
            "Debet":"XG-0000000204-00001",
            "Tekst":"Test af tekst",
            "Reference":"test af reference",
            "Bogføringsdato":"12.09.2025",
            "Kommentar":"test af comment",
            "Artskonto":"40000000",
            "PosteringsTekst":"Test af posterings tekst",
            "Kost":4444.22,
            "BilagsFilePath":"/Users/lakas/git/playwright_test/file_path.txt",
            "csv_filename":"/Users/lakas/git/playwright_test/opus.csv"
        }

    def tearDown(self):
        # Teardown code: clean up resources
        # Example: del self.invoice
        pass

    def test_invoice_creation_opus_data(self):

        # test missing password
        try:
            opus = OpusConfig(municipality_code=370, username="username")
        except Exception as e:
            self.assertTrue("password" in str(e).lower() and "missing" in str(e).lower())
        # test missing username
        try:
            opus = OpusConfig(municipality_code=370, password="passseord")
        except Exception as e:
            self.assertTrue("username" in str(e).lower() and "missing" in str(e).lower())
        # test missing municipality_code
        try:
            opus = OpusConfig(username="bruger", password="pasord")
        except Exception as e:
            self.assertTrue("municipality_code" in str(e).lower() and "missing" in str(e).lower())  


    def test_invoice_creation_invoice_data(self):
        opus = OpusConfig(municipality_code=370, username="bruger", password="kode1234")

        try:
            invoice = nkInvoice(opus_data=opus, invoice_data=self.error_missing_debet_invoice_data)
        except Exception as e:
            self.assertTrue("debet" in str(e).lower() and "missing" in str(e).lower())  

        try:
            invoice = nkInvoice(opus_data=opus, invoice_data=self.error_missing_kredit_invoice_data)
        except Exception as e:
            self.assertTrue("kredit" in str(e).lower() and "missing" in str(e).lower())  

        try:
            invoice = nkInvoice(opus_data=opus, invoice_data=self.error_missing_kost_invoice_data)
        except Exception as e:
            self.assertTrue("kost" in str(e).lower() and "missing" in str(e).lower())  


    def test_invoice_creation(self):
        opus = OpusConfig(municipality_code=370, username="bruger", password="kode1234")

        try:
            invoice = nkInvoice(opus_data=opus, invoice_data=self.correct_invoice_data)
            invoice.create_invoice()
        except Exception as e:
            #Error: Error in function '_start_opus_rollebaseret': Login failed: Enter your user ID in the format "domain\user" or "user@domain".
            self.assertTrue("_start_opus_rollebaseret" in str(e).lower() and "login failed" in str(e).lower())  




if __name__ == '__main__':
    unittest.main()