from cat.mad_hatter.decorators import tool
from cat.mad_hatter.decorators import hook

import sqlite3
import json

DB_PATH = "/app/cat/componentsDB/database.sqlite"


@hook
def agent_prompt_prefix(prefix, cat):
    prefix = """You are an AI component picker assistant.
You help users to find an electrical component based on the request.
Always reply based on informations given explicitely to you."""

    return prefix


@hook
def before_cat_recalls_procedural_memories(procedural_recall_config, cat):
    procedural_recall_config["threshold"] = 0.5

    return procedural_recall_config


def get_structure(db_path):
    # Load DB structure and dynamically generate tool prefix.

    # db_structure is a JSON-like string the cat can understand.
    # While testing just simple static prefix
    db_structure = """Tables:[
"Mosfets": {	Code TEXT NOT NULL,
	Polarity TEXT NOT NULL [measure_unit: "N" or "P"],
	Power REAL NOT NULL [measure_unit: W],
	Drain_s_V REAL NOT NULL [measure_unit: V],
	Gate_s_V REAL NOT NULL [measure_unit: V],
	Drain_s_I REAL NOT NULL [measure_unit: A],
	T_junc REAL NOT NULL [measure_unit: °C],
	Rise_t REAL NOT NULL [measure_unit: ns],
	Output_cap REAL NOT NULL [measure_unit: pF],
	Rds_ON REAL NOT NULL [measure_unit: Ohm],
	Package_ID INTEGER NOT NULL [ID reference to table "Packages"]}
"Packages": {	ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	Name TEXT NOT NULL}
"Resistors": {	Value REAL NOT NULL [measure_unit: Ohm],
	Tolerance REAL NOT NULL [measure_unit: %],
	Power REAL NOT NULL [measure_unit: W],
	Type_ID INTEGER NOT NULL [ID reference to table "Resistor_types"]}
"Resistor_types": {	ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"Type" TEXT NOT NULL}
]"""

    prefix = f"""Use this tool whenever the user asks every questions about electrical components, to find the characteristics, to find some that respect some requirements, or to give a list of components.
input is an SQLite query to extract requested components from a database.
When searching for TEXT use the LIKE comparator instead of =.
Use ID references to other tables indicated in the strucutre when possible, and never make the query return the ID itself but the value it points to unless specificately stated.
Use ONLY given tables in the structure to find data, if there is not what the user requestet make an SQLite query that returns no data.
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
