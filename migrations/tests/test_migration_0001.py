"""Tests for the 0001_initial_schema Alembic migration (structure only, no DB needed)."""

import importlib.util
import os
import pytest


def _load_migration():
    """Load the migration module via importlib (filename starts with a digit)."""
    versions_dir = os.path.join(os.path.dirname(__file__), "..", "versions")
    path = os.path.join(versions_dir, "0001_initial_schema.py")
    spec = importlib.util.spec_from_file_location("migration_0001", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def migration():
    return _load_migration()


# ── Revision metadata ──────────────────────────────────────────────────────────

class TestRevisionMetadata:
    def test_revision_id(self, migration):
        assert migration.revision == "0001"

    def test_no_parent_revision(self, migration):
        assert migration.down_revision is None

    def test_no_branch_labels(self, migration):
        assert migration.branch_labels is None

    def test_no_depends_on(self, migration):
        assert migration.depends_on is None


# ── Callable guards ────────────────────────────────────────────────────────────

class TestCallables:
    def test_upgrade_is_callable(self, migration):
        assert callable(migration.upgrade)

    def test_downgrade_is_callable(self, migration):
        assert callable(migration.downgrade)


# ── upgrade() inspects the expected operations ────────────────────────────────
# We run upgrade() with a mock Alembic `op` object to capture what tables/indexes
# it tries to create — no real database is touched.

class _OpRecorder:
    """Captures op.create_table and op.create_index calls."""

    def __init__(self):
        self.tables_created = []
        self.indexes_created = []
        self.executed_sql = []

    def create_table(self, name, *cols, **kw):
        self.tables_created.append(name)

    def create_index(self, name, table, cols, **kw):
        self.indexes_created.append((name, table))

    def execute(self, sql):
        self.executed_sql.append(str(sql))


@pytest.fixture
def op_recorder(migration, monkeypatch):
    recorder = _OpRecorder()
    monkeypatch.setattr(migration, "op", recorder)
    migration.upgrade()
    return recorder


class TestUpgradeOperations:
    def test_creates_organizations_table(self, op_recorder):
        assert "organizations" in op_recorder.tables_created

    def test_creates_projects_table(self, op_recorder):
        assert "projects" in op_recorder.tables_created

    def test_creates_users_table(self, op_recorder):
        assert "users" in op_recorder.tables_created

    def test_creates_api_keys_table(self, op_recorder):
        assert "api_keys" in op_recorder.tables_created

    def test_creates_four_tables_total(self, op_recorder):
        assert len(op_recorder.tables_created) == 4

    def test_creates_projects_org_id_index(self, op_recorder):
        index_names = [name for name, _ in op_recorder.indexes_created]
        assert "idx_projects_org_id" in index_names

    def test_creates_users_org_id_index(self, op_recorder):
        index_names = [name for name, _ in op_recorder.indexes_created]
        assert "idx_users_org_id" in index_names

    def test_creates_users_email_index(self, op_recorder):
        index_names = [name for name, _ in op_recorder.indexes_created]
        assert "idx_users_email" in index_names

    def test_creates_api_keys_user_id_index(self, op_recorder):
        index_names = [name for name, _ in op_recorder.indexes_created]
        assert "idx_api_keys_user_id" in index_names

    def test_creates_api_keys_hashed_key_index(self, op_recorder):
        index_names = [name for name, _ in op_recorder.indexes_created]
        assert "idx_api_keys_hashed_key" in index_names

    def test_creates_six_indexes_total(self, op_recorder):
        assert len(op_recorder.indexes_created) == 6

    def test_executes_pgcrypto_extension(self, op_recorder):
        assert any("pgcrypto" in sql for sql in op_recorder.executed_sql)

    def test_executes_user_role_enum(self, op_recorder):
        assert any("user_role" in sql for sql in op_recorder.executed_sql)


class TestDowngradeOperations:
    """downgrade() must drop tables in the correct reverse-dependency order."""

    def test_downgrade_drops_api_keys_before_users(self, migration, monkeypatch):
        drop_order = []

        class DropRecorder:
            def drop_table(self, name, **kw):
                drop_order.append(name)

            def execute(self, sql):
                pass

        monkeypatch.setattr(migration, "op", DropRecorder())
        migration.downgrade()

        assert drop_order.index("api_keys") < drop_order.index("users")

    def test_downgrade_drops_users_before_organizations(self, migration, monkeypatch):
        drop_order = []

        class DropRecorder:
            def drop_table(self, name, **kw):
                drop_order.append(name)

            def execute(self, sql):
                pass

        monkeypatch.setattr(migration, "op", DropRecorder())
        migration.downgrade()

        assert drop_order.index("users") < drop_order.index("organizations")

    def test_downgrade_drops_projects_before_organizations(self, migration, monkeypatch):
        drop_order = []

        class DropRecorder:
            def drop_table(self, name, **kw):
                drop_order.append(name)

            def execute(self, sql):
                pass

        monkeypatch.setattr(migration, "op", DropRecorder())
        migration.downgrade()

        assert drop_order.index("projects") < drop_order.index("organizations")

    def test_downgrade_drops_all_four_tables(self, migration, monkeypatch):
        dropped = []

        class DropRecorder:
            def drop_table(self, name, **kw):
                dropped.append(name)

            def execute(self, sql):
                pass

        monkeypatch.setattr(migration, "op", DropRecorder())
        migration.downgrade()

        assert set(dropped) == {"organizations", "projects", "users", "api_keys"}

    def test_downgrade_drops_user_role_enum(self, migration, monkeypatch):
        executed = []

        class DropRecorder:
            def drop_table(self, name, **kw):
                pass

            def execute(self, sql):
                executed.append(str(sql))

        monkeypatch.setattr(migration, "op", DropRecorder())
        migration.downgrade()

        assert any("user_role" in sql for sql in executed)
