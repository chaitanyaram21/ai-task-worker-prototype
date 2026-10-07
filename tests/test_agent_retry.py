import os
import pytest
from unittest.mock import MagicMock, patch
from agent import AutonomousAgent

class DummyResponse:
    def __init__(self, text="test"):
        self.text = text
        self.function_calls = None

@patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
@patch("agent.genai.Client")
def test_agent_retry_success_after_failure(mock_client, capsys):
    mock_chat = MagicMock()
    mock_client.return_value.chats.create.return_value = mock_chat
    
    # 503, 503, then success
    mock_chat.send_message.side_effect = [
        Exception("503 UNAVAILABLE. High demand"),
        Exception("503 UNAVAILABLE. High demand"),
        DummyResponse("Success")
    ]
    
    agent = AutonomousAgent([], max_retries=3)
    # mock time.sleep so test runs fast
    with patch("time.sleep", return_value=None):
        res = agent.send_message_with_retry("test_task")
        
    assert res is not None
    assert res.text == "Success"
    
    captured = capsys.readouterr().out
    assert "[MODEL RETRY]" in captured
    assert "attempt 2/3" in captured

@patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
@patch("agent.genai.Client")
def test_agent_retry_exhausted(mock_client, capsys):
    mock_chat = MagicMock()
    mock_client.return_value.chats.create.return_value = mock_chat
    
    # 503 infinitely
    mock_chat.send_message.side_effect = Exception("503 UNAVAILABLE")
    
    agent = AutonomousAgent([], max_retries=3)
    with patch("time.sleep", return_value=None):
        res = agent.send_message_with_retry("test_task")
        
    assert res is None
    captured = capsys.readouterr().out
    assert "[MODEL ERROR]" in captured
    assert "after 3 attempts" in captured

@patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
@patch("agent.genai.Client")
def test_agent_config_error(mock_client, capsys):
    mock_chat = MagicMock()
    mock_client.return_value.chats.create.return_value = mock_chat
    
    # 404
    mock_chat.send_message.side_effect = Exception("404 NOT FOUND")
    
    agent = AutonomousAgent([], max_retries=3)
    res = agent.send_message_with_retry("test_task")
        
    assert res is None
    captured = capsys.readouterr().out
    assert "[CONFIGURATION ERROR]" in captured
    assert "MODEL RETRY" not in captured

@patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
@patch("agent.genai.Client")
def test_programmatic_verification_enforcement(mock_client):
    mock_chat = MagicMock()
    mock_client.return_value.chats.create.return_value = mock_chat
    
    agent = AutonomousAgent([], max_retries=3)
    # Force state change
    agent.state_changed = True
    agent.verification_passed = False
    
    # Send a mock task_complete
    from google.genai.types import FunctionCall
    mock_response = MagicMock()
    mock_response.function_calls = [FunctionCall(name="task_complete", args={"summary": "done", "evidence": "none"})]
    mock_chat.send_message.side_effect = [mock_response, DummyResponse("I am stopped")]
    
    agent.run("test")
    # Because verification was not passed, the agent loop prevents task_complete
    # and instead queues a TASK_COMPLETION_REJECTED message to send back.
