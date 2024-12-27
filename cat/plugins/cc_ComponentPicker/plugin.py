from cat.mad_hatter.decorators import tool
from cat.mad_hatter.decorators import hook

from cat.plugins.cc_ComponentPicker.functions import pick_component

import json


@hook
def agent_prompt_prefix(prefix, cat):

    prefix = """You are an electronics component picker AI tool.
You help who asks to find a component that satisfies the request.
You MUST respond only with information that was given to you explicitely and if you don't have that information say that you "don't have informations" """

    return prefix


@tool
def component_info(input, cat):
    """Use this tool to identify and structure necessary information from user questions about electronic components.  

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

    results = [pick_component(component, cat) for component in components]

    return "\n".join(results)
