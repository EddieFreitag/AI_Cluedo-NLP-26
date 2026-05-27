import json


class CluedoGameState:
    def __init__(self, n_players, max_turns, solution, player_cards):
        self.current_turn = 0
        self.n_players = n_players
        self.max_turns = max_turns
        self.solution = solution
        self.player_cards = player_cards
        self.player_knowledge = {player: set(cards) for player, cards in player_cards.items()}

    def print_current_state(self):
        print(f"Turn: {self.current_turn}")
        print(f"Player Knowledge:")
        for player, knowledge in self.player_knowledge.items():
            print(f"{player}: {knowledge}")

    def update_state(self, response):
        # This function will update the game state based on the player's response
        # For simplicity, we will just print the response here
        print(f"Updating state with response: {response}")
        return "What happened."

class CluedoPlayer:
    def __init__(self, name, model):
        self.has_lost = False
        self.name = name
        self.model = model
        self.notebook = ""

    def get_response(self, message):
        return f"{self.name} is making a move."

class CluedoOrchestrator:
    def __init__(self, game_state, players):
        self.game_state = game_state
        self.players = players
        self.prompts = self.load_prompts()
    
    def load_prompts(self):
        with open("resources/prompts.json", "r") as f:
            prompts = json.load(f)
        return prompts

    def parse_response(self, response):
        # This function will parse the response from the player
        # For simplicity, we will just print the response here
        print(f"Parsing response: {response}")

    def inform_player(self, player, update, is_current_player):
        # This function will inform the player about the update in the game state
        # For simplicity, we will just print the update here
        if is_current_player:
            print(f"Informing {player.name} about their move: {update}")
        else:
            print(f"Informing {player.name} about other player's move: {update}")

    def advance_game(self):
        self.game_state.current_turn += 1
        print(f"Advancing to turn {self.game_state.current_turn}")
        if self.game_state.current_turn > self.game_state.max_turns:
            return False
        
        # so each player has a turn to make a move[suggest, accuse]
        # each player will be informed about the move and update their notebook
        for player in self.players:
            if player.has_lost:
                continue
            # player makes suggestion or accusation
            response = player.get_response(self.prompts["initial_prompt"])
            # game state is updated based on the action
            update = self.game_state.update_state(response)
            # update contains info such as "Player 1 suggested: miss scarlet" and "Player 2 showed a card to Player 1"
            for p in self.players:
                if p.has_lost:
                    continue
                self.inform_player(p, update, p==player)
    
        return True
    
    def start_game(self):
        while self.advance_game():
            pass
        self.end_game()

    def end_game(self):
        print("Game Over.")


class CluedoGame:
    def __init__(self):
        self.game_state = None
        self.players = []
        self.orchestrator = None
        
    def run_game(self, index=0):
        experiment = json.load(open("instances/instances.json", "r"))
        game = experiment["instances"][index]
        for player_name in game["player_cards"].keys():
            self.players.append(CluedoPlayer(player_name, None))

        self.game_state = CluedoGameState(
            n_players=experiment["n_players"],
            max_turns=experiment["max_turns"],
            solution=game["solution"],
            player_cards=game["player_cards"]
        )
        self.orchestrator = CluedoOrchestrator(self.game_state, self.players)
        self.orchestrator.start_game()

if __name__ == "__main__":
    game = CluedoGame()
    game.run_game()