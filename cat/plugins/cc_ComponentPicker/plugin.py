from cat.mad_hatter.decorators import tool
from cat.mad_hatter.decorators import hook


@hook
def agent_prompt_prefix(prefix, cat):
    prefix = """"""

    return prefix


@tool(return_direct=True)
def component_info(input, cat):
    """"""

    return "Test - DB"
