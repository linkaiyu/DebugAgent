# description
The spec skill is used to create spec in any stage of the software development, from specification, to plan and implementation
user use /spec when providing prompt.
the spec skill defines the structure in three tiers:
  1. spec/requirements
  2.   plan: architecute, data flow, libs, SDK, algorithms etc
  3.     implmentation code, modules, functions etc

all three componenets are contained in json structure, with key, description, graph relationship
the spec and plan live in .spec.json file, the code lives in .py file
the graph relationship allows spec_manager.py program to navigate the node to retrieve information by AI Agent
/spec prompt or skill explain the above structure and regulates AI Agent's operation.
by using /spec, AI agent will maintain the .spec.json when it takes user input, generate code, or tries to understand the context
this approach is meant to preserve the software context for AI agent and also to reduce .py code size by separating .spec.json from .py docstring

the /reverse_spec skill reverse engineer the existing code to create the .spec.json file
