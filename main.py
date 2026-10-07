import os
import sys
import tools
from agent import AutonomousAgent

def main():
    # 1. Environment Check
    if not os.environ.get("GEMINI_API_KEY"):
        print("[ERROR] Please set the GEMINI_API_KEY environment variable.")
        return

    # 2. Setup SQLite Database Environment
    tools.init_db()

    # 3. Register available tools
    available_tools = [
        tools.list_files,
        tools.read_file,
        tools.write_file,
        tools.submit_invoice_to_system,
        tools.verify_invoice_in_system,
        tools.search_web,
        tools.calculate,
        tools.ask_user_for_clarification,
        tools.task_complete
    ]

    # 4. Initialize Agent
    worker = AutonomousAgent(tools_list=available_tools)
    
    # 5. Define Task 
    # Use CLI arguments if provided, else fall back to the default task prompt
    if len(sys.argv) > 1:
        task_prompt = " ".join(sys.argv[1:])
    else:
        task_prompt = (
            "Find the latest invoice from Acme Corp in the data/invoices directory, "
            "extract the invoice number, amount and due date, enter it into our internal system, "
            "and verify that it was recorded before completing the task."
        )
    
    # 6. Run
    worker.run(task_prompt)

if __name__ == "__main__":
    main()