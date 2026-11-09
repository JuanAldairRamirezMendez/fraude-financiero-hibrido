# Base de datos

SQLite + SQLAlchemy 2.0 + Alembic son el default. Usa constraints, indices en filtros/orden, transacciones cortas y WAL. No guardes parquet ni pickles en DB. Abstrae repositorios para migrar a PostgreSQL sin cambiar servicios.
