import os
import pytest
from pathlib import Path
import tools

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path):
    # Setup safe temp DB for tests
    test_db = tmp_path / "test.db"
    tools.DB_PATH = str(test_db)
    
    # Overwrite tool global dirs to point to temp dir for isolation
    tools.ROOT_DIR = tmp_path
    tools.DATA_DIR = tmp_path / "data"
    tools.OUTPUT_DIR = tools.DATA_DIR / "output"
    
    tools.DATA_DIR.mkdir(parents=True, exist_ok=True)
    tools.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Init DB
    tools.init_db(str(test_db))
    
    yield tmp_path
