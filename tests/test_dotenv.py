import os
from unittest.mock import patch
from qa_bot import config
import importlib

def test_dotenv_loading(tmp_path, monkeypatch):
    """Verify that load_dotenv is called and loads variables from a file."""
    # Create a dummy .env file in the temp directory
    env_file = tmp_path / ".env"
    env_file.write_text("LLM_API_KEY=file-secret-key\nTEST_VAR=exists")
    
    # We need to re-import or re-load the config module to trigger load_dotenv
    # in the context of the current directory being tmp_path
    monkeypatch.chdir(tmp_path)
    
    # Patch load_dotenv in the module where it is used
    with patch("dotenv.load_dotenv") as mock_load:
        importlib.reload(config)
        assert mock_load.called

    # Since config.llm_api_key() just calls os.environ.get, 
    # we can verify it returns the value from our dummy file 
    # if we manually trigger load_dotenv or mock the environment.
    # Actually, importlib.reload(config) above already called the real load_dotenv 
    # (if not patched) or the mock. 
    
    # Let's do a clean run with the real load_dotenv
    # Ensure variables are not already in environment
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("TEST_VAR", raising=False)
    
    importlib.reload(config)
    # Note: load_dotenv() from config.py will look for .env in current working dir
    assert os.environ.get("TEST_VAR") == "exists"
    assert os.environ.get("LLM_API_KEY") == "file-secret-key"
