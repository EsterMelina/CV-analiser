"""Development helper: freeze the original schema without operational access."""
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
os.environ.update(ENVIRONMENT="test", DATABASE_URL="sqlite:///:memory:")
from sqlalchemy import create_engine
from alembic.autogenerate import produce_migrations, render_python_code
from alembic.migration import MigrationContext
from app.core.database import Base
from app import models

with create_engine("sqlite:///:memory:").connect() as connection:
    migration = produce_migrations(MigrationContext.configure(connection), Base.metadata)
    source = '''"""Original schema frozen before tenant and session changes."""
from alembic import op
import sqlalchemy as sa
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
'''
    source += render_python_code(migration.upgrade_ops) + "\n\ndef downgrade():\n"
    source += '    raise RuntimeError("Restore the pre-migration backup; baseline downgrade would destroy data.")\n'
    destination = root / "backend/migrations/versions/0001_baseline.py"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise RuntimeError("Baseline already frozen")
    destination.write_text(source, encoding="utf-8")
