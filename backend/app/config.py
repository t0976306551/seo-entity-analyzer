from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    serper_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    google_service_account_b64: str = ""
    frontend_url: str = "http://localhost:3000"
    google_client_id: str = ""
    google_client_secret: str = ""

settings = Settings()
