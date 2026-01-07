import sys
from pathlib import Path

# זה הקובץ conftest.py נמצא ב: PII_Detection_System/tests
# parents[1] => PII_Detection_System
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))