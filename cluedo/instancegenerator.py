# cluedo/instancegenerator.py

import os
import random

from clemcore.clemgame import GameInstanceGenerator


SEED = 42

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
    "Knife",
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
    "Study"
]


class CluedoGameInstanceGenerator(GameInstanceGenerator):

    def __init__(self):
        super().__init__(os.path.dirname(__file__))

    def on_generate(self, seed: int, **kwargs):

        random.seed(seed)

        # Create one experiment
        experiment = self.add_experiment("minimal")

        experiment["max_turns"] = 6

        experiment["initial_prompt"] = (
            "You are playing Cluedo.\n"
            "On your turn, make a suggestion.\n"
            "Format exactly:\n"
            "SUGGEST: suspect, weapon, room"
        )

        # Create some game instances
        for instance_id in range(3):

            suspects = SUSPECTS.copy()
            weapons = WEAPONS.copy()
            rooms = ROOMS.copy()

            # Select secret solution
            solution = {
                "suspect": random.choice(suspects),
                "weapon": random.choice(weapons),
                "room": random.choice(rooms),
            }

            # Remove solution cards
            remaining_cards = []

            for s in suspects:
                if s != solution["suspect"]:
                    remaining_cards.append(s)

            for w in weapons:
                if w != solution["weapon"]:
                    remaining_cards.append(w)

            for r in rooms:
                if r != solution["room"]:
                    remaining_cards.append(r)

            random.shuffle(remaining_cards)

            # Split cards between 2 players
            midpoint = len(remaining_cards) // 2

            player1_hand = remaining_cards[:midpoint]
            player2_hand = remaining_cards[midpoint:]

            # Create instance
            game_instance = self.add_game_instance(
                experiment,
                instance_id
            )

            game_instance["solution"] = solution

            game_instance["player_hands"] = {
                "player_1": player1_hand,
                "player_2": player2_hand,
            }

            game_instance["suspects"] = suspects
            game_instance["weapons"] = weapons
            game_instance["rooms"] = rooms


if __name__ == "__main__":
    CluedoGameInstanceGenerator().generate(seed=SEED)