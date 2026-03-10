"""Helper to run pytest from the correct working directory on Windows."""
import os
import sys
import pathlib

# Change to the project root before pytest collects anything
os.chdir(pathlib.Path(__file__).parent)

import pytest
sys.exit(pytest.main(["test/tests.py", "-v", "--tb=short"]))
