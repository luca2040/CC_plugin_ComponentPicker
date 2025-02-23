from typing import List, Tuple
from cat.plugins.cc_ComponentPicker.database import (
    get_table_types,
    get_units_per_table,
    get_DB_tables_ddl,
)

import json


def get_needed_tables(
    llm, query: str, db_path: str, index_table: str
) -> Tuple[List[str], str, str]:
    """Returns the list of tables that need to be used to extract the data specified by the query from the DB."""

    db_structure, table_names = get_structure(db_path, index_table)

    llm_query = f"""Respond with a JSON list containing the names of SQLite tables needed to extract requested electrical components from a database.
Tables only contain components categorized by the title, except for general categories like microcontrollers or integrated circuits.
Use ONLY given tables in the structure to find data.
REQUEST:
{query}
DATABASE STRUCTURE:
{db_structure}"""

    llm_response = llm.llm(
        llm_query,
        format={
            "type": "array",
            "items": {"type": "string"},
        },
    )

    return json.loads(llm_response), table_names, db_structure


def get_db_query(
    llm,
    query: str,
    db_structure: str,
    db_path: str,
    index_table: str,
    tables: List[str],
    unit_tables: List[str],
    use_units: bool,
) -> Tuple[str, str]:
    """Returns an SQLite query that extracts from the DB the data specified in the query.
    The database structure is needed to tell the LLM to generate the query based on that structure.
    """

    units = ""
    if use_units:
        units = "MEASUREMENT UNITS:\n"
        units += get_units_for_tables(db_path, tables, index_table, unit_tables)

    llm_query = f"""Respond with an SQLite query to extract requested components from a database.
When searching for TEXT use the LIKE comparator instead of =
ALWAYS Use ID references to other tables indicated in the foreign keys when possible, and NEVER make the query return the ID itself but the value it points to unless specificately stated.
Use ONLY given tables in the structure to find data, if there is not what the user requestet make an SQLite query that returns no data.
Always include a 15 rows limit for the output and order by relevant data asked by the user, ONLY if not asked to find a maximum or minimum value, if so then use the respective functions to get only that value.
REQUEST:
{query}
DATABASE STRUCTURE:
{db_structure}
{units}"""

    llm_response = llm.llm(
        llm_query,
        format={
            "type": "object",
            "properties": {
                "SQL_query": {"type": "string"},
            },
            "required": ["SQL_query"],
        },
    )

    result = json.loads(llm_response)["SQL_query"]

    return result, units


def get_tables(
    db_path: str, index_table: str
) -> Tuple[List[str], List[str], List[str], bool]:
    """Returns the list of tables in the DB, divided by the type specified in the index table."""

    table_types = get_table_types(db_path, index_table)

    data_tables = []
    advanced_tables = []

    unit_tables = [None for _ in range(3)]
    # 0: columns_metadata_table_name
    # 1: units_map_table_name
    # 2: units_table_name

    # Table types
    # |ID |Description                |
    # |---|---------------------------|
    # |0  |Main index table           |
    # |1  |Table function descriptions|
    # |2  |Columns index table        |
    # |3  |Measurement units mapping  |
    # |4  |Measurement units          |
    # |5  |Normal data table          |
    # |6  |Advanced search data table |

    for name, type in table_types:
        match type:
            case 2:
                unit_tables[0] = name
            case 3:
                unit_tables[1] = name
            case 4:
                unit_tables[2] = name
            case 5:
                data_tables.append(name)
            case 6:
                advanced_tables.append(name)

    use_units = all(name is not None for name in unit_tables)

    return data_tables, advanced_tables, unit_tables, use_units


def get_structure(
    db_path: str, index_table: str
) -> Tuple[str, Tuple[List[str], List[str], List[str], bool]]:
    """Generates a string containing the structure of the database."""

    data_tables, advanced_tables, unit_tables, use_units = get_tables(
        db_path, index_table
    )

    total_tables = data_tables + advanced_tables
    table_DDLs = get_DB_tables_ddl(db_path, total_tables)

    db_structure = "\n".join(ddl for _, ddl in table_DDLs.items())
    return db_structure, (data_tables, advanced_tables, unit_tables, use_units)


def get_units_for_tables(
    db_path: str, table_names: List[str], index_table: str, unit_tables: List[str]
) -> str:
    """Returns the measurement units list for the specified tables."""

    units_list = get_units_per_table(
        db_path, unit_tables[0], unit_tables[1], unit_tables[2], index_table
    )

    units = ""
    for table, t_units in units_list.items():
        if table in table_names:
            units += f"Table: {table}\n{t_units}\n"

    return units


def get_elastic_query(llm, input: str) -> str:
    """Returns an elasticsearch-optimized query based on the input query."""

    llm_query = f"""Given a query, generate another query that represents the input.
Your response should contain the request in the input, but formatted in a way optimized for a search engine looking into a components database,
using keywords and removing useless words.
Yout response also should be the most concise possible and point to the correct result.
QUERY:
{input}"""

    llm_response = llm.llm(
        llm_query,
        format={
            "type": "object",
            "properties": {
                "search_query": {"type": "string"},
            },
            "required": ["search_query"],
        },
    )

    return json.loads(llm_response)["search_query"]
