from cat.mad_hatter.decorators import tool
from cat.mad_hatter.decorators import hook

from cat.plugins.cc_ComponentPicker.database import *

import sqlite3
import json

DB_PATH = "/app/cat/componentsDB/database.sqlite"
INDEX_TABLE = "Tables_metadata"


@hook
def agent_prompt_prefix(prefix, cat):
    prefix = """You are an AI component picker assistant.
You help users to find an electrical component based on the request.
Always reply based on informations given explicitely to you, and NEVER discuss info that is given to you (everything is always correct).
NEVER insert in your response ANY data that is not given explicitely to you."""

    return prefix


@hook
def before_cat_recalls_procedural_memories(procedural_recall_config, cat):
    procedural_recall_config["threshold"] = 0.5

    return procedural_recall_config


def get_structure(db_path, index_table):
    # Load DB structure and dynamically generate tool prefix.
    table_types = get_table_types(db_path, index_table)

    data_tables = []
    advanced_tables = []

    columns_metadata_table_name = None
    units_map_table_name = None
    units_table_name = None

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
                columns_metadata_table_name = name
            case 3:
                units_map_table_name = name
            case 4:
                units_table_name = name
            case 5:
                data_tables.append(name)
            case 6:
                advanced_tables.append(name)

    use_units = columns_metadata_table_name and units_map_table_name and units_table_name

    units = ""
    if use_units:
        units_list = get_units_per_table(
            db_path, columns_metadata_table_name, units_map_table_name, units_table_name, index_table)

        units_string = ""
        for table, t_units in units_list.items():
            units_string += f"Table: {table}\n{t_units}\n"

        units = f"MEASUREMENT UNITS:\n{units_string}"

    # will be used later
    print(advanced_tables)

    table_DDLs = get_DB_tables_ddl(db_path, data_tables)

    db_structure = "\n".join(ddl for _, ddl in table_DDLs.items())

    prefix = f"""Use this tool whenever the user asks every questions about electrical components, to find the characteristics, to find some that respect some requirements, or to give a list of components.
input is an SQLite query to extract requested components from a database.
When searching for TEXT use the LIKE comparator instead of =.
ALWAYS Use ID references to other tables indicated in the strucutre when possible, and NEVER make the query return the ID itself but the value it points to unless specificately stated.
Use ONLY given tables in the structure to find data, if there is not what the user requestet make an SQLite query that returns no data.
As a minimun always include a 10 rows max for the output and order by relevant data asked by the user.
DATABASE STRUCTURE:
{db_structure}
{units}"""

    def func(obj):
        obj.__doc__ = prefix
        return obj

    return func


@tool()
@get_structure(DB_PATH, INDEX_TABLE)
def component_info(input, cat):
    cat.send_ws_message(content=f"```SQL\n{input}\n```", msg_type='chat')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(input)

    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append(dict(zip(columns, row)))

    json_response = json.dumps(result)

    conn.close()

    return json_response
