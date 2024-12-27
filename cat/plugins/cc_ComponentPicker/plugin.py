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
If a TOOL OUTPUT returns the character # followed by @request@, it means that the user didn't specify the @request@ component characteristisc, so you MUST respond to tell the user to INCLUDE THAT SPECIFIC INFO.

ALWAYS USE CHAT CONTEXT TO CONTINUE THE DIALOGUE AND USE TOOLS, IF SPECIFIED IN OTHER MESSAGES."""

    return prefix


@tool
def component_info(input, cat):
    """Use this tool to identify and structure necessary information from user questions about electronic components, or continuation from previous dialogs and messages.  

**Input Format**: The input should be a JSON list, where each component is an object with required parameters extracted from the user's query. Each component is named with a unique code (e.g., "C1" for the first capacitor or "IC2" for the second IC).  

**Example**:  
User Question:  
"Find a 5mA diode fast enough to run at 50kHz, and an N-mosfet capable of 5A at that frequency, controlled by the diode output."  

Tool Input:  
```json  
[  
  {  
    "code": "D1",  
    "type": "diode",  
    "parameters": {  
      "minimum_current": "5mA",  
      "frequency": "50kHz"  
    }  
  },  
  {  
    "code": "M1",  
    "type": "mosfet",  
    "parameters": {  
      "polarity": "N",  
      "minimum_current": "5A",  
      "frequency": "50kHz"  
    }
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
