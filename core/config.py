"""
Configuration management for Arooba-AIOps.
Loads environment variables with intelligent fallbacks.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    TELEMETRY_SOURCE: str = os.getenv("TELEMETRY_SOURCE", "simulated").lower()
    EDGE_AP_HOST: str = os.getenv("EDGE_AP_HOST", "http://192.168.4.1:8000")
    EDGE_AP_TIMEOUT_SEC: float = float(os.getenv("EDGE_AP_TIMEOUT_SEC", "5.0"))

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock").lower()

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")


config = Config()
