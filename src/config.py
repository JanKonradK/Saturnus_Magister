from pydantic_settings import BaseSettings
from pydantic import Field
from enum import Enum

class Environment(str, Enum):
    LOCAL = "local"
    DOCKER = "docker"
    AWS = "aws"
    GCP = "gcp"

class Settings(BaseSettings):
    environment: Environment = Environment.DOCKER

    # Database (shared with DeepApply)
    database_url: str = Field(..., validation_alias="DATABASE_URL")

    # Gmail
    gmail_credentials_path: str = "credentials.json"
    gmail_token_path: str = "token.pickle"
    gmail_scopes: list[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.compose",
    ]

    # AI Agent (OpenAI-compatible API)
    agent_api_key: str = Field(..., validation_alias="AGENT_API_KEY")
    agent_model: str = "grok-4-1-fast-reasoning"
    agent_base_url: str = "https://api.x.ai/v1"

    # TickTick
    ticktick_access_token: str = Field(..., validation_alias="TICKTICK_ACCESS_TOKEN")
    ticktick_client_id: str = Field(..., validation_alias="TICKTICK_CLIENT_ID")
    ticktick_client_secret: str = Field(..., validation_alias="TICKTICK_CLIENT_SECRET")

    # TickTick Projects (Eisenhower Matrix)
    ticktick_q1_project: str = Field(..., validation_alias="TICKTICK_Q1_PROJECT")
    ticktick_q2_project: str = Field(..., validation_alias="TICKTICK_Q2_PROJECT")
    ticktick_q3_project: str = Field(..., validation_alias="TICKTICK_Q3_PROJECT")
    ticktick_q4_project: str = Field(..., validation_alias="TICKTICK_Q4_PROJECT")
    ticktick_work_project: str = Field(..., validation_alias="TICKTICK_WORK_PROJECT")

    # Matching thresholds
    auto_match_threshold: float = 0.85
    review_threshold: float = 0.50

    # Processing
    poll_interval_seconds: int = 300
    max_concurrent_emails: int = 8  # For free-threaded parallelism

    # Future: Auto-reply
    enable_auto_reply: bool = False
    auto_reply_confidence_threshold: float = 0.95

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

settings = Settings()
