import json
import tools
from pathlib import Path

def test_submit_and_verify_invoice(setup_test_env):
    res1 = tools.submit_invoice_to_system("INV-001", "Acme", "2026-10-01", 1000.50, "2026-11-01")
    assert "SUCCESS" in res1
    
    # Test identical duplicate
    res2 = tools.submit_invoice_to_system("INV-001", "Acme", "2026-10-01", 1000.50, "2026-11-01")
    assert "already exists" in res2

    # Verification success
    verify_str = tools.verify_invoice_in_system("INV-001", "Acme", 1000.50, "2026-11-01")
    verify_data = json.loads(verify_str)
    assert verify_data["verified"] is True
    assert verify_data["amount_match"] is True

    # Verification failure on incorrect amount
    verify_str_bad = tools.verify_invoice_in_system("INV-001", "Acme", 999.00, "2026-11-01")
    verify_data_bad = json.loads(verify_str_bad)
    assert verify_data_bad["verified"] is False
    assert verify_data_bad["amount_match"] is False

def test_file_tools_security(setup_test_env):
    # Setup test file
    test_file = tools.DATA_DIR / "test.txt"
    test_file.write_text("hello")
    
    # Can read safe file
    assert tools.read_file(str(test_file)) == "hello"
    
    # Cannot read outside directory
    outside_file = setup_test_env / "secret.txt"
    outside_file.write_text("secret")
    res = tools.read_file(str(outside_file))
    assert "Error: Cannot access" in res
    
    # Write only to output
    res = tools.write_file(str(tools.OUTPUT_DIR / "out.txt"), "output")
    assert "Successfully" in res
    
    # Cannot write directly to data/ or outside
    res = tools.write_file(str(tools.DATA_DIR / "out.txt"), "output")
    assert "Can only write files to the data/output/" in res
