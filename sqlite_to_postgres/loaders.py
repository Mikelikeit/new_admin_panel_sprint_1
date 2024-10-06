import sqlite3
import logging
from psycopg import ClientCursor
from dataclasses import dataclass, astuple, fields
from datetime import datetime
from typing import Generator

# models
from models import table_fabric, DifferentColumn

logger = logging.getLogger('JournalDev')
BATCH_SIZE = 100


def _replace_column_name(query: str) -> str:
    """Метод замены имен колонок в sql запросе"""
    upd_q = query
    for replace in DifferentColumn:
        upd_q = upd_q.replace(replace.name, replace.value)
    return upd_q


def extract_data(sqlite_cursor: sqlite3.Cursor,
                 table_name: str, column_names: str) -> Generator[list[sqlite3.Row], None, None]:
    """Метод получения данных из SQLite"""
    query_slt_sqlite = f'SELECT {column_names} FROM {table_name}'

    sqlite_cursor.execute(_replace_column_name(query_slt_sqlite))
    while results := sqlite_cursor.fetchmany(BATCH_SIZE):
        yield results


def _reform_data(row: dict) -> dict:
    """Метод точечного преобразования данных, адаптирование полей SQLite"""
    for name in DifferentColumn:
        if not name.value in row.keys():
            continue
        if isinstance(row[name.value], str):
            row[name.name] = datetime.fromisoformat(row.get(name.value))
        del row[name.value]
    return row


def transform_data(sqlite_cursor: sqlite3.Cursor,
                   table_name: str, column_names: str) -> Generator[list[dataclass], None, None]:
    """Метод трансформации данных из SQLite"""
    for batch in extract_data(sqlite_cursor, table_name, column_names):
        yield [table_fabric[table_name](**_reform_data(dict(row))) for row in batch]


def load_data(sqlite_cursor: sqlite3.Cursor, pg_cursor: ClientCursor, table_name: str) -> None:
    """Основной метод загрузки данных из SQLite в Postgres"""
    pg_column_names = [field.name for field in fields(table_fabric[table_name])]
    column_names_str = ', '.join(pg_column_names)
    placeholder = ', '.join(['%s'] * len(pg_column_names))

    for batch in transform_data(sqlite_cursor, table_name, column_names_str):
        bind_values = ', '.join(
            pg_cursor.mogrify(f'({placeholder})', astuple(item)) for item in batch
        )
        query_insert_to_pg = (f'INSERT INTO content.{table_name} ({column_names_str}) '
                              f'VALUES {bind_values} ON CONFLICT (id) DO NOTHING;')
        try:
            pg_cursor.execute(query_insert_to_pg)
        except Exception as err:
            logger.error(f'Getting exception :: %err', err)
            raise ValueError(f'There are errors when recording to postgres')


def get_all_table_names_sqlite(cursor: sqlite3.Cursor) -> list[str]:
    """Метод получения названий таблиц из SQLite"""
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    cursor.execute(query)
    return sorted([tbl['name'] for tbl in cursor.fetchall()])


def test_transfer(sqlite_cursor: sqlite3.Cursor, pg_cursor: ClientCursor, table: str) -> None:
    """Метод проверки данных после загрузки в Postgres"""
    logger.info(f'Checking table: {table}')
    pg_column_names = [field.name for field in fields(table_fabric[table])]
    column_names_str = ', '.join(pg_column_names)
    query_sqlite = f'SELECT {column_names_str} FROM {table}'
    sqlite_cursor.execute(_replace_column_name(query_sqlite))

    while batch := sqlite_cursor.fetchmany(BATCH_SIZE):
        original_batch = [table_fabric[table](**_reform_data(dict(row))) for row in batch]
        ids = [item.id for item in original_batch]
        pg_cursor.execute(f'SELECT * FROM content.{table} WHERE id = ANY(%s)', [ids])
        transferred_batch = [table_fabric[table](**dict(row)) for row in pg_cursor.fetchall()]

        assert len(original_batch) == len(transferred_batch)
        assert sorted(original_batch, key=lambda item: item.id) == sorted(transferred_batch, key=lambda item: item.id)
    logger.info(f'ok {table}')
