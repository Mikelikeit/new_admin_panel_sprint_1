import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass, astuple, asdict, fields
from datetime import datetime
from typing import Generator
from uuid import UUID
from enum import Enum

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

    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = UUID(self.id)
        if isinstance(self.genre_id, str):
            self.genre_id = UUID(self.genre_id)
        if isinstance(self.film_work_id, str):
            self.film_work_id = UUID(self.film_work_id)


@dataclass
class PersonFilmWork(UUIDMixin):
    person_id: UUID
    film_work_id: UUID
    role: str
    created: datetime

    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = UUID(self.id)
        if isinstance(self.person_id, str):
            self.person_id = UUID(self.person_id)
        if isinstance(self.film_work_id, str):
            self.film_work_id = UUID(self.film_work_id)


table_fabric = {
    'film_work': FilmWork,
    'genre': Genre,
    'person': Person,
    'genre_film_work': GenreFilmWork,
    'person_film_work': PersonFilmWork
}


class DifferentColumn(Enum):
    created = 'created_at'
    modified = 'updated_at'


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


def test_transfer(sqlite_cursor: sqlite3.Cursor, pg_cursor: ClientCursor, table: str) -> None:
    """Метод проверки данных после загрузки в Postgres"""
    print(f'Проверка таблицы {table}')
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
    print(f'ok {table}')


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
        pg_cursor.execute(query_insert_to_pg)


def get_all_table_names_sqlite(cursor: sqlite3.Cursor) -> list[str]:
    """Метод получения названий таблиц из SQLite"""
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    cursor.execute(query)
    return sorted([tbl['name'] for tbl in cursor.fetchall()])


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
                pg_conn.commit()
                print(f'Таблица {tbl_name} залита')
                test_transfer(sqlite_cur, pg_cur, tbl_name)
