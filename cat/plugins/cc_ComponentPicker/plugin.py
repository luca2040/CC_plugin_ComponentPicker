from cat.mad_hatter.decorators import tool
from cat.mad_hatter.decorators import hook

from cat.plugins.cc_ComponentPicker.functions import pick_component

import json


@hook
def agent_prompt_prefix(prefix, cat):

    prefix = """You are an electronics component picker AI tool.
You help who asks to find a component that satisfies the request.
You MUST respond only with information that was given to you explicitely and if you don't have that information say that you "don't have informations".

**IMPORTANT**
If a TOOL OUTPUT returns the character # followed by @request@, it means that the user didn't specify the @request@ component characteristisc, so you MUST respond to tell the user to Include That Specific Info.

ALWAYS USE CHAT CONTEXT TO CONTINUE THE DIALOGUE AND USE TOOLS, IF SPECIFIED IN OTHER MESSAGES.

If more than one component are found for the same component requested, list them all and include a little summary at the end with the suggested components (if found)."""

    return prefix


@tool
def component_info(input, cat):
    """Use this tool to identify and structure necessary information from user questions about electronic components, or info about components (for example "I need ...." or "find a ..."), or continuation from previous dialogs and messages.

**Input Format**: The input should be a JSON list, where each component is an object with required parameters extracted from the user's query, listed in the "description".
Each component is named with a unique code (e.g., "C1" for the first capacitor or "IC2" for the second IC).
IMPORTANT: Don't put any references between component descriptions (example: "resistor for the diode"), but repeat the data (example: "300Ohm resistor")

**Example**:
User Question:
"Find a 5mA diode fast enough to run at 50kHz, and an N-mosfet capable of 5A at that frequency, controlled by the diode output."  

Tool Input:
[
  {
    "code": "D1",
    "type": "diode",
    "description": "Fast diode, can sustain at least 5mA, can run at 50kHz"
  },
  {
    "code": "M1",
    "type": "mosfet",
    "description": "N-mosfet, can sustain at least 5A, can run at 50kHz"
  }
]

**Example**:
User Question:
"I need a 100mA PNP Darlington transistor that can run at 40V, and a diode that will be connected to its output."  

Tool Input:
[
  {
    "code": "T1",
    "type": "transistor",
    "description": "PNP Darlington transistor, can sustain at least 100mA, can run at 40V"
  },
  {
    "code": "D1",
    "type": "diode",
    "description": "Diode, can sustain at least 100mA, can sustain 40V"
  }
]
"""

    components = json.loads(input)

    results = ""

    cat.send_ws_message(content=f'Let me find the component...',
                        msg_type='chat')

    for component in components:
        picked_component, detail, found = pick_component(component, cat)

        if detail:
            if found:
                results += f"""\n\n\nFound components: {
                    picked_component}\n\n for request: {str(component)}"""
            else:
                results += f"""\n\n\nNOT Found component for request: {
                    str(component)}"""
        else:
            results += f"""\n\n\nNOT fount: {str(component)}\n\n Because the detail {
                picked_component} is missing."""

    return results
