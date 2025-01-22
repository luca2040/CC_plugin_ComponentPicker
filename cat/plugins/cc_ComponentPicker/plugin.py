from cat.mad_hatter.decorators import tool
from cat.mad_hatter.decorators import hook

from cat.plugins.cc_ComponentPicker.data import get_needed_tables, get_db_query
from cat.plugins.cc_ComponentPicker.database import query_db_json

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


@tool()
def component_info(input, cat):
    """Use this tool always when the user asks a question about electrical components, to find the characteristics,
to find some that meet some requirements, or to give a list of components.
input is what the user requested, formatted in a complete and short way.
"""

    tables, (data_tables, advanced_tables, unit_tables,
             use_units), structure = get_needed_tables(cat, input, DB_PATH, INDEX_TABLE)
    if not tables:
        return "Component not found"

    advanced_search = any(name in advanced_tables for name in tables)

    if advanced_search:
        return "adv"

    db_query, units = get_db_query(cat, input, structure, DB_PATH,
                                   INDEX_TABLE, tables, unit_tables, use_units)

    cat.send_ws_message(content=f"```SQL\n{db_query}\n```", msg_type='chat')

    db_result = query_db_json(DB_PATH, db_query)

    return_info = f"""DB QUERY:
```{db_query}```
RESPONDED:
{db_result}
{units}"""

    return return_info
