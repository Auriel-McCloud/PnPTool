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

    # Mistral AI ("La Plateforme", api.mistral.ai) — Alternative zu Gemini,
    # z.B. wenn das Gemini-Kontingent aufgebraucht ist. Kein Google-Konto nötig.
    mistral_api_key: str = ""
    mistral_model: str = "mistral-small-latest"

    # Welcher KI-Anbieter für die Ideenschmiede/KI-Generierung aktiv ist:
    # "gemini" oder "mistral". Umschaltbar ohne Code-Änderung.
    ki_provider: str = "gemini"

    # Spotify Web API — globale Anbindung (ein Konto fürs ganze Tool, nicht
    # pro Kampagne). client_id/secret kommen aus dem Spotify-Dashboard, die
    # eigentliche Nutzerverbindung (Refresh-Token) liegt in Neo4j
    # (SpotifyKonto-Knoten, siehe app/spotify/repository.py), nicht hier —
    # sie entsteht erst durch den Verbinden-Knopf in der Oberflaeche.
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    # Muss exakt mit der im Spotify-Dashboard eingetragenen Redirect-URI
    # uebereinstimmen. Spotify verlangt seit 2025 eine explizite Loopback-IP
    # statt "localhost" — deshalb 127.0.0.1, nicht localhost.
    spotify_redirect_uri: str = "http://127.0.0.1:8001/api/spotify/callback"
    # Wohin nach dem Spotify-Login zurueckgeleitet wird (das Frontend, nicht
    # die API). Fuer Marks Standard-Setup der Vite-Dev-Server.
    frontend_base_url: str = "http://localhost:5173"

    cors_origins: list[str] = ["http://localhost:5173", "http://192.168.178.21:5173"]


settings = Settings()
