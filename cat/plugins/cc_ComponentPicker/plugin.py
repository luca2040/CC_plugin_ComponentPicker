from cat.mad_hatter.decorators import tool
from cat.mad_hatter.decorators import hook

from cat.plugins.cc_ComponentPicker.data import (
    get_needed_tables,
    get_db_query,
    get_tables,
    get_elastic_query
)
from cat.plugins.cc_ComponentPicker.database import query_db_json, get_data_list

import os
from elasticsearch import Elasticsearch

DB_PATH = os.environ["CAT_DB_PATH"]
INDEX_TABLE = os.environ["CAT_INDEX_TABLE"]


@hook
def agent_prompt_prefix(prefix, cat):
    prefix = """You are an AI component picker assistant.
You help users to find an electrical component based on the request.
Always reply based on informations given explicitely to you, and NEVER discuss info that is given to you (everything is always correct).
NEVER insert in your response ANY data that is not given explicitely to you."""

    return prefix


@hook
def before_cat_bootstrap(cat):
    es = Elasticsearch("http://elasticsearch:9200",
                       api_key=os.environ["ELASTIC_KEY"])

    _, advanced_tables, _, _ = get_tables(DB_PATH, INDEX_TABLE)

    for table in advanced_tables:
        es_table = table.lower()

        if not es.indices.exists(index=es_table):
            es.indices.create(index=es_table)

        data_list = get_data_list(DB_PATH, table)

        docs = []
        base_settings = {
            "_extract_binary_content": True,
            "_reduce_whitespace": True,
            "_run_ml_inference": True,
        }

        for row in data_list:
            index_data = {"index": {"_index": es_table, "_id": str(row["ID"])}}
            content_data = base_settings.copy()

            row.pop("ID")

            for key, value in row.items():
                content_data[key] = value

            docs += [index_data, content_data]

        es.bulk(operations=docs, pipeline="ent-search-generic-ingestion")

    es.close()


@hook
def before_cat_recalls_procedural_memories(procedural_recall_config, cat):
    procedural_recall_config["threshold"] = 0.5

    return procedural_recall_config


@tool()
def component_info(input, cat):
    """Use this tool always when the user asks a question about electrical components (Active, passive, integrated circuits, ...), to find the characteristics,
to find some that meet some requirements, or to give a list of components.
input is what the user requested, formatted in a complete and short way.
"""

    tables, (_, advanced_tables, unit_tables, use_units), structure = get_needed_tables(
        cat, input, DB_PATH, INDEX_TABLE
    )
    cat.send_ws_message(content=f"Selected tables:\n{tables}", msg_type="chat")
    if not tables:
        return "Requested component's table does not exist in the database."

    advanced_search = any(name in advanced_tables for name in tables)

    if advanced_search:
        es_query = get_elastic_query(cat, input)
        # The commented "nopep8" is just because the formatter kept breaking this line
        cat.send_ws_message(content=f"Elastic query:\n{es_query}", msg_type="chat")  # nopep8

        es = Elasticsearch(
            "http://elasticsearch:9200", api_key=os.environ["ELASTIC_KEY"]
        )

        search_body = {
            "query": {
                "query_string": {"query": es_query}
            }
        }

        response = es.search(index="ics", body=search_body)
        es.close()

        result_found = response["hits"]["total"]["value"] > 0
        hits = response["hits"]["hits"]

        results = []
        for hit in hits:
            score = hit["_score"]
            source = hit["_source"]
            data = str(list(source.items()))

            results.append((score, data))

        result_num = 3
        sorted_results = sorted(results, key=lambda x: x[0], reverse=True)
        best_results = sorted_results[:result_num]

        return_info = f"""SEARCH RETURNED ITEMS:
{str([res[1] for res in best_results])}"""

        return return_info

    db_query, units = get_db_query(
        cat, input, structure, DB_PATH, INDEX_TABLE, tables, unit_tables, use_units
    )

    cat.send_ws_message(content=f"```SQL\n{db_query}\n```", msg_type="chat")

    db_result = query_db_json(DB_PATH, db_query)
    if not db_result:
        db_result = "Found no components meeting the requirements."

    return_info = f"""DB QUERY:
```{db_query}```
RESPONDED:
{db_result}
{units}"""

    return return_info
