import json
from pathlib import Path
from experiment_runner import ExperimentRunner
from evaluation.analysis import CluedoAnalyzer
from evaluation.metrics import evaluate


results_dir = Path("cluedo/results")

def run_games():
    model_api_mapping = json.load(open("cluedo/models.json", "r"))


    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir.resolve()}")

    json_paths = sorted(
        p for p in results_dir.rglob("*")
        if p.is_file()
        and p.suffix in {".jsonl"}
    )

    tested = [str(x).replace(".jsonl", "").replace("results/", "") for x in json_paths]
    baseline_model = "gemma3:4b"
    test = {
        "ollama": True,
        "groq": False,
        "gemini": False,
        "cohere": False,
    }
    print("Testing all models except:")
    print(tested)
    for model_api in model_api_mapping.keys():
        for model in model_api_mapping[model_api]:
            if test[model_api] and model not in tested:
                print(f"Running {model_api} experiment: {model}")
                if "ollama" == model_api:
                    baseline_model = model
                    print("Running Ollama model against itself")
                try:
                    ExperimentRunner(
                        model_name=model,
                        baseline_model=baseline_model, 
                        instances_dir="cluedo/instances",
                        output_file=f"cluedo/results/{model}.jsonl"
                        ).run()
                    tested.append(model)
                except Exception as e:
                    print("Warning: big bad error happened:")
                    print(e)


def run_analysis():
    output_path = results_dir / "analysis_summary.json"
    json_paths = sorted(
        p for p in results_dir.rglob("*")
        if p.is_file()
        and p.suffix in {".json", ".jsonl"}
        and p.name != output_path.name
    )

    if not json_paths:
        print(f"No JSON files found under {results_dir.resolve()}")
        return {}

    all_summaries = {}
    for path in json_paths:
        ca = CluedoAnalyzer(path)
        summary = ca.summary()
        all_summaries[path.relative_to(results_dir).as_posix()] = summary
        print(f"=== {path} ===")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=4, ensure_ascii=False)

    print(f"Saved aggregated analysis to {output_path}")
    return all_summaries


def run_metrics():
    all_results = {}
    for file in results_dir.glob("*.json"):
        with open(file, encoding="utf-8") as f:
            summary = json.load(f)
        all_results.update(evaluate(summary))

    output_path = Path(__file__).resolve().parent / "evaluation" / "evaluation_summary.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(json.dumps(all_results, indent=2))
    print(f"Saved metrics summary to {output_path}")
    return all_results


if __name__ == "__main__":
    run_games()
    run_analysis()
    run_metrics()