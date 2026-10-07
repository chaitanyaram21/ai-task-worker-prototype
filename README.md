# Autonomous AI Task Worker Prototype

**Author:** Ambati Chaitanya Ram  
**Roll No:** 24110035  
**Institution:** Indian Institute of Technology Gandhinagar  

This is a prototype of an Autonomous AI Worker capable of taking a natural language instruction, reasoning about it, utilizing simulated tools (file system, web search, internal APIs), and verifying completion. 

It is built in Python using the official `google-genai` SDK, taking advantage of native LLM function calling to achieve a stable Reason-and-Act (ReAct) loop.

## Setup and Run Instructions
1. Install Python 3.10 or higher.
2. Install the required dependencies: `pip install -r requirements.txt`
3. Get a free Gemini API key from Google AI Studio.
4. Set your API key as an environment variable in your terminal:
   - **Command Prompt (Windows):** `set GEMINI_API_KEY=your_key_here`
   - **PowerShell (Windows):** `$env:GEMINI_API_KEY="your_key_here"`
   - **Mac/Linux:** `export GEMINI_API_KEY="your_key_here"`
5. Run the prototype: `python main.py`

## Architecture
The prototype relies on a **ReAct (Reason and Act) loop** driven by the `google-genai` SDK. 
- **The Brain:** The `AutonomousAgent` wraps a persistent LLM chat session. 
- **The Hands:** A suite of isolated Python functions (`tools.py`) are passed to the model via native function calling schemas. 
- **The Loop:** When given a prompt, the model returns a `function_call` payload instead of text. The Python script intercepts this, executes the local code (e.g., reading a file or hitting an API mock), and injects the output back into the chat as an observation. The model evaluates the result and loops until it confidently triggers the `task_complete` tool.

## Important Technical & Design Decisions
1. **Native Function Calling over Regex Parsing:** Older agents required prompting the LLM to output specific JSON formats and parsing them manually. I used native function calling schemas. This drastically improves reliability, as the model is fine-tuned at the API level to strictly adhere to tool parameter signatures.
2. **Deterministic Termination:** I implemented an explicit `task_complete` tool. This solves the classic agent problem of infinite loops. The agent has a clear, programmatic way to signal that it believes the objective is met, passing its final verification summary.
3. **Error Catching as Feedback:** If a tool fails (e.g., trying to read a missing file), the system doesn't crash. Instead, the `try/except` block returns the error string to the LLM. The system prompt instructs the agent to read this error and attempt a retry or an alternative approach, ensuring high resilience.
4. **Generalization:** Because the ReAct loop evaluates actions dynamically rather than executing a hardcoded script, the exact same agent engine can accomplish entirely different tasks just by changing the `task_prompt`.

## Known Limitations
- **Context Window Exhaustion:** For a workflow requiring 50+ steps, the chat history will grow indefinitely. Eventually, it will exceed the token limit, requiring a context-summarization mechanism.
- **Sandboxing:** The `calculate` tool uses Python's `ast` for safety, but in a production environment, tools interacting with files or code execution need to be heavily isolated using Docker or microVMs (like Firecracker).
- **No Vision:** This specific prototype relies on text extraction. It cannot natively process PDF invoices or navigate visual UI elements without additional tools.

## What I Would Build Next
If given more time, I would build:
1. **Playwright/Browser Integration:** Moving beyond mock APIs, I would give the agent a headless browser tool to log into real SaaS platforms, navigate DOM trees, and scrape/click dynamically.
2. **Multimodal File Reading:** Upgrading the `read_file` tool to pass images and PDFs directly into Gemini's multimodal context, bypassing the need for separate OCR pipelines.
3. **Vector Database Memory:** Implementing a RAG database to give the agent long-term memory across entirely different sessions.

## Assumptions Made
- I assumed a mock internal environment is acceptable to demonstrate the logical reasoning capabilities of the agent without requiring real-world, authenticated SaaS credentials.
- I assumed the user wants the agent to run locally on their machine, hence the use of local filesystem tools.

## Details of Models and APIs Used
- **Model:** `gemini-3.8-flash` (chosen for its exceptionally fast inference speed, which is crucial for multi-step agent loops, and its native support for complex function calling).
- **SDK:** Official `google-genai` Python SDK.
- **External Services:** A lightweight call to the Wikipedia API is used to simulate a live web search tool.

## License
This project is open-source and available under the [MIT License](LICENSE).
