from experiment_runner import ExperimentRunner
import json

model_api_mapping = json.load(open("models.json", "r"))
tested = ["llama3:8b", "gemma3:4b", "gemma3:12b"]
baseline_model = "gemma3:4b"
test = {
    "ollama": False,
    "groq": False,
    "gemini": False,
    "cohere": True,
}

for model_api in model_api_mapping.keys():
    for model in model_api_mapping[model_api]:
        if test[model_api]:
            print(f"Running {model_api} experiment: {model}")
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