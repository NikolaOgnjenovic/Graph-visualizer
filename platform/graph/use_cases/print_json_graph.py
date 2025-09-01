import argparse
import json
import sys
from pathlib import Path

# Ensure project root is in sys.path so that 'plugins' and 'API' packages are importable when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins.datasources.json.graph.json.datasource import JsonTreeLoader


def main():
    parser = argparse.ArgumentParser(description="Load a JSON file as a graph and print it.")
    parser.add_argument("json_path", nargs="?", default=str(Path(__file__).resolve().parents[3] / "data/json/test_simple_graph.json"), help="Path to JSON file to load")
    args = parser.parse_args()

    path = Path(args.json_path)
    if not path.exists():
        print(f"File not found: {path}")
        raise SystemExit(1)

    content = path.read_text(encoding="utf-8")
    loader = JsonTreeLoader()
    graph = loader.load(content)

    # Pretty print basic graph info
    print(f"Graph ID: {graph.graph_id}")
    print(f"Nodes ({len(graph.nodes)}):")
    for n in graph.nodes:
        attrs = json.dumps(n.attributes, ensure_ascii=False)
        print(f"  - [{n.node_id}] {n.name} attrs={attrs}")

    print(f"Edges ({len(graph.edges)}):")
    for e in graph.edges:
        print(f"  - {e.source.node_id} -> {e.destination.node_id} ({e.direction.name})")


if __name__ == "__main__":
    main()
