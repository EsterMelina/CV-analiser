from alembic import op
import sqlalchemy as sa
revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("criteria_version", sa.Integer(), nullable=False, server_default="1"))
    with op.batch_alter_table("candidate_matches") as batch:
        batch.add_column(sa.Column("criteria_version", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("resume_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_match_resume", "resumes", ["resume_id"], ["id"])
    op.create_table("criteria_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "version", name="uq_criteria_version"))


def downgrade():
    raise RuntimeError("Restaurar backup para preservar histórico de critérios")
