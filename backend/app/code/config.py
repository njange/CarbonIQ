from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "carbonIQ API"
    MONGODB_URI: str
    MONGODB_DB: str = "carboniQ"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

settings = Settings()