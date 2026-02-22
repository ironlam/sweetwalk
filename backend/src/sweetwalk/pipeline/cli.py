import argparse
from pathlib import Path
from sweetwalk.pipeline.extract import extract_pedestrian_graph, save_graph


CITIES = {
    "paris": "Paris, France",
    "london": "London, United Kingdom",
    "munich": "Munich, Germany",
    "nyc": "New York City, New York, USA",
}


def main():
    parser = argparse.ArgumentParser(description="Sweet Walk data pipeline")
    parser.add_argument(
        "city",
        choices=list(CITIES.keys()),
        help="City to process",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Output directory for graph files",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    place = CITIES[args.city]
    print(f"Extracting pedestrian graph for {place}...")

    G = extract_pedestrian_graph(place)
    print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    output_path = args.output_dir / f"{args.city}.graphml"
    save_graph(G, output_path)
    print(f"  Saved to {output_path}")


if __name__ == "__main__":
    main()
