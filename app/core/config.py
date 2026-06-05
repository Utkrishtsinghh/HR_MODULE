from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "UTK AI HR"
    database_url: str = "sqlite:///./data/app.db"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    gemini_api_key: str = ""
    frontend_base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
