"""Durable prospective paper evidence. Revision 0002, following 0001."""

from pathlib import Path

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

SQL = Path(__file__).resolve().parents[1] / "sql" / revision
TABLES = ("portfolio", "decision", "order", "market_event", "ledger_entry")


def upgrade():
    for name in ("tables", "guards", "financial"):
        op.execute((SQL / f"{name}.sql").read_text())
    for name in TABLES:
        op.execute(f"""
            CREATE TRIGGER paper_guard BEFORE INSERT OR UPDATE OR DELETE ON paper_{name}
            FOR EACH ROW EXECUTE FUNCTION paper_guard_{name}();
            CREATE TRIGGER paper_no_truncate BEFORE TRUNCATE ON paper_{name}
            FOR EACH STATEMENT EXECUTE FUNCTION paper_immutable();
        """)
    for name in ("portfolio", "order", "ledger_entry", "market_event"):
        op.execute(f"""
            CREATE CONSTRAINT TRIGGER paper_commit AFTER INSERT OR UPDATE
            ON paper_{name} DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION paper_check_commit()
        """)


def downgrade():
    op.execute("LOCK TABLE paper_portfolio IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT FROM paper_portfolio) THEN
                RAISE EXCEPTION 'Downgrade refused: paper portfolios exist';
            END IF;
        END $$
    """)
    op.execute("ALTER TABLE paper_portfolio DROP CONSTRAINT paper_state_evidence")
    op.execute("DROP FUNCTION paper_lock(uuid)")
    op.execute("DROP TRIGGER paper_preserve_market ON market")
    op.execute("DROP FUNCTION paper_preserve_market()")
    for name in reversed(TABLES):
        op.execute(f"DROP TABLE paper_{name}")
        op.execute(f"DROP FUNCTION paper_guard_{name}()")
    for function in (
        "paper_project_state()",
        "paper_check_commit()",
        "paper_immutable()",
        "paper_pending(uuid)",
        "paper_latest(uuid)",
        "paper_fee(numeric)",
        "paper_config_text(jsonb)",
    ):
        op.execute(f"DROP FUNCTION {function}")
    for domain in ("instant", "number", "hash", "key"):
        op.execute(f"DROP DOMAIN paper_{domain}")
