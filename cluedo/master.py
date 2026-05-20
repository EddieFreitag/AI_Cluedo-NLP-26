from typing import Dict, List

from clemcore.backends import Model
from clemcore.clemgame import GameBenchmark, DialogueGameMaster, Player


# -------------------------
# Players
# -------------------------

class CluedoPlayer(Player):

    def __init__(self, model, name):
        super().__init__(model)
        self.name = name
        self.counter = 0

    def _custom_response(self, messages, turn_idx=None):
        self.counter += 1
        return f"SUGGEST: Scarlet, Rope, Kitchen (t={self.counter})"


# -------------------------
# Game Master (LEGACY STYLE)
# -------------------------



class Cluedo(DialogueGameMaster):

    def _on_setup(self, **game_instance):
        self.turn = 0
        self.max_turns = 4

        self.p1 = CluedoPlayer(self.player_models[0], "player_1")
        self.p2 = CluedoPlayer(self.player_models[1], "player_2")


        self.add_player(self.p1, initial_context="test")
        self.add_player(self.p2, initial_context="test")


    def _does_game_proceed(self):
        return self.turn < self.max_turns

    def _validate_player_response(self, player, utterance):
        return utterance.startswith("SUGGEST:")

    def _on_parse_response(self, player, utterance):
        return utterance.replace("SUGGEST:", "").strip(), False

    def _after_add_player_response(self, player, utterance):
        return
    
    def _advance_game(self, player, parsed_response):
        self.turn += 1

    def _parse_response(self, player, response):
        return super()._parse_response(player, response)


class CluedoGameBenchmark(GameBenchmark):

    def __init__(self, game_spec):
        super().__init__(game_spec)

    def get_description(self):
        return "Minimal 2-player Cluedo sandbox"

    def is_single_player(self):
        return False

    def create_game_master(self, experiment, player_models):
        return Cluedo(self.game_spec, experiment, player_models)