import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass, astuple, asdict, fields
from datetime import datetime
from typing import Generator
from uuid import UUID

import psycopg
from psycopg import ClientCursor
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DSL = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT')
}

BATCH_SIZE = 100


@dataclass
class DatetimeMixin:
    created: datetime
    modified: datetime


@dataclass
class UUIDMixin:
    id: UUID

    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = UUID(self.id)


@dataclass
class FilmWork(UUIDMixin, DatetimeMixin):
    title: str
    description: str
    creation_date: datetime.date
    rating: float
    type: str


@dataclass
class Genre(UUIDMixin, DatetimeMixin):
    name: str
    description: str


@dataclass
class Person(UUIDMixin, DatetimeMixin):
    full_name: str


@dataclass
class GenreFilmWork(UUIDMixin):
    genre_id: UUID
    film_work_id: UUID
    created: datetime


@dataclass
class PersonFilmWork(UUIDMixin):
    person_id: UUID
    film_work_id: UUID
    role: str
    created: datetime


table_fabric = {
    'film_work': FilmWork,
    'genre': Genre,
    'person': Person,
    'genre_film_work': GenreFilmWork,
    'person_film_work': PersonFilmWork
}


def extract_data(sqlite_cursor: sqlite3.Cursor,
                 table_name: str, column_names: str) -> Generator[list[sqlite3.Row], None, None]:
    query_slt_sqlite = f'SELECT {column_names} FROM {table_name}'
    for replace in (('created', 'created_at'), ('modified', 'updated_at')):
        query_slt_sqlite = query_slt_sqlite.replace(*replace)
    sqlite_cursor.execute(query_slt_sqlite)
    while results := sqlite_cursor.fetchmany(BATCH_SIZE):
        yield results


def transform_data(sqlite_cursor: sqlite3.Cursor,
                   table_name: str, column_names: str) -> Generator[list[dataclass], None, None]:
    for batch in extract_data(sqlite_cursor, table_name, column_names):
        yield [table_fabric[table_name](**dict(row)) for row in batch]


def load_data(sqlite_cursor: sqlite3.Cursor, pg_cursor: psycopg.Cursor, table_name: str) -> None:
    """Основной метод загрузки данных из SQLite в Postgres"""
    pg_column_names = [field.name for field in fields(table_fabric[table_name])]
    miss = ['created_at', 'updated_at']
    column_names_str = ','.join(pg_column_names)
    col_count = ', '.join(['%s'] * len(pg_column_names))

    for batch in transform_data(sqlite_cursor, table_name, column_names_str):
        query_insert_to_pg = (f'INSERT INTO content.{table_name} ({column_names_str}) '
                              f'VALUES ({col_count}) ON CONFLICT (id) DO NOTHING;')
        batch_as_tuples = [astuple(student) for student in batch]
        pg_cursor.executemany(query_insert_to_pg, batch_as_tuples)


def get_all_table_names_sqlite(cursor: sqlite3.Cursor) -> list[str]:
    """Метод получения названий таблиц из SQLite"""
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    cursor.execute(query)
    return [tbl['name'] for tbl in cursor.fetchall()]


if __name__ == '__main__':
    with closing(sqlite3.connect(os.getenv('SQLITE_PATH'))) as sqlite_conn, closing(psycopg.connect(
            **DSL, row_factory=dict_row, cursor_factory=ClientCursor)) as pg_conn:

        sqlite_conn.row_factory = sqlite3.Row

        with closing(sqlite_conn.cursor()) as sqlite_cur, closing(pg_conn.cursor(row_factory=dict_row)) as pg_cur:

            table_names_sqlite = get_all_table_names_sqlite(sqlite_cur)

            if not table_names_sqlite:
                raise ValueError('В SQLite не было найдено ни одной таблицы для миграции')
            for tbl_name in table_names_sqlite:
                load_data(sqlite_cur, pg_cur, tbl_name)
                exit(22)
