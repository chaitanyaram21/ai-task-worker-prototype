import os
import json
import urllib.request
import urllib.parse
import ast
import sqlite3
from pathlib import Path

DB_PATH = os.path.join("data", "internal_system.db")
ROOT_DIR = Path(__file__).parent.resolve()
DATA_DIR = (ROOT_DIR / "data").resolve()
OUTPUT_DIR = (DATA_DIR / "output").resolve()

def init_db(db_path: str = DB_PATH):
    """Initializes the SQLite database with the required schema."""
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            company_name TEXT NOT NULL,
            invoice_date TEXT NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'recorded',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def _is_safe_path(filepath: str, allowed_root: Path) -> bool:
    try:
        target = Path(filepath).resolve()
        return target.is_relative_to(allowed_root)
    except Exception:
        return False

def list_files(directory: str) -> str:
    """Lists files in the specified directory. Use this to discover available files (e.g. data/invoices)."""
    try:
        target_dir = Path(directory).resolve()
        if not _is_safe_path(target_dir, DATA_DIR):
            return "Error: Cannot access directories outside the allowed data/ workspace."
        if not target_dir.exists():
            return f"Error: Directory '{target_dir}' does not exist."
        files = [f.name for f in target_dir.iterdir() if f.is_file()]
        return json.dumps(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

def read_file(filepath: str) -> str:
    """Reads the contents of a file on the local filesystem. Use this to inspect files."""
    try:
        target_file = Path(filepath).resolve()
        if not _is_safe_path(target_file, DATA_DIR):
            return "Error: Cannot access files outside the allowed data/ workspace."
        with open(target_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Failed to read file: {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """Writes the given content to a file. Restricted to data/output/."""
    try:
        target_file = Path(filepath).resolve()
        if not _is_safe_path(target_file, OUTPUT_DIR):
            return "Error: Can only write files to the data/output/ directory."
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {target_file.name}"
    except Exception as e:
        return f"Failed to write file: {str(e)}"

def submit_invoice_to_system(invoice_number: str, company_name: str, invoice_date: str, amount: float, due_date: str) -> str:
    """Records an invoice in the local simulated company database (SQLite).
    This changes persistent state.
    After calling this tool, you MUST use verify_invoice_in_system to independently confirm the record exists.
    """
    if not invoice_number or not company_name:
        return "Error: invoice_number and company_name cannot be empty."
    try:
        amount_float = float(amount)
    except ValueError:
        return "Error: amount must be a numeric value."

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,))
        if cursor.fetchone():
            conn.close()
            return f"Invoice {invoice_number} already exists in the internal system."
        
        cursor.execute('''
            INSERT INTO invoices (invoice_number, company_name, invoice_date, amount, due_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (invoice_number, company_name, invoice_date, amount_float, due_date))
        conn.commit()
        conn.close()
        return f"SUCCESS: Invoice {invoice_number} submitted."
    except Exception as e:
        return f"Database Error: {str(e)}"

def verify_invoice_in_system(invoice_number: str, company_name: str, amount: float, due_date: str) -> str:
    """Queries the simulated company database and independently verifies whether an invoice exists and matches all expected fields.
    This is an independent verification operation and must be used before task completion.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT company_name, amount, due_date, status FROM invoices WHERE invoice_number = ?", (invoice_number,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return json.dumps({
                "verified": False,
                "record_exists": False,
                "error": f"No matching invoice found for number {invoice_number}."
            })
            
        db_company, db_amount, db_due_date, db_status = row
        try:
            expected_amount = float(amount)
        except ValueError:
            expected_amount = None

        company_match = (db_company.lower() == company_name.lower())
        amount_match = (db_amount == expected_amount)
        due_date_match = (db_due_date == due_date)
        
        verified = company_match and amount_match and due_date_match

        return json.dumps({
            "verified": verified,
            "record_exists": True,
            "invoice_number_match": True,
            "company_match": company_match,
            "amount_match": amount_match,
            "due_date_match": due_date_match,
            "status": db_status
        }, indent=2)

    except Exception as e:
        return f"Database Error: {str(e)}"

def search_web(query: str) -> str:
    """Searches the web for the given query using Wikipedia and returns a summary."""
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'AIWorker/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            results = [f"- {item['title']}: {item['snippet']}..." for item in data['query']['search'][:3]]
            return "\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search failed: {str(e)}"

def calculate(expression: str) -> str:
    """Evaluates a mathematical expression and returns the result."""
    try:
        node = ast.parse(expression, mode='eval')
        return str(eval(compile(node, '<string>', 'eval'), {"__builtins__": None}, {}))
    except Exception as e:
        return f"Calculation failed: {str(e)}"

def ask_user_for_clarification(question: str) -> str:
    """Pauses execution to ask the human user a question for clarification or approval."""
    print(f"\n[CLARIFICATION NEEDED] {question}")
    human_response = input("Your response: ")
    return f"User replied: {human_response}"

def task_complete(summary: str, evidence: str) -> str:
    """Call this tool ONLY when you have achieved the user's end goal and independently verified the outcome.
    Provide a summary of the actions taken and the verified evidence.
    """
    return f"TASK COMPLETED SUCCESSFULLY\nSummary: {summary}\nEvidence:\n{evidence}"