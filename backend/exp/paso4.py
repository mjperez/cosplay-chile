from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, text


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str


settings = Settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
print("motor creado, sin abrir conexiones todavia")
print()

with engine.connect() as c:
    print("version:", c.execute(text("SELECT version()")).scalar_one()[:45])

print()
c1 = engine.connect()
print("una abierta:  ", engine.pool.status())
c2 = engine.connect()
print("dos abiertas: ", engine.pool.status())
c1.close()
c2.close()
print("cerradas:     ", engine.pool.status())
