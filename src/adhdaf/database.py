# ABOUTME: Async SQLAlchemy engine, session factory, and migration runner.
# ABOUTME: Applies .sql migration files on startup, tracks which have already run.
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from adhdaf.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session():
    async with async_session() as session:
        yield session


async def run_migrations():
    migrations_dir = Path(__file__).parent / "migrations"
    if not migrations_dir.exists():
        return

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: sync_conn.execute(
                __import__("sqlalchemy").text(
                    "CREATE TABLE IF NOT EXISTS schema_migrations "
                    "(name TEXT PRIMARY KEY, applied_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
                )
            )
        )

        applied = await conn.run_sync(
            lambda sync_conn: {
                row[0]
                for row in sync_conn.execute(
                    __import__("sqlalchemy").text("SELECT name FROM schema_migrations")
                ).fetchall()
            }
        )

        for migration_file in sorted(migrations_dir.glob("*.sql")):
            if migration_file.name in applied:
                continue
            sql = migration_file.read_text()
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement:
                    await conn.run_sync(
                        lambda sync_conn, s=statement: sync_conn.execute(
                            __import__("sqlalchemy").text(s)
                        )
                    )
            await conn.run_sync(
                lambda sync_conn, name=migration_file.name: sync_conn.execute(
                    __import__("sqlalchemy").text(
                        "INSERT INTO schema_migrations (name) VALUES (:name)"
                    ),
                    {"name": name},
                )
            )
