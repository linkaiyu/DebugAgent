# description
the spec driven development is made of four components:

1. spec.prompt.md:
    the /spec prompt that provides policies for spec methology, include the knowledge graph management, graph node syntax, etc
2. x.spec.md:
    file that contain the content details of the requirement and specification text
    this .spec.md file should contain the content that is mapped by the implementations in code. it should have id that is used for the index file
3. x.index.json: 
    the index file for graph relationship that points to the .spec.md or the .py file
4. spec_tool.py: the management tool for CRUD operations, 

====
1. index.json contains knowledge graph relationship. 
   the node element contains ID for each spec entity.
   the souce code contain the ID in the tag for begin and end of that entity
   e.g.

```python
# id:calculate start
    def calculate(data, factor=2):
        result = sum(data) * factor
        return result
# id:calculate end

# id:some_feature start
    #whatever text here
    #whatever content here
# id:some_feature end
```
2. spec_tool.py should use the id to retrieve the text block from the source code file if the content is not contained in the .index.json file

3. spec.prompt.md should have instructions that instruct LLM agent to create and maintain the id and use spec_tool to update the index when source code is changed

4. logically, the requirement nodes should point to spec nodes, spec nodes should point to implementation nodes (function nodes)

    requirement ->specified-by spec 
    spec->implemented by function

5. when user use /spec, LLM agent should use spec_tool to update each of these nodes and relatiohships:

    requirement     : id and content element for the full requirement text
    specification   : id and content element for the full specification text
    implementation  : id that identifies the function as described in bullet point 1 above

6. to improve traverse performance, consider update spec_tool.py to use this json schema for .spec.json. this should cover the types for requirement, specification, module, class, function etc software structure.

make sure you understand the following examples for schema and runtime code

{
  "entities": {
    "<entity_id>": {
      "type": "<entity_type>",
      "name": "<name>",
      "properties": {}
    }
  },

  "relations": [
    {
      "source": "<entity_id>",
      "relation": "<relation_type>",
      "target": "<entity_id>",
      "properties": {}
    }
  ]
}

so that these node types can be stored, for example

requirement:

{
  "id": "req_login",
  "type": "Requirement",
  "name": "User Login",
  "properties": {
    "priority": "high"
  }
}
specification:

{
  "id": "spec_oauth",
  "type": "Specification",
  "name": "OAuth Authentication",
  "properties": {
    "version": "1.0"
  }
}

class:

{
  "id": "class_authservice",
  "type": "Class",
  "name": "AuthService",
  "properties": {
    "file": "auth_service.py"
  }
}

function:

{
  "id": "func_validate_token",
  "type": "Function",
  "name": "validate_token",
  "properties": {
    "file": "auth_service.py",
    "line": 45
  }
}

relationships:

[
  {
    "source": "req_login",
    "relation": "implemented_by",
    "target": "spec_oauth"
  },

  {
    "source": "spec_oauth",
    "relation": "defines",
    "target": "class_authservice"
  },

  {
    "source": "class_authservice",
    "relation": "contains",
    "target": "func_validate_token"
  }
]

for runtime code, at loading time:

entities = {}

outgoing_edges = {}
incoming_edges = {}

type_index = {}
name_index = {}

entity look up:

entities["func_validate_token"]

type index:

type_index = {
    "Function": {
        "func_validate_token",
        "func_login"
    },

    "Class": {
        "class_authservice"
    }
}
query:
find_all_functions()

use strong typed relations:

implemented_by
defines
contains
calls
inherits
uses
verified_by
depends_on
creates
reads
writes


    

