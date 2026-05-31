#!/usr/bin/env python3
import os
import sys
import json
import re
import ast
import argparse
from pathlib import Path
import networkx as nx

class SpecGraphEngine:
    def __init__(self, workspace_dir=".", index_file=None):
        if not index_file:
            raise ValueError("index_file must be provided")
        self.workspace = Path(workspace_dir).resolve()
        self.index_file = Path(index_file)
        if not self.index_file.is_absolute():
            self.index_file = self.workspace / self.index_file
        self.graph = nx.DiGraph()
        self._load_index()

    def _parse_spec_file(self, file_path):
        """Load JSON metadata from spec files."""
        try:
            if file_path.suffix != '.json':
                return None, None
            with open(file_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            return meta.get('id', file_path.stem), meta
        except Exception as e:
            print(f"Error parsing metadata from file {file_path.name}: {e}", file=sys.stderr)
        return None, None

    def _add_node(self, node_id, node_type, **attrs):
        if self.graph.has_node(node_id):
            self.graph.nodes[node_id].update(attrs)
        else:
            self.graph.add_node(node_id, node_type=node_type, **attrs)
        return node_id

    def _reverse_relation(self, relation):
        return {
            "depends_on": "used_by",
            "uses": "used_by",
            "belongs_to": "contains",
            "contains": "belongs_to",
            "implements": "implemented_by",
            "implemented_by": "implements",
        }.get(relation)

    def _add_edge(self, source, target, relation):
        self.graph.add_edge(source, target, relation=relation)
        reverse = self._reverse_relation(relation)
        if reverse and not self.graph.has_edge(target, source):
            self.graph.add_edge(target, source, relation=reverse)

    def _get_function_source(self, file_path, function_name):
        """Extract function source code from a Python file using AST."""
        try:
            full_path = self.workspace / file_path
            if not full_path.exists():
                return None
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    lines = source.split('\n')
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else len(lines)
                    return '\n'.join(lines[start_line:end_line])
        except Exception as e:
            return None
        return None

    def compile_index(self):
        """Builds a knowledge graph from spec files and persists it as JSON."""
        self.graph.clear()

        specs_dir = self.workspace / "specs"
        specs_dir.mkdir(exist_ok=True)

        missing_descriptions = []
        missing_requirements = []
        missing_code_pointers = []

        for file_path in specs_dir.glob("*.spec.json"):
            spec_id, meta = self._parse_spec_file(file_path)
            if not spec_id:
                continue

            code_pointer = meta.get('code_pointer', {})
            code_file = code_pointer.get('file')
            code_function = code_pointer.get('function')

            self._add_node(
                spec_id,
                node_type="spec",
                description=meta.get('description', meta.get('details', meta.get('summary', ''))),
                requirements=meta.get('requirements', []),
                type=meta.get('type', 'function'),
                spec_file=str(file_path.name),
                file=code_file,
                function=code_function,
            )

            # Preserve additional spec metadata such as requirements or documentation.
            for key, value in meta.items():
                if key in {"id", "code_pointer", "depends_on", "relationships", "summary", "details", "description", "requirements", "type"}:
                    continue
                self.graph.nodes[spec_id][key] = value

            file_node_id = None
            code_node_id = None

            if code_file:
                file_node_id = f"code_file:{code_file}"
                self._add_node(
                    file_node_id,
                    node_type="code_file",
                    file=code_file,
                )

            if code_function:
                code_node_id = f"code_function:{code_file or '<unknown>'}:{code_function}"
                self._add_node(
                    code_node_id,
                    node_type="code_function",
                    file=code_file,
                    function=code_function,
                )
                if file_node_id:
                    self._add_edge(code_node_id, file_node_id, "belongs_to")
                self._add_edge(spec_id, code_node_id, "uses")
            elif file_node_id:
                self._add_edge(spec_id, file_node_id, "uses")

            dependencies = meta.get('depends_on', [])
            if isinstance(dependencies, str):
                dependencies = [d.strip() for d in dependencies.split(',') if d.strip()]

            if not meta.get('description') and not meta.get('details') and not meta.get('summary'):
                missing_descriptions.append(spec_id)
            if 'requirements' not in meta or not meta.get('requirements'):
                missing_requirements.append(spec_id)
            if not code_file or not code_function:
                missing_code_pointers.append(spec_id)

            for dep in dependencies:
                self._add_node(dep, node_type="spec")
                self._add_edge(spec_id, dep, "depends_on")

            relationships = meta.get('relationships', {})
            if isinstance(relationships, dict):
                for relation, targets in relationships.items():
                    if isinstance(targets, str):
                        targets = [targets]
                    for target in targets:
                        target_type = "spec" if ':' not in target else "code_function"
                        self._add_node(target, node_type=target_type)
                        self._add_edge(spec_id, target, relation)

        graph_data = nx.node_link_data(self.graph)
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2)

        result = {
            "status": "success",
            "nodes_indexed": len(self.graph.nodes),
        }
        if missing_descriptions:
            result["missing_descriptions"] = missing_descriptions
        if missing_requirements:
            result["missing_requirements"] = missing_requirements
        if missing_code_pointers:
            result["missing_code_pointers"] = missing_code_pointers

        return result

    def _load_index(self):
        """Hydrates the runtime graph from the JSON index cache."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.graph = nx.node_link_graph(data)
            except Exception:
                self.compile_index()
        else:
            self.compile_index()

    def node_info(self, node_id):
        if not self.graph.has_node(node_id):
            return {"error": f"Graph node '{node_id}' does not exist."}

        node_attr = dict(self.graph.nodes[node_id])
        outgoing = [
            {"target": target, "relation": self.graph.edges[node_id, target]["relation"]}
            for target in self.graph.successors(node_id)
        ]
        incoming = [
            {"source": source, "relation": self.graph.edges[source, node_id]["relation"]}
            for source in self.graph.predecessors(node_id)
        ]
        node_attr["id"] = node_id
        node_attr["outgoing_relationships"] = outgoing
        node_attr["incoming_relationships"] = incoming
        
        if node_attr.get("node_type") == "code_function":
            file_path = node_attr.get("file")
            function_name = node_attr.get("function")
            if file_path and function_name:
                source_code = self._get_function_source(file_path, function_name)
                if source_code:
                    node_attr["source_code"] = source_code
        
        return node_attr

    def search_spec(self, spec_id):
        """Returns node metadata and relationships for a spec element."""
        return self.node_info(spec_id)

    def analyze_downstream_impact(self, spec_id):
        """Traverses the graph to find nodes that depend on the target spec."""
        if not self.graph.has_node(spec_id):
            return {"error": f"Specification structural node '{spec_id}' not found."}

        affected_nodes = list(nx.ancestors(self.graph, spec_id))
        impact_map = []
        for aff_id in affected_nodes:
            node = self.graph.nodes[aff_id]
            impact_map.append({
                "spec_id": aff_id,
                "description": node.get('description'),
                "target_file": node.get('file'),
                "target_function": node.get('function')
            })

        focus = self.graph.nodes[spec_id]
        return {
            "focus_node": spec_id,
            "file": focus.get('file'),
            "function": focus.get('function'),
            "downstream_impacted_code": impact_map,
        }

    def query_nodes(self, node_type=None, relation=None, target=None, direction="out"):
        results = []
        for node_id, attrs in self.graph.nodes(data=True):
            if node_type and attrs.get("node_type") != node_type:
                continue

            if relation:
                matches = False
                if direction == "out":
                    for successor in self.graph.successors(node_id):
                        if self.graph.edges[node_id, successor].get("relation") == relation:
                            if target is None or successor == target:
                                matches = True
                                break
                else:
                    for predecessor in self.graph.predecessors(node_id):
                        if self.graph.edges[predecessor, node_id].get("relation") == relation:
                            if target is None or predecessor == target:
                                matches = True
                                break
                if not matches:
                    continue

            results.append({"id": node_id, "meta": attrs})
        return results

    def find_path(self, source_id, target_id):
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return {"error": "Source or target node does not exist."}

        try:
            path = nx.shortest_path(self.graph.to_undirected(), source_id, target_id)
            return {"path": path}
        except nx.NetworkXNoPath:
            return {"path": [], "error": "No path found between source and target."}

    def update_or_create_spec(self, spec_id, description, spec_type='function', depends_on=None, requirements=None, code_file="", code_function=""):
        """Saves spec metadata and regenerates the knowledge graph."""
        specs_dir = self.workspace / "specs"
        specs_dir.mkdir(exist_ok=True)
        file_path = specs_dir / f"{spec_id}.spec.json"
        existing_meta = {}

        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_meta = json.load(f)
            except Exception:
                pass

        dep_list = []
        if depends_on:
            dep_list = [d.strip() for d in depends_on.split(',') if d.strip()]

        req_list = None
        if requirements:
            try:
                parsed = json.loads(requirements)
                req_list = parsed
            except Exception:
                req_list = [r.strip() for r in requirements.split(',') if r.strip()]

        meta_payload = {
            "id": spec_id,
            "type": spec_type,
            "description": description,
            "code_pointer": {"file": code_file, "function": code_function},
            "depends_on": dep_list,
        }

        if req_list is not None:
            meta_payload["requirements"] = req_list

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(meta_payload, f, indent=2)

        return self.compile_index()

def main():
    parser = argparse.ArgumentParser(description="SpecTool Knowledge Graph Gateway Engine for AI Agents.")
    parser.add_argument(
        "--index-file",
        required=True,
        help="Path to the JSON index file used to store the knowledge graph.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("compile", help="Rebuild the graph index.")

    search_p = subparsers.add_parser("search", help="Query a spec node blueprint.")
    search_p.add_argument("--id", required=True, help="Node ID target.")

    node_p = subparsers.add_parser("node", help="Inspect a graph node with relationships.")
    node_p.add_argument("--id", required=True, help="Node ID target.")

    query_p = subparsers.add_parser("query", help="Query graph nodes by type or relation.")
    query_p.add_argument("--type", default="", help="Node type filter.")
    query_p.add_argument("--relation", default="", help="Relationship filter.")
    query_p.add_argument("--target", default="", help="Target node ID for relationship queries.")
    query_p.add_argument("--direction", default="out", choices=["out", "in"], help="Relationship traversal direction.")

    path_p = subparsers.add_parser("path", help="Find a path between two graph nodes.")
    path_p.add_argument("--from", dest="source", required=True, help="Source node ID.")
    path_p.add_argument("--to", dest="target", required=True, help="Target node ID.")

    impact_p = subparsers.add_parser("impact", help="Trace architectural impact zones.")
    impact_p.add_argument("--id", required=True, help="Spec or node ID target.")

    update_p = subparsers.add_parser("update", help="Create or edit a functional specification node.")
    update_p.add_argument("--id", required=True, help="Spec ID.")
    update_p.add_argument("--description", required=True, help="Detailed description text.")
    update_p.add_argument("--details", dest="description", help="Deprecated alias for --description.")
    update_p.add_argument("--summary", dest="description", help="Deprecated alias for --description.")
    update_p.add_argument("--type", default="function", help="Spec classification, such as function, module, or service.")
    update_p.add_argument("--depends_on", default="", help="Comma separated system dependencies.")
    update_p.add_argument("--requirements", default="", help="Comma separated or JSON array of requirements.")
    update_p.add_argument("--file", default="", help="Target file mapping pointer.")
    update_p.add_argument("--function", default="", help="Target function implementation string.")

    args = parser.parse_args()
    engine = SpecGraphEngine(index_file=args.index_file)

    if args.command == "compile":
        res = engine.compile_index()
    elif args.command == "search":
        res = engine.search_spec(args.id)
    elif args.command == "node":
        res = engine.node_info(args.id)
    elif args.command == "query":
        res = engine.query_nodes(
            node_type=args.type or None,
            relation=args.relation or None,
            target=args.target or None,
            direction=args.direction,
        )
    elif args.command == "path":
        res = engine.find_path(args.source, args.target)
    elif args.command == "impact":
        res = engine.analyze_downstream_impact(args.id)
    elif args.command == "update":
        res = engine.update_or_create_spec(
            spec_id=args.id,
            description=args.description,
            spec_type=args.type,
            depends_on=args.depends_on,
            requirements=args.requirements,
            code_file=args.file,
            code_function=args.function,
        )
    else:
        res = {"error": "Unknown command."}

    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
