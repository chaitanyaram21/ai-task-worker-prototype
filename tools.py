import os
import json
import urllib.request
import urllib.parse
import ast
import sqlite3
from typing import Optional

DB_PATH = os.path.join("data", "internal_system.db")

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

def list_files(directory: str) -> str:
    """Lists files in the specified directory. Use this to discover available files (e.g. data/invoices)."""
    try:
        safe_dir = os.path.normpath(directory)
        if ".." in safe_dir or safe_dir.startswith("/") or safe_dir.startswith("\\") or ":" in safe_dir:
            return "Error: Cannot access directories outside the allowed workspace."
        if not os.path.exists(safe_dir):
            return f"Error: Directory '{safe_dir}' does not exist."
        files = os.listdir(safe_dir)
        return json.dumps(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

def read_file(filepath: str) -> str:
    """Reads the contents of a file on the local filesystem. Use this to inspect files."""
    try:
        safe_path = os.path.normpath(filepath)
        if ".." in safe_path or safe_path.startswith("/") or safe_path.startswith("\\") or ":" in safe_path:
            return "Error: Cannot access files outside the allowed workspace."
        with open(safe_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Failed to read file: {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """Writes the given content to a file on the local filesystem."""
    try:
        safe_path = os.path.normpath(filepath)
        if ".." in safe_path or safe_path.startswith("/") or safe_path.startswith("\\") or ":" in safe_path:
            return "Error: Cannot access files outside the allowed workspace."
        os.makedirs(os.path.dirname(safe_path) or '.', exist_ok=True)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
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
        
        # Check for duplicates
        cursor.execute("SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,))
        if cursor.fetchone():
            conn.close()
            return f"Error: Invoice {invoice_number} already exists in the system."
        
        cursor.execute('''
            INSERT INTO invoices (invoice_number, company_name, invoice_date, amount, due_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (invoice_number, company_name, invoice_date, amount_float, due_date))
        conn.commit()
        conn.close()
        return f"SUCCESS: Invoice {invoice_number} submitted."
    except Exception as e:
        return f"Database Error: {str(e)}"

def verify_invoice_in_system(invoice_number: str) -> str:
    """Queries the simulated company database and verifies whether an invoice matching the supplied invoice_number exists.
    This is an independent verification operation and should be used before task completion when an invoice is submitted.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT company_name, invoice_date, amount, due_date, status FROM invoices WHERE invoice_number = ?", (invoice_number,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return f"VERIFIED: Invoice ID {invoice_number} found.\nCompany: {row[0]}\nDate: {row[1]}\nAmount: {row[2]}\nDue Date: {row[3]}\nStatus: {row[4]}"
        else:
            return f"VERIFICATION FAILED: No matching invoice found in the internal system for number {invoice_number}."
    except Exception as e:
        return f"Database Error: {str(e)}"

def search_web(query: str) -> str:
    """Searches the web for the given query using Wikipedia and returns a summary. The prototype uses this constrained tool rather than arbitrary website automation."""
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
    print(f"\n[HUMAN CLARIFICATION REQUIRED]: {question}")
    human_response = input("Your response: ")
    return f"User replied: {human_response}"

def task_complete(summary: str, evidence: str) -> str:
    """Call this tool ONLY when you have achieved the user's end goal and independently verified the outcome.
    Provide a summary of the actions taken and the verified evidence (e.g. database verification result).
    """
    return f"TASK COMPLETED SUCCESSFULLY\nSummary: {summary}\nEvidence:\n{evidence}"