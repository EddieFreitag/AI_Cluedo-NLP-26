# cluedo/instancegenerator.py

import os
import random
import json

SEED = 42
INST_PATH = "instances/"

SUSPECTS = [
    "Scarlet",
    "Mustard",
    "White",
    "Green",
    "Peacock",
    "Plum"
]

WEAPONS = [
    "Rope",
    "Dagger",
    "Candlestick",
    "Revolver",
    "Lead Pipe",
    "Wrench"
]

ROOMS = [
    "Kitchen",
    "Ballroom",
    "Conservatory",
    "Dining Room",
    "Library",
    "Lounge",
    "Hall",
    "Study",
    "Billiard Room"
]


class CluedoInstanceGenerator:
    def __init__(self, seed=SEED, n_players=2, max_turns=5, n_instances=10):
        self.seed = seed
        self.n_players = n_players
        self.max_turns = max_turns
        self.n_instances = n_instances
        random.seed(seed)

    def generate_instance(self):
        suspect = random.choice(SUSPECTS)
        weapon = random.choice(WEAPONS)
        room = random.choice(ROOMS)
        solution = {
                "suspect": suspect,
                "weapon": weapon,
                "room": room
        }

        all_cards = SUSPECTS + WEAPONS + ROOMS
        all_cards.remove(suspect)
        all_cards.remove(weapon)
        all_cards.remove(room)
        random.shuffle(all_cards)
        player_cards = {}
        for i in range(self.n_players):
            player_cards[f"Player {i + 1}"] = all_cards[i * (len(all_cards) // self.n_players):(i + 1) * (len(all_cards) // self.n_players)]

        return solution, player_cards

    def save_experiment(self, instances, filename="instances.json"):
        with open(os.path.join(INST_PATH, filename), "w") as f:
            experiment = {
                "seed": self.seed,
                "n_players": self.n_players,
                "max_turns": self.max_turns,
                "instances": instances
            }
            json.dump(experiment, f, indent=4)

    def generate_experiment(self):
        instances = []
        for i in range(self.n_instances):
            solution, player_cards = self.generate_instance()
            instance = {
                "solution": solution,
                "player_cards": player_cards
            }
            instances.append(instance)
        # save instances to json file
        self.save_experiment(instances)

if __name__ == "__main__":
    generator = CluedoInstanceGenerator()
    generator.generate_experiment()