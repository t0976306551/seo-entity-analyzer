from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    serper_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    google_service_account_b64: str = ""
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

settings = Settings()
