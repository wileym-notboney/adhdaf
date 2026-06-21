# ABOUTME: Async SQLAlchemy engine, session factory, and migration runner.
# ABOUTME: Applies .sql migration files on startup, tracks which have already run.
from pathlib import Path

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from adhdaf.config import settings


def create_app_engine(url: str | None = None, echo: bool = False):
    eng = create_async_engine(url or settings.database_url, echo=echo)

    @event.listens_for(eng.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return eng


engine = create_app_engine()
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session():
    async with async_session() as session:
        yield session


def ensure_db_directory():
    url = settings.database_url
    if "sqlite" in url:
        parts = url.split("///", 1)
        if len(parts) == 2 and parts[1]:
            Path(parts[1]).parent.mkdir(parents=True, exist_ok=True)


async def run_migrations(eng=None):
    if eng is None:
        eng = engine

    migrations_dir = Path(__file__).parent / "migrations"
    if not migrations_dir.exists():
        return

    async with eng.begin() as conn:
        await conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(name TEXT PRIMARY KEY, applied_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
            )
        )

        result = await conn.execute(text("SELECT name FROM schema_migrations"))
        applied = {row[0] for row in result.fetchall()}

        for migration_file in sorted(migrations_dir.glob("*.sql")):
            if migration_file.name in applied:
                continue
            sql = migration_file.read_text()
            for statement in sql.split(";"):
                stmt = statement.strip()
                if stmt:
                    await conn.execute(text(stmt))
            await conn.execute(
                text("INSERT INTO schema_migrations (name) VALUES (:name)"),
                {"name": migration_file.name},
            )
