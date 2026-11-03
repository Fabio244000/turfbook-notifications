from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    # A Lambda execution environment handles one invocation at a time, so one
    # connection is enough; it also caps connections to the shared RDS at one per
    # environment.
    db_pool_size: int = 1
    db_max_overflow: int = 0
    # Replaces connections that went stale while the environment was idle.
    db_pool_pre_ping: bool = True
    ses_sender: str
    ses_region: str = 'us-east-1'
    ses_timeout_seconds: float = 1.0
    dlq_url: str
    dlq_timeout_seconds: float = 1.0
    # Region of the service's own resources (the DLQ); Lambda sets AWS_REGION.
    aws_region: str = 'us-east-1'
    api_prefix: str = '/api'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()
