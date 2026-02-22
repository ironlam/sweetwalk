from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mapbox_token: str = ""
    data_dir: str = "data"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_prefix": "SWEETWALK_", "env_file": ".env"}


settings = Settings()
