from google import genai
from google.genai import types

class AutonomousAgent:
    def __init__(self, tools_list, model_name="gemini-3.8-flash", max_retries=3):
        self.client = genai.Client()
        self.tools_list = tools_list
        self.max_retries = max_retries
        self.consecutive_failures = 0
        
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
        
        self.chat = self.client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                tools=self.tools_list,
                temperature=0.1,
                system_instruction=self.system_prompt
            )
        )

    def run(self, task: str):
        print(f"\n[USER TASK]\n{task}\n")
        print("-" * 50)
        
        response = self.chat.send_message(task)
        
        while True:
            if response.function_calls:
                parts = []
                for function_call in response.function_calls:
                    fn_name = function_call.name
                    args = function_call.args
                    
                    # Sanitize arguments for logging
                    log_args = {k: (v if len(str(v)) < 100 else str(v)[:100] + "...") for k, v in args.items()}
                    print(f"\n[ACTION]\nTool: {fn_name}\nArguments: {log_args}")
                    
                    # Execute
                    result = self.execute_tool(fn_name, args)
                    print(f"\n[OBSERVATION]\n{result}")
                    
                    if "Error" in str(result) or "FAILED" in str(result):
                        self.consecutive_failures += 1
                        if self.consecutive_failures >= self.max_retries:
                            result = f"SYSTEM ERROR: Action failed {self.consecutive_failures} consecutive times. You have reached the maximum retry limit. You MUST attempt a different alternative approach, report failure, or use ask_user_for_clarification."
                            print(f"\n[SYSTEM ALERT]\n{result}")
                    else:
                        # Reset failures on successful tool execution
                        self.consecutive_failures = 0
                    
                    if fn_name == "task_complete":
                        print(f"\n[WORKFLOW TERMINATED]\n{result}")
                        return result
                        
                    parts.append(
                        types.Part.from_function_response(
                            name=fn_name,
                            response={"result": result}
                        )
                    )
                
                try:
                    response = self.chat.send_message(parts)
                except Exception as e:
                    print(f"\n[SYSTEM ERROR] LLM Communication failed: {e}")
                    return
            else:
                if response.text:
                    print(f"\n[THOUGHT]\n{response.text.strip()}")
                
                response = self.chat.send_message(
                    "Please use a tool to progress the task, or use task_complete if you have independently verified that the outcome is achieved."
                )

    def execute_tool(self, name: str, args: dict) -> str:
        for tool in self.tools_list:
            if tool.__name__ == name:
                try:
                    return tool(**args)
                except Exception as e:
                    return f"Error executing tool: {type(e).__name__} - {str(e)}"
        return f"Error: Unknown tool {name}"