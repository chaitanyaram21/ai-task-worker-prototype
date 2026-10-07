# Autonomous AI Task Worker

**Author:** Ambati Chaitanya Ram  
**Roll No:** 24110035  
**Institution:** Indian Institute of Technology Gandhinagar  

## Overview
This project is an Autonomous AI Task Worker that receives a natural-language task and executes it autonomously using the Gemini API.

## Problem Being Solved
Manual business processes (like discovering, reading, and entering invoices into a database) are time-consuming. This project demonstrates an AI agent that can autonomously navigate a local filesystem, extract structured data from unstructured text, and interact with a simulated internal database to complete workflows without hardcoded scripts.

## Architecture
```text
User Task
   ↓
Gemini
   ↓
Tool Selection
   ↓
Tool Execution
   ↓
Observation
   ↓
Gemini
   ↓
Verification
   ↓
Task Completion
```

## Expected Workflow
For the primary invoice task, the expected autonomous sequence is:
`discover (list_files)` → `read (read_file)` → `extract (LLM)` → `submit (submit_invoice_to_system)` → `verify (verify_invoice_in_system)` → `complete (task_complete)`

## Available Tools
- `list_files`: Discover files in a directory.
- `read_file` / `write_file`: Safely read and write files within the sandbox.
- `submit_invoice_to_system`: Persists extracted invoice data to the SQLite database.
- `verify_invoice_in_system`: Independently queries the SQLite database to verify all fields.
- `ask_user_for_clarification`: Halts execution to ask a human when ambiguity exists.
- `task_complete`: Finishes the workflow, providing a summary and evidence.

## Setup
1. Create a virtual environment and activate it:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Set your API key:
   ```powershell
   $env:GEMINI_API_KEY="your_api_key_here"
   ```
   *(Optional) You can change the model via `$env:GEMINI_MODEL="gemini-1.5-pro"` (default is `gemini-3.8-flash`).*

## Running
Run the default invoice task:
```powershell
python main.py "Find the latest invoice from Acme Corp in the data/invoices directory, extract the invoice number, amount and due date, enter it into our internal system, and verify that it was recorded before completing the task."
```

## Reliability
- **Bounded Gemini Retries**: Uses exponential backoff (2s, 4s, 8s) up to 3 times to cleanly handle `503` (high demand) and `429` (rate limit) errors.
- **Honest Failures**: Does not print giant tracebacks on standard errors. If the model is completely unavailable after 3 attempts, it terminates cleanly.
- **Configuration Errors**: 401, 403, and 404 errors (like invalid models) are caught and reported as `[CONFIGURATION ERROR]`.
- **Maximum Agent Steps**: Hard limit of 20 steps prevents infinite looping.
- **Tool Failure Recovery**: Failures during tool execution are caught and passed to the LLM as observations, enabling bounded alternative strategies.

## Verification
The prototype does not blindly trust completion.
- `submit_invoice_to_system()` persists the invoice to a real, stateful SQLite database.
- `verify_invoice_in_system()` independently queries the database to compare expected values.
- **Programmatic Enforcement**: The agent loop internally prevents the LLM from completing the task if a state-changing operation occurred without a subsequent successful independent verification.

## Safety
- **File Sandbox**: `read_file` and `list_files` strictly enforce boundaries via `pathlib` resolve checks (restricted to `data/`).
- **Write Restrictions**: `write_file` is completely restricted to `data/output/`.
- **Duplicate Protection**: SQLite prevents inserting duplicate invoices.
- **Human Clarification**: An `ask_user_for_clarification` tool exists to break ambiguities safely.

## Testing
To run the automated tests (verifying retries, DB persistence, boundaries):
```powershell
pytest -q
```

## Limitations
- **Local simulated internal system**: Uses SQLite instead of a full enterprise ERP.
- **Fictional data**: Relies on `data/invoices` text files.
- **API Dependency**: Fully dependent on Google Gemini's availability.
- **No external credentials**: Does not connect to live corporate endpoints.
- **Narrow domain**: Primarily focused on basic file processing and data entry.

## Future Improvements
- Browser interaction (e.g., Playwright)
- Richer approval workflows
- Additional verification mechanisms

## License
This project is open-source and available under the [MIT License](LICENSE).
