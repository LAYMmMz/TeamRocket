"""Non-destructive installer for TeamRocket team SQLite auto-reconciliation."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "app" / "main.py"
SOURCE = ROOT / "team_sqlite_integration.py"
if not TARGET.is_file() or not SOURCE.is_file():
    raise SystemExit("Copy this installer and team_sqlite_integration.py into Developer1_Backend/backend first")

code = TARGET.read_text(encoding="utf-8")
if 'TeamRocket SQLite automatic reconciliation' in code:
    print("Already installed. No changes made.")
    raise SystemExit(0)

# The existing app.main creates Store in lifespan and closes it in finally.
# Make only two carefully anchored inserts: no replacement of API routes.
BEFORE = "        try:\n            yield\n        finally:\n"
AFTER = '''        # TeamRocket SQLite automatic reconciliation (development only).
        mirror_stop = asyncio.Event()
        mirror_task = None
        if settings.environment == "development":
            from team_sqlite_integration import integration_ready, reconcile
            if integration_ready():
                async def mirror_loop():
                    while not mirror_stop.is_set():
                        try:
                            await asyncio.to_thread(reconcile, app.state.store)
                        except Exception as exc:
                            logging.getLogger(__name__).warning(
                                "Team SQLite reconciliation failed: %s",
                                type(exc).__name__,
                            )
                        try:
                            await asyncio.wait_for(mirror_stop.wait(), timeout=10.0)
                        except TimeoutError:
                            pass
                mirror_task = asyncio.create_task(mirror_loop())

        try:
            yield
        finally:
'''
BEFORE_CLOSE = "        finally:\n            stop.set()\n"
AFTER_CLOSE = '''        finally:
            mirror_stop.set()
            if mirror_task is not None:
                await mirror_task
            stop.set()
'''

# Windows and Unix line endings both supported without altering layout.
newline = "\r\n" if "\r\n" in code else "\n"
normalized = code.replace("\r\n", "\n")
if normalized.count(BEFORE) != 1 or normalized.count(BEFORE_CLOSE) != 1:
    raise SystemExit("Unexpected app/main.py layout. No files changed. Share your main.py for a safe patch.")
patched = normalized.replace(BEFORE, AFTER, 1).replace(BEFORE_CLOSE, AFTER_CLOSE, 1)
backup = TARGET.with_name("main.before_team_sqlite_integration.py.bak")
if backup.exists():
    raise SystemExit(f"Backup already exists at {backup}; no changes made")
shutil.copy2(TARGET, backup)
TARGET.write_text(patched.replace("\n", newline), encoding="utf-8")
print("Integration installed into app/main.py")
print("Backup:", backup)
print("Source store remains offline.db; teammate's SQLite is an automatic projection")
