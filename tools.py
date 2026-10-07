import os
import json
import urllib.request
import urllib.parse
import ast

def search_web(query: str) -> str:
    """Searches the web for the given query and returns a summary of results. Useful for finding information."""
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'AIWorker/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            results = [f"- {item['title']}: {item['snippet']}..." for item in data['query']['search'][:3]]
            return "\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search failed: {str(e)}"

def read_file(filepath: str) -> str:
    """Reads the contents of a file on the local filesystem. Use this to inspect files."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Failed to read file: {str(e)}. Check if the path is correct."

def write_file(filepath: str, content: str) -> str:
    """Writes the given content to a file on the local filesystem."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Failed to write file: {str(e)}"

def calculate(expression: str) -> str:
    """Evaluates a mathematical expression and returns the result."""
    try:
        # Safe evaluation of basic math
        node = ast.parse(expression, mode='eval')
        return str(eval(compile(node, '<string>', 'eval'), {"__builtins__": None}, {}))
    except Exception as e:
        return f"Calculation failed: {str(e)}"

def submit_invoice_to_system(company_name: str, amount: float, due_date: str) -> str:
    """Submits extracted invoice details to the internal accounting system API."""
    # This acts as our simulated internal company application
    return f"SUCCESS: Invoice for {company_name} of amount ${amount} due on {due_date} has been recorded in the internal system."

def task_complete(summary: str) -> str:
    """Call this tool ONLY when you have achieved the user's end goal. Provide a summary of the outcome."""
    return f"TASK FINISHED: {summary}"

def ask_user_for_clarification(question: str) -> str:
    """Pauses execution to ask the human user a question for clarification or approval."""
    print(f"\n⚠️  [Agent Needs Help]: {question}")
    human_response = input("Your response: ")
    return f"User replied: {human_response}"