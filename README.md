# Autonomous AI Task Worker Prototype

**Author:** Ambati Chaitanya Ram  
**Roll No:** 24110035  
**Institution:** Indian Institute of Technology Gandhinagar  

## Project Overview
This project solves the problem of manual business process execution by providing an Autonomous AI Worker. It takes a natural-language task (e.g., extracting invoice data and entering it into an internal system) and autonomously reasons, plans, and acts to complete it.

The agent operates in a constrained, secure local sandbox using a SQLite database as a persistent internal system and restricted filesystem tools.

## Architecture
```
User
 |
 v
Autonomous Agent (gemini-3.8-flash)
 |
 v
LLM Function Calling
 |
 +--> File Tools (list_files, read_file, write_file)
 |
 +--> Web Tool (Wikipedia Search)
 |
 +--> Calculator
 |
 +--> Internal SQLite System (submit_invoice, verify_invoice)
 |
 +--> Human Clarification (ask_user_for_clarification)
 |
 v
Observation
 |
 v
Agent (Evaluates state, checks for failures/retries)
 |
 v
Verification (Independent Database Query)
 |
 +--> Success --> Completion
 |
 +--> Failure --> Retry / Alternative
```

## Demo Workflow
1. **Natural Language Task**: "Find the latest invoice from Acme Corp..."
2. **File Discovery**: Agent uses `list_files("data/invoices")` to find candidate files.
3. **Reading**: Agent reads the files to extract the invoice number, date, amount, and due date.
4. **Submission**: Agent calls `submit_invoice_to_system` which persists the record in the local SQLite database.
5. **Verification**: Agent is strictly required to call `verify_invoice_in_system` to independently query the database and confirm the record was saved correctly.
6. **Completion**: Agent reports evidence of completion.

## Setup Instructions

1. Install Python 3.10 or higher.
2. Initialize and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   # On Mac/Linux:
   source .venv/bin/activate
   ```
3. Install the required dependencies: 
   ```bash
   pip install -r requirements.txt
   ```
4. Get a free Gemini API key from Google AI Studio.
5. Set your API key as an environment variable in your terminal:
   - **Command Prompt (Windows):** `set GEMINI_API_KEY=your_key_here`
   - **PowerShell (Windows):** `$env:GEMINI_API_KEY="your_key_here"`
   - **Mac/Linux:** `export GEMINI_API_KEY="your_key_here"`

## Run
To run the default invoice processing workflow:
```bash
python main.py
```

To run a custom task:
```bash
python main.py "Find the invoice from Globex Corp in data/invoices, extract the details, submit it, and verify it."
```

## Tests
The project includes a suite of unit tests for the tools, testing SQLite persistence, verification, and filesystem sandbox restrictions.
Run tests via:
```bash
python -m unittest discover tests
```

## Design Decisions
- **Native Function Calling:** We use the native Gemini SDK function calling feature because it guarantees highly structured, reliable API interactions compared to regex parsing.
- **Local SQLite DB:** Rather than mocking a "SUCCESS" response, the agent interacts with a real SQLite database (`data/internal_system.db`) to ensure persistent state change and allow for actual verification.
- **Independent Verification:** The agent is strictly prohibited from claiming success based on the submission tool's output alone. It must perform a separate database query to verify the transaction.
- **Bounded Retries:** The agent tracks consecutive failures. If a tool fails 3 times, the agent is forced to try an alternative approach or halt.
- **Human Clarification:** We implemented an `ask_user_for_clarification` tool, giving the agent a safe escalation path if data is ambiguous or authorization is required.

## Reliability and Generalization
- **Errors as Observations:** Python exceptions do not crash the script; they are caught and fed back to the LLM so it can learn from its mistake.
- **Generalization:** The agent is not hardcoded to a single script. Because it relies on a dynamic ReAct loop, it can accomplish entirely different tasks (like web searching or math) using the same engine.

## Known Limitations
- **No GUI / Browser Vision:** The current prototype relies on text parsing and constrained Wikipedia search rather than arbitrary Playwright browser automation or computer-vision.
- **Local Sandboxing Only:** While the filesystem tools prevent directory traversal (`../`), it lacks production-grade microVM isolation.

## Future Work
- **Playwright Browser Automation:** Giving the agent a headless browser to log into real SaaS platforms and scrape/click dynamically.
- **Multimodal File Reading:** Upgrading the `read_file` tool to pass images and PDFs directly into Gemini's multimodal context, bypassing text-only limitations.
- **RAG Memory:** Implementing a Vector Database for long-term semantic memory across different execution sessions.

## Requirement Coverage

| Requirement | Implementation |
|-------------|----------------|
| Natural-language task | Agent accepts arbitrary task text via CLI |
| Planning/action selection | Handled natively by LLM function calling loop |
| Tool execution | File sandbox, SQLite DB, Calculator, Web tools |
| Observation | Tool results safely returned as string observations |
| Memory | Conversational state maintained during execution |
| Failure detection | Exceptions caught and returned as observations |
| Retry | Bounded retry logic (max 3 consecutive failures) |
| Verification | Independent SQLite `SELECT` verification tool |
| Human clarification | `ask_user_for_clarification` tool interrupts execution |
| Completion evidence | Verified record data included in `task_complete` |
| Generalization | Supports user-supplied tasks via command line |

## License
This project is open-source and available under the [MIT License](LICENSE).
