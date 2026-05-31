# description
the spec driven development is made of three components:
1. spec.prompt.md that provide policies for spec methology, include the knowledge graph management, graph node syntax, etc
2. x.index.json the index file for graph relationship
3. spec_tool.py the management tool for CRUD operations, 

====
1. index.json contains knowledge graph relationship. 
   the node element contains ID for each spec entity.
   the souce code contain the ID in the tag for begin and end of that entity
   e.g. 
- # id:calculate start
    def calculate(data, factor=2):
        result = sum(data) * factor
        return result
- # id:calculate end

- # id:some_feature start
    #whatever text here
    #whatever content here
- # id:some_feature end

2. spec_tool.py should use the id to retrieve the text block from the source code file if the content is not contained in the .index.json file

3. spec.prompt.md should have instructions that instruct LLM agent to create and maintain the id and use spec_tool to update the index when source code is changed

4. logically, the requirement nodes should point to spec nodes, spec nodes should point to implementation nodes (function nodes)

    requirement ->specified-by spec 
    spec->implemented by function

5. when user use /spec, LLM agent should use spec_tool to update each of these nodes and relatiohships:

    requirement     : id and content element for the full requirement text
    specification   : id and content element for the full specification text
    implementation  : id that identifies the function as described in bullet point 1 above

    

