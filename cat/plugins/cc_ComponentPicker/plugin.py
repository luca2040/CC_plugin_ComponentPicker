from cat.mad_hatter.decorators import tool
from cat.mad_hatter.decorators import hook

import sqlite3


@hook
def agent_prompt_prefix(prefix, cat):
    prefix = """You are an AI component picker assistant.
You help users to find an electrical component based on the request.
You reply ONLY using info returned by Tools, if info is not given, respond that I Dont Have Informations."""

    return prefix


def get_structure(db_path):
    # Load DB structure and dynamically generate tool prefix.

    # While testing just simple static prefix
    prefix = """Use this tool whenever the user asks about cats"""

    def func(obj):
        obj.__doc__ = prefix
        return obj

    return func


@tool(return_direct=True)
@get_structure("/app/cat/componentsDB/database.sqlite")
def component_info(input, cat):

    return "Test - DB"
