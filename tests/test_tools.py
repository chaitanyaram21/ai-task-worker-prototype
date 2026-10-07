import unittest
import os
import sqlite3
import tools

class TestTools(unittest.TestCase):
    def setUp(self):
        # Use an file DB for tests because :memory: is lost on connection close
        import uuid
        self.test_db_path = f"tests/test_{uuid.uuid4().hex}.db"
        tools.DB_PATH = self.test_db_path
        
        # Initialize schema
        tools.init_db(self.test_db_path)
        
        # Create dummy directories for file tests
        os.makedirs("data/invoices", exist_ok=True)
        with open("data/invoices/test_inv.txt", "w") as f:
            f.write("Invoice Number: TEST-001\nAmount: 100")

    def tearDown(self):
        try:
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
        except:
            pass

    def test_submit_invoice_creates_record(self):
        result = tools.submit_invoice_to_system("INV-123", "Acme", "2026-10-01", 1500.0, "2026-11-01")
        self.assertIn("SUCCESS", result)
        
        # Verify directly in DB
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT amount FROM invoices WHERE invoice_number='INV-123'")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 1500.0)

    def test_verify_invoice_success(self):
        tools.submit_invoice_to_system("INV-456", "Globex", "2026-10-01", 200.0, "2026-11-01")
        result = tools.verify_invoice_in_system("INV-456")
        self.assertIn("VERIFIED", result)
        self.assertIn("Globex", result)

    def test_verify_invoice_failure(self):
        result = tools.verify_invoice_in_system("NONEXISTENT")
        self.assertIn("VERIFICATION FAILED", result)

    def test_submit_duplicate_invoice(self):
        tools.submit_invoice_to_system("DUP-1", "Test", "2026-01-01", 10.0, "2026-02-01")
        result = tools.submit_invoice_to_system("DUP-1", "Test", "2026-01-01", 10.0, "2026-02-01")
        self.assertIn("Error: Invoice DUP-1 already exists", result)

    def test_list_files_sandbox(self):
        result = tools.list_files("../")
        self.assertIn("Error: Cannot access directories outside", result)

    def test_read_file_sandbox(self):
        result = tools.read_file("../../secret.txt")
        self.assertIn("Error: Cannot access files outside", result)
        
    def test_read_file_missing(self):
        result = tools.read_file("data/invoices/missing.txt")
        self.assertIn("Failed to read file", result)

if __name__ == "__main__":
    unittest.main()
