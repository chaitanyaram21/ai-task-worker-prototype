from google import genai
from google.genai import types

class AutonomousAgent:
    def __init__(self, tools_list, model_name="gemini-3.8-flash"):
        self.client = genai.Client()
        self.tools_list = tools_list
        
        # We use a persistent chat session to maintain context across multiple steps
        self.chat = self.client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                tools=self.tools_list,
                temperature=0.1,  # Low temperature for more deterministic, logical actions
                system_instruction=(
                    "You are an autonomous AI task worker. "
                    "Your job is to understand the user's end goal and achieve it by taking a sequence of actions. "
                    "You have access to a set of tools. Observe the result of each action and decide what to do next. "
                    "If a tool fails, analyze the error and try a reasonable alternative. "
                    "Once you have verified the goal is achieved, you MUST call the 'task_complete' tool with a summary."
                )
            )
        )

    def run(self, task: str):
        print(f"\n[Agent] Received Task: {task}\n")
        print("-" * 50)
        
        response = self.chat.send_message(task)
        
        while True:
            # If the LLM decides to take an action, it will return function_calls
            if response.function_calls:
                parts = []
                for function_call in response.function_calls:
                    fn_name = function_call.name
                    args = function_call.args
                    
                    print(f"🔄 [Action] Calling {fn_name} with args: {args}")
                    
                    # Execute the tool locally
                    result = self.execute_tool(fn_name, args)
                    print(f"👁️  [Observation] {result}\n")
                    
                    # Terminate if the agent called the completion tool
                    if fn_name == "task_complete":
                        print(f"✅ [Workflow Terminated]")
                        return result
                        
                    # Prepare the tool result to send back to the LLM
                    parts.append(
                        types.Part.from_function_response(
                            name=fn_name,
                            response={"result": result}
                        )
                    )
                # Send the observation back so the LLM can decide the next step
                response = self.chat.send_message(parts)
            else:
                # If the model just talks without acting, nudge it to use tools
                print(f"💭 [Thought/Message]: {response.text}\n")
                response = self.chat.send_message(
                    "Please use a tool to progress the task, or use task_complete if you are finished."
                )

    def execute_tool(self, name: str, args: dict) -> str:
        for tool in self.tools_list:
            if tool.__name__ == name:
                try:
                    return tool(**args)
                except Exception as e:
                    return f"Error executing tool: {e}"
        return f"Unknown tool: {name}"