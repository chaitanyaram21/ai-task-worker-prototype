import os
import sys
import tools
from agent import AutonomousAgent

def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("[CONFIGURATION ERROR]\nGEMINI_API_KEY environment variable not found.\nPlease set it before running.")
        sys.exit(1)

    tools.init_db()

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

    try:
        worker = AutonomousAgent(tools_list=available_tools)
    except Exception:
        sys.exit(1)
    
    if len(sys.argv) > 1:
        task_prompt = " ".join(sys.argv[1:])
    else:
        task_prompt = (
            "Find the latest invoice from Acme Corp in the data/invoices directory, "
            "extract the invoice number, amount and due date, enter it into our internal system, "
            "and verify that it was recorded before completing the task."
        )
    
    worker.run(task_prompt)

if __name__ == "__main__":
    main()