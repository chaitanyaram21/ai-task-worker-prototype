import os
import tools
from agent import AutonomousAgent

def main():
    # 1. Environment Check
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ Please set the GEMINI_API_KEY environment variable.")
        return

    # 2. Setup Mock Environment
    # We create a fake invoice file to simulate the user's messy file system
    mock_invoice = """
    =============================
             INVOICE
    =============================
    From: Acme Corp
    To: Example Inc.
    Date: 2023-10-25
    Due Date: 2023-11-25
    Amount Due: 1450.00
    
    Items:
    - Server Hosting: $1,000.00
    - Maintenance: $450.00
    =============================
    """
    tools.write_file("invoice_acme.txt", mock_invoice)
    print("📁 Mock environment ready (invoice_acme.txt created).")

    # 3. Register tools the agent is allowed to use
    available_tools = [
        tools.search_web,
        tools.read_file,
        tools.write_file,
        tools.calculate,
        tools.submit_invoice_to_system,
        tools.task_complete,
        tools.ask_user_for_clarification
    ]

    # 4. Initialize Agent
    worker = AutonomousAgent(tools_list=available_tools)
    
    # 5. Define Task (Matches the prompt's example exactly)
    task_prompt = (
        "Find the latest invoice from Acme Corp in the local directory (invoice_acme.txt), "
        "extract the amount and due date, enter it into our internal system, "
        "and tell me once it is done."
    )
    
    # 6. Run
    worker.run(task_prompt)

if __name__ == "__main__":
    main()