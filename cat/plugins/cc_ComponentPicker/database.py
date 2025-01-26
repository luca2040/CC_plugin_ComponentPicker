from typing import List
import sqlite3
import json


def get_table_types(db_path: str, index_table: str) -> List[any]:
    """Returns the table types from the index table."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT Table_name, Table_type FROM {index_table}")
    table_types = cursor.fetchall()

    conn.close()

    return table_types


def get_DB_tables_ddl(db_path: str, data_tables: List[str]) -> dict:
    """Get the DLL of the specified tables."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        f"""SELECT name FROM sqlite_master WHERE type='table' AND name IN ({
            ", ".join("?" for _ in data_tables)});""",
        data_tables,
    )

    tab_names = cursor.fetchall()
    DDLs = {}

    for db_table_name in tab_names:
        table_name = db_table_name[0]

        cursor.execute(
            f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?;",
            (table_name,),
        )

        ddl = cursor.fetchone()[0]
        DDLs[table_name] = ddl

    conn.close()

    return DDLs


def get_units_per_table(
    db_path: str,
    columns_metadata_table_name: str,
    units_map_table_name: str,
    units_table_name: str,
    index_table: str,
) -> dict:
    """Returns the measurement units divided by table"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        f"""SELECT u.Unit, t.Table_name, c.Column_name
                    FROM {units_map_table_name} um
                    JOIN {units_table_name} u ON um.Unit_ID = u.ID
                    JOIN {index_table} t ON um.Table_ID = t.ID
                    JOIN {columns_metadata_table_name} c ON um.Column_ID = c.ID;"""
    )

    units_fetch = cursor.fetchall()

    meas_units = {}
    for unit, table, column in units_fetch:
        if table not in meas_units:
            meas_units[table] = []
        meas_units[table].append({column: unit})

    conn.close()
    return meas_units


def query_db_json(db_path: str, query: str) -> str | None:
    """Execute the query on the DB and return the results as a JSON string"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(query)

    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append(dict(zip(columns, row)))

    json_response = json.dumps(result)

    conn.close()

    return json_response if result else None


def get_data_list(db_path: str, table_name: str) -> List[dict]:
    """Get all the data from a table"""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    data = [dict(row) for row in rows]

    conn.close()

    return data
