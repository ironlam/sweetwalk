import argparse
from pathlib import Path
from sweetwalk.pipeline.extract import extract_pedestrian_graph, save_graph
from sweetwalk.scoring.scorer import extract_feature_layers, score_graph


CITIES = {
    "paris": "Paris, France",
    "london": "London, United Kingdom",
    "munich": "Munich, Germany",
    "nyc": "New York City, New York, USA",
}


def main():
    parser = argparse.ArgumentParser(description="Sweet Walk data pipeline")
    parser.add_argument("city", choices=list(CITIES.keys()), help="City to process")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--skip-scoring", action="store_true", help="Skip scoring step (graph only)")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    place = CITIES[args.city]

    print(f"[1/3] Extracting pedestrian graph for {place}...")
    G = extract_pedestrian_graph(place)
    print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    if not args.skip_scoring:
        print(f"[2/3] Downloading feature layers for scoring...")
        layers = extract_feature_layers(place)
        for name, gdf in layers.items():
            print(f"  {name}: {len(gdf)} features")

        print(f"[3/3] Scoring edges...")
        G = score_graph(G, layers)

    output_path = args.output_dir / f"{args.city}.graphml"
    save_graph(G, output_path)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
