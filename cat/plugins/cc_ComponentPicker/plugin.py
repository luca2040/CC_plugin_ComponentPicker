from cat.mad_hatter.decorators import tool
from cat.mad_hatter.decorators import hook

import sqlite3
import json

DB_PATH = "/app/cat/componentsDB/database.sqlite"


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


def get_DB_tables_ddl(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

    tab_names = cursor.fetchall()
    DDLs = {}

    for db_table_name in tab_names:
        table_name = db_table_name[0]

        cursor.execute(
            f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))

        ddl = cursor.fetchone()[0]
        DDLs[table_name] = ddl

    conn.close()

    return DDLs


def get_structure(db_path):
    # Load DB structure and dynamically generate tool prefix.

    table_DDLs = get_DB_tables_ddl(db_path)
    table_DDLs.pop("sqlite_sequence")

    db_structure = "\n".join(ddl for _, ddl in table_DDLs.items())

    prefix = f"""Use this tool whenever the user asks every questions about electrical components, to find the characteristics, to find some that respect some requirements, or to give a list of components.
input is an SQLite query to extract requested components from a database.
When searching for TEXT use the LIKE comparator instead of =.
ALWAYS Use ID references to other tables indicated in the strucutre when possible, and NEVER make the query return the ID itself but the value it points to unless specificately stated.
Use ONLY given tables in the structure to find data, if there is not what the user requestet make an SQLite query that returns no data.
As a minimun always include a 10 rows max for the output and order by relevant data asked by the user.
DATABASE STRUCTURE:
{db_structure}"""

    def func(obj):
        obj.__doc__ = prefix
        return obj

    return func


@tool()
@get_structure(DB_PATH)
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
