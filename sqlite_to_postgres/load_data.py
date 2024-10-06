import os
import sqlite3
import logging.config
from contextlib import closing

import psycopg
from psycopg import ClientCursor
from psycopg.rows import dict_row
from dotenv import load_dotenv

# loaders
from loaders import get_all_table_names_sqlite, load_data, test_transfer

load_dotenv()
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('JournalDev')

DSL = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT')
}


def main() -> None:
    with closing(sqlite3.connect(os.getenv('SQLITE_PATH'))) as sqlite_conn, closing(psycopg.connect(
            **DSL, row_factory=dict_row, cursor_factory=ClientCursor)) as pg_conn:

        sqlite_conn.row_factory = sqlite3.Row

        with closing(sqlite_conn.cursor()) as sqlite_cur, closing(pg_conn.cursor(row_factory=dict_row)) as pg_cur:
            table_names_sqlite = get_all_table_names_sqlite(sqlite_cur)
            if not table_names_sqlite:
                logger.error('SQLite. Not found tables for migration')
                raise ValueError('SQLite. Not found tables for migration')
            for tbl_name in table_names_sqlite:
                load_data(sqlite_cur, pg_cur, tbl_name)
                pg_conn.commit()
                logger.info(f'Migrate table {tbl_name} is finished')
                test_transfer(sqlite_cur, pg_cur, tbl_name)



if __name__ == '__main__':
    main()
