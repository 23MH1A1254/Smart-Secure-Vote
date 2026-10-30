import os

APP_ENV = os.getenv("APP_ENV", "local")
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
JWT_SECRET = os.getenv("JWT_SECRET", "local-demo-secret-change-this")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeMe-Demo-123")
EXPOSE_DEMO_OTP = os.getenv("EXPOSE_DEMO_OTP", "true").lower() == "true"
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "true").lower() == "true"
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
