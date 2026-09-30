"""Generate a reviewable revision against migrations in an isolated memory DB."""
import os
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
os.environ.update(ENVIRONMENT="test", DATABASE_URL="sqlite:///:memory:")
from sqlalchemy import create_engine
from alembic import command
from alembic.autogenerate import produce_migrations, render_python_code
from alembic.migration import MigrationContext
from app.core.database import Base
from app import models
from app.migrate import config

revision, previous = sys.argv[1:3]
target = root / f"backend/migrations/versions/{revision}_domain.py"
if target.exists():
    raise RuntimeError("Revision already exists")
with create_engine("sqlite:///:memory:").begin() as connection:
    command.upgrade(config(connection), "head")
    migration = produce_migrations(MigrationContext.configure(connection), Base.metadata)
    source = f'from alembic import op\nimport sqlalchemy as sa\nrevision = "{revision}"\ndown_revision = "{previous}"\nbranch_labels = None\ndepends_on = None\n\ndef upgrade():\n'
    source += render_python_code(migration.upgrade_ops).replace("sa.text('now()')", 'sa.func.now()').replace("sa.text('(CURRENT_TIMESTAMP)')", 'sa.func.now()')
    source += '\n\ndef downgrade():\n    raise RuntimeError("Restore backup to preserve history")\n'
    target.write_text(source, encoding="utf-8")
