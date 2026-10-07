# Autonomous AI Task Worker

**Author:** Ambati Chaitanya Ram  
**Roll No:** 24110035  
**Institution:** Indian Institute of Technology Gandhinagar  

This is a focused prototype of an autonomous AI worker that accepts a natural-language task, reasons about the required actions, selects tools, observes tool results, handles failures, performs a state-changing operation, independently verifies the result, and only then completes the task. The demonstrated workflow is invoice processing using a local simulated internal system.

## Overview

Traditional tool-calling demos often stop after the model selects and calls a tool. This project focuses on the complete execution loop:

1. Understand the goal
2. Break the task into actions
3. Select an appropriate tool
4. Execute the tool
5. Observe the result
6. Decide what to do next
7. Recover from failures when possible
8. Perform the state-changing action
9. Independently verify the outcome
10. Complete only after verification

The prototype intentionally focuses on a narrow but genuinely executable workflow rather than pretending to automate every possible computer task.

## Demonstrated Workflow

"Find the latest invoice from Acme Corp in the data/invoices directory, extract the invoice number, amount and due date, enter it into our internal system, and verify that it was recorded before completing the task."

```text
Natural-language task
        ↓
AutonomousAgent
        ↓
Gemini function calling
        ↓
Tool selection
        ↓
File discovery / reading
        ↓
Invoice extraction
        ↓
SQLite internal system
        ↓
Independent verification
        ↓
task_complete
```

The worker must discover the appropriate invoice rather than being directly handed the final invoice filename. For the supplied fixtures, the latest Acme invoice should be identified from the invoice dates.

## Architecture

### AutonomousAgent — agent.py
- Gemini model interaction
- native function calling
- tool selection
- observation feedback
- bounded execution
- retry handling
- completion enforcement
- verification state tracking

### Tools — tools.py
- invoice discovery
- file reading
- safe output writing
- calculation
- SQLite persistence
- independent verification
- human clarification

### CLI — main.py
- accepts a natural-language task
- initializes the local environment
- configures tools
- starts the autonomous worker

### Internal System
The internal application is intentionally simulated locally using SQLite rather than connecting to a real company system.

## Key Engineering Features

### Bounded Gemini Retries
- transient failures such as 429/502/503/504 can be retried
- maximum of 3 model attempts
- exponential delays approximately 2s, 4s, 8s
- configuration/authentication failures are not blindly retried

### Bounded Agent Execution
- maximum agent step limit
- prevents uncontrolled/infinite execution
- worker terminates cleanly when the limit is reached

### Programmatic Verification Gate
After a state-changing operation, Python-side controller state requires independent verification before task_complete is accepted.
```text
state-changing action
        ↓
verification required
        ↓
independent verification
        ↓
verification passed
        ↓
task_complete allowed
```

### Tool Error Recovery
Tool failures are returned to the agent as observations so it can reconsider its next action.

### Human Clarification
The worker can ask the user for clarification when the task is ambiguous or requires human input.

## Available Tools

| Tool | Purpose |
|---|---|
| `list_files` | Discover available files |
| `read_file` | Read files within the allowed data directory |
| `write_file` | Write files within the allowed output directory |
| `calculate` | Perform safe arithmetic calculations |
| `submit_invoice_to_system` | Persist invoice data to SQLite |
| `verify_invoice_in_system` | Independently verify the stored invoice |
| `ask_user_for_clarification` | Request human input |
| `task_complete` | Signal successful completion after required checks |

## Data and Security

Reads are restricted to:
`data/`

Writes are restricted to:
`data/output/`

Resolved paths and containment checks are used to prevent traversal outside the allowed directory.
The internal invoice system is local SQLite.
- no real credentials are included
- no confidential data is required
- no unauthorized third-party systems are accessed
- invoice fixtures are fictional

## Repository Structure

```text
ai-task-worker-prototype/
├── agent.py
├── tools.py
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── data/
│   └── invoices/
│       ├── acme_invoice_2026_08.txt
│       ├── acme_invoice_2026_09.txt
│       ├── acme_invoice_2026_10.txt
│       └── globex_invoice_2026_10.txt
└── tests/
    ├── conftest.py
    ├── test_tools.py
    └── test_agent_retry.py
```

## Setup

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then:

```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

Optional model configuration:

```powershell
$env:GEMINI_MODEL="gemini-3.8-flash"
```

## Running

```powershell
python main.py
```

A custom natural-language task can be supplied as arguments:
```powershell
python main.py "Find the latest invoice from Acme Corp in the data/invoices directory, extract the invoice number, amount and due date, enter it into our internal system, and verify that it was recorded before completing the task."
```

## Testing

```powershell
pytest -q
```

Tests cover the important deterministic parts of the worker, including:
- invoice persistence
- duplicate handling
- invoice verification
- incorrect verification data
- filesystem boundary enforcement
- model retry behavior
- completion gating

## Reliability

### Model/API failures
Transient Gemini failures can be retried with bounded backoff.

### Tool failures
Tool errors are returned to the agent as observations so the agent can reassess the next action.

### Execution limits
The worker has a maximum number of agent steps to prevent uncontrolled execution.

These mechanisms improve reliability but do not guarantee successful completion for every arbitrary task.

## Verification

The worker does not treat "the model said it succeeded" as sufficient evidence. For the invoice workflow:

1. Invoice data is extracted.
2. The invoice is persisted to SQLite.
3. The verification tool independently queries SQLite.
4. Critical stored values (invoice number, company, amount, due date) are compared.
5. Only after successful verification can the agent complete the task.

## Design Decisions

### Native Gemini function calling
Keeps the prototype simple and directly exposes the available tools to the model.

### SQLite
Provides a real persistent local state store without requiring an external service.

### Python-side completion enforcement
Prevents the model from bypassing the verification requirement by simply declaring success.

### Narrow workflow
A smaller genuinely working autonomous workflow is preferable to a broad collection of mocked capabilities.

### Local fictional data
Keeps the demonstration safe and reproducible without requiring real credentials or external systems.

## Limitations

- Current demonstration focuses on structured/text invoice files.
- Internal system is a local SQLite simulation.
- No real enterprise application integration.
- No browser automation in the current prototype.
- No production-grade isolation or sandboxing.
- Model/API availability can still affect execution.
- Natural-language extraction quality depends on the model and input format.
- The agent is bounded by a maximum execution-step limit.

## Future Improvements

- browser/computer automation
- PDF and OCR invoice processing
- multimodal document understanding
- richer recovery strategies
- stronger state tracking
- production-grade sandboxing
- additional enterprise integrations
- longer-term memory for multi-step workflows
- richer verification/evidence collection

## Assignment Coverage

| Requirement | Implementation |
|---|---|
| Understand end goal | Natural-language task + model reasoning |
| Break into actions | Tool/function-calling loop |
| Use tools | File, calculation, SQLite, clarification tools |
| Observe results | Tool outputs returned to model |
| Decide next action | Iterative agent loop |
| Detect failures | Tool/model error handling |
| Retry/recover | Bounded model retries + tool feedback |
| Verify outcome | Independent SQLite verification |
| Human clarification | ask_user_for_clarification |
| Safe completion | Programmatic completion gate |
| Reproducibility | Local fictional invoice fixtures + SQLite |

## Why This Prototype

The important engineering idea is not simply calling an LLM tool, but controlling the complete execution lifecycle:
`reason` → `act` → `observe` → `recover` → `verify` → `complete`

## License
This project is open-source and available under the [MIT License](LICENSE).
