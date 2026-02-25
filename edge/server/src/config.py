from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    central_server_url: str
    edge_api_key: str

    sync_interval_seconds: int = 300
    frame_skip: int = 5
    detection_threshold: float = 0.363
    attendance_cooldown_minutes: int = 10
    cv_workers: int = 4

    yunet_model_path: str = "models/yunet.onnx"
    sface_model_path: str = "models/sface.onnx"


settings = Settings()
