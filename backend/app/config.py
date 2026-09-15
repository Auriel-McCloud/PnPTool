from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    # Google Gemini API Key (generativelanguage.googleapis.com). Kommt aus der
    # .env, damit er nie ins Repository gelangt.
    gemini_api_key: str = ""
    # Welches Gemini-Modell für KI-Generierung genutzt wird. "flash" reicht
    # für Text; bei Bedarf auf "pro" wechseln (z.B. gemini-3.8-flash o.ä.).
    gemini_model: str = "gemini-3.6-flash"

    cors_origins: list[str] = ["http://localhost:5173", "http://192.168.178.21:5173"]


settings = Settings()
