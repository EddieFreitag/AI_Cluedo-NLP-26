import argparse
import json
import os
import random
from pathlib import Path
from game_master import CluedoGame

from instancegenerator import CluedoInstanceGenerator

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("model_name", type=str)
    return parser.parse_args()


class ExperimentRunner:

    def __init__(
        self,
        model_name: str,
        baseline_model:str,
        instances_dir: str,
        output_file: str,
    ):
        self.model_name = model_name
        self.baseline_model = baseline_model
        self.instances_dir = instances_dir
        self.output_file = output_file
        

    def run(self):
        instances = self.load_instances()
        print(f"Initializing {len(instances)} experiments with models: {self.model_name}")
        for inst in instances:
            n_players = inst['n_players']
            max_turns = inst['max_turns']
            games = inst['games']
            seed = inst['seed']

            # create list of baseline_models and at random pos set target_model
            pos = random.randint(0, n_players-1)
            models = [self.baseline_model] * n_players
            models[pos] = self.model_name
            game_logs = []

            for i, g in enumerate(games):
                print("+"+"-"*40+"+")
                print(f"|\t Evaluating game {i+1}/{len(games)}\t\t|")
                print("+"+"-"*40+"+")

                cluedo = CluedoGame(models, g, n_players, max_turns, i)
                cluedo.run_game()
                game_logs.append(cluedo.orchestrator.logger.finalize())

            # save the instance
            experiment = {
                "model": self.model_name,
                "pos": pos,
                "baseline_model": self.baseline_model,
                "players": n_players,
                "max_turns": max_turns,
                "seed": seed,
                "game_logs": game_logs
            }

            self.save(experiment)
            


                

    def save(self, experiment):
        path = Path(self.output_file)

        # ensure parent directories exist
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(experiment, ensure_ascii=False))
            f.write("\n")


    def load_instances(self):

        instances = []

        for path in sorted(Path(self.instances_dir).glob("*.json")):
            with open(path) as f:
                instances.append(json.load(f))

        return instances
    

if __name__ == "__main__":
    args = parse_args()
    model = args.model_name
    baseline_model = "llama3:8b"
    exp = ExperimentRunner(model, baseline_model, "instances", output_file=f"results/{model}.jsonl")
    exp.run()