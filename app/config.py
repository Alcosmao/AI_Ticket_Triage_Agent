import os
from dotenv import load_dotenv

load_dotenv()

USE_MOCK: bool = os.getenv("USE_MOCK", "true").lower() == "true"

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME: str = "gpt-5.4-mini"
MAX_TOKENS = 1500

MAX_AGENT_STEPS: int = 3

OUTPUTS_DIR: str = "outputs"

