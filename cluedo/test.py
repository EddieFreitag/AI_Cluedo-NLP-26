import json
from experiment_runner import ExperimentRunner
from pathlib import Path

model_api_mapping = json.load(open("models.json", "r"))

results_dir = Path("results")
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
    "groq": True,
    "gemini": True,
    "cohere": True,
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
                    instances_dir="instances",
                    output_file=f"results/{model}.jsonl"
                    ).run()
                tested.append(model)
            except Exception as e:
                print("Warning: big bad error happened:")
                print(e)