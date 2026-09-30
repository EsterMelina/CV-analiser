from alembic import op
import sqlalchemy as sa
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("applications", sa.Column("analysis_status", sa.String(30), nullable=False, server_default="pending"))
    op.execute("UPDATE applications SET analysis_status='completed' WHERE score IS NOT NULL")


def downgrade():
    op.drop_column("applications", "analysis_status")
