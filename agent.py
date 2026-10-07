import os
import time
from google import genai
from google.genai import types

class AutonomousAgent:
    def __init__(self, tools_list, max_retries=3, max_agent_steps=20):
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        
        # Check API key first
        if not os.environ.get("GEMINI_API_KEY"):
            print("[CONFIGURATION ERROR]\nGemini authentication or model configuration failed.\nCheck GEMINI_API_KEY and GEMINI_MODEL.")
            raise ValueError("GEMINI_API_KEY not set")
            
        self.client = genai.Client()
        self.tools_list = tools_list
        self.max_retries = max_retries
        self.max_agent_steps = max_agent_steps
        self.consecutive_failures = 0
        
        # State tracking for programmatic verification
        self.state_changed = False
        self.verification_passed = False
        
        self.system_prompt = """You are an autonomous AI task worker.
Follow these rules strictly:
1. Focus on accomplishing the user's end goal, not merely producing a textual answer.
2. Choose tools based on the current task and observations.
3. Treat tool outputs as observations, not automatically as proof that the requested outcome was achieved.
4. When a task requires a state change, independently verify the resulting state whenever a verification mechanism is available.
5. Do not call task_complete until the requested outcome has been verified, unless verification is genuinely impossible and the user is explicitly informed.
6. Never declare the task complete merely because a tool returned a success message.
7. If a tool fails, inspect the error and attempt a reasonable retry or alternative when safe.
8. Never retry indefinitely. If an approach fails repeatedly, attempt a reasonable alternative rather than repeating the identical action.
9. Ask the user for clarification when important information is ambiguous, multiple targets exist, or proceeding could cause an unsafe action.
10. Do not invent tool results, database records, files, or successful actions.
11. Keep the final response concise but include useful evidence of completion.
"""
        try:
            self.chat = self.client.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    tools=self.tools_list,
                    temperature=0.1,
                    system_instruction=self.system_prompt
                )
            )
        except Exception as e:
            print(f"[CONFIGURATION ERROR]\nGemini authentication or model configuration failed.\nError: {str(e)}")
            raise

    def send_message_with_retry(self, content):
        """Wraps Gemini requests with bounded exponential backoff for transient errors."""
        base_wait = 2
        for attempt in range(1, self.max_retries + 1):
            try:
                return self.chat.send_message(content)
            except Exception as e:
                error_msg = str(e).lower()
                # Check for transient errors
                if any(x in error_msg for x in ["503", "429", "unavailable", "high demand", "overloaded", "rate limit", "502", "504"]):
                    if attempt == self.max_retries:
                        print(f"\n[MODEL ERROR]\nGemini API is temporarily unavailable after {self.max_retries} attempts.\n\nThe task was not completed because the AI worker could not obtain a model response.\n\nPlease try again later.")
                        return None
                    wait_time = base_wait ** attempt
                    print(f"\n[MODEL RETRY]\nGemini temporarily unavailable (503/429).\nRetrying in {wait_time} seconds... (attempt {attempt}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    # Non-transient errors (auth, config, 404, etc.)
                    print(f"\n[CONFIGURATION ERROR]\nGemini authentication or model configuration failed.\nError details: {str(e)}")
                    return None
        return None

    def run(self, task: str):
        print(f"\n[USER TASK]\n{task}\n")
        print("-" * 50)
        
        response = self.send_message_with_retry(task)
        if not response:
            return
            
        step_count = 0
        
        while step_count < self.max_agent_steps:
            step_count += 1
            if response.function_calls:
                parts = []
                for function_call in response.function_calls:
                    fn_name = function_call.name
                    args = function_call.args
                    
                    log_args = {k: (v if len(str(v)) < 100 else str(v)[:100] + "...") for k, v in args.items()}
                    print(f"\n[ACTION]\nTool: {fn_name}\nArguments: {log_args}")
                    
                    # Track programmatic state constraints
                    if fn_name == "task_complete":
                        if self.state_changed and not self.verification_passed:
                            result = "TASK_COMPLETION_REJECTED: The task cannot be marked complete yet. A state-changing action occurred but independent verification has not passed. Use the appropriate verification tool first."
                            print(f"\n[SYSTEM INTERVENTION]\n{result}")
                            parts.append(types.Part.from_function_response(name=fn_name, response={"result": result}))
                            continue
                        else:
                            # Actually complete
                            result = self.execute_tool(fn_name, args)
                            print(f"\n[WORKFLOW TERMINATED]\n{result}")
                            return result

                    # Execute
                    result = self.execute_tool(fn_name, args)
                    print(f"\n[OBSERVATION]\n{result}")
                    
                    # Monitor state changes and verifications
                    if fn_name in ["submit_invoice_to_system", "write_file"] and "Error" not in str(result):
                        self.state_changed = True
                    
                    if fn_name == "verify_invoice_in_system":
                        if '"verified": true' in str(result).lower():
                            self.verification_passed = True
                    
                    if "Error" in str(result) or "FAILED" in str(result):
                        self.consecutive_failures += 1
                        if self.consecutive_failures >= self.max_retries:
                            result = f"SYSTEM ERROR: Action failed {self.consecutive_failures} consecutive times. You MUST attempt a different alternative approach, report failure, or use ask_user_for_clarification."
                            print(f"\n[SYSTEM ALERT]\n{result}")
                    else:
                        self.consecutive_failures = 0
                        
                    parts.append(types.Part.from_function_response(name=fn_name, response={"result": result}))
                
                response = self.send_message_with_retry(parts)
                if not response:
                    return
            else:
                if response.text:
                    print(f"\n[THOUGHT]\n{response.text.strip()}")
                
                response = self.send_message_with_retry("Please use a tool to progress the task, or use task_complete if you have independently verified that the outcome is achieved.")
                if not response:
                    return
                    
        # If loop exits due to step limit
        print("\n[AGENT LIMIT]\nMaximum agent steps reached.\n\nThe task could not be completed safely within the allowed number of actions.")
        return

    def execute_tool(self, name: str, args: dict) -> str:
        for tool in self.tools_list:
            if tool.__name__ == name:
                try:
                    return tool(**args)
                except Exception as e:
                    return f"Error executing tool: {type(e).__name__} - {str(e)}"
        return f"Error: Unknown tool {name}"