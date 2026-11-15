import os
import secrets
from pathlib import Path

env_file = Path(".env")
if not env_file.exists():
    contents = (
        "APP_ENV=development\n"
        "SQLITE_PATH=./data/offline.db\n"
        f"DEV_AUTH_SECRET={secrets.token_urlsafe(48)}\n"
        f"OFFLINE_GRANT_SECRET={secrets.token_urlsafe(48)}\n"
        "CORS_ORIGINS=http://localhost:5173\n"
        "ALLOW_DEMO_RULES=false\n"
    )
    with env_file.open("x", encoding="utf-8") as handle:
        handle.write(contents)
    os.chmod(env_file, 0o600)

for line in env_file.read_text(encoding="utf-8").splitlines():
    if line.strip() and not line.lstrip().startswith("#"):
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip())

from app.auth.dependencies import issue_development_token
from app.core.config import Settings
import uvicorn

settings = Settings()
settings.validate()
token = issue_development_token(
    settings, "developer", ["admin"], ["DEMO-01", "DEMO-02"]
)

print("\nDevelopment token:\n" + token)
print("\nAPI documentation: http://127.0.0.1:8000/docs")
print("In Swagger, click Authorize and paste the token alone.\n")

uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
