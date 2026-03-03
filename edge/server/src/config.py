from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    CENTRAL_SERVER_URL: str
    EDGE_API_KEY: str

    SYNC_INTERVAL_SECONDS: int = 30
    FRAME_SKIP: int = 5
    DETECTION_THRESHOLD: float = 0.45
    ATTENDANCE_COOLDOWN_MINUTES: int = 1
    CV_WORKERS: int = 6

    YUNET_MODEL_PATH: str = "models/yunet.onnx"
    SFACE_MODEL_PATH: str = "models/sface.onnx"

    TOP_K: int = 50
    SCORE_THRESHOLD: float = 0.6
    NMS_THRESHOLD: float = 0.3


settings = Settings()
