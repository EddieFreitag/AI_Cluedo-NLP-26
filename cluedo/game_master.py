import json
import argparse
from ollama import chat
from instancegenerator import SUSPECTS, WEAPONS, ROOMS

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="*")
    return parser.parse_args()

class CluedoPlayer:
    def __init__(self, name: str, model: str, cards=[]):
        self.has_lost = False
        self.name = name
        self.model = model
        self.cards = cards
        self.notebook = ""

    def get_response(self, message: dict):
        response = chat(
            model=self.model,
            messages=[
                {
                    'role': 'system',
                    'content': message['system']
                },
                {
                    'role': 'user',
                    'content': message['user']
                }
            ]
        )
        return response

class CluedoGameState:
    def __init__(self, n_players: int, max_turns: int, solution: dict, players: list):
        self.game_over = False
        self.current_turn = 0
        self.n_players = n_players
        self.max_turns = max_turns
        self.solution = solution
        self.players = players
        self.player_knowledge = {player.name: player.cards for player in self.players}

    def print_current_state(self):
        print(f"Turn: {self.current_turn}")
        print(f"Player Knowledge:")
        for player, knowledge in self.player_knowledge.items():
            print(f"{player}: {knowledge}")

    def update_state(self, response, current_player: CluedoPlayer) -> tuple:
        # This function will update the game state based on the player's response        

        if response['action'].lower() == "suggest":
            # need to check wether a player holds any of the suggested cards and show one
            print(f"{current_player.name} makes move: {response}")
            suspect = response['suspect']
            weapon = response['weapon']
            room = response['room']
            current_player_info = ""
            other_player_info = ""
            card = ""
            shows_card = False
            for p in self.players:
                # if p holds a suggested card he shows it and we stop
                if p != current_player:
                    p_cards = [c.lower() for c in p.cards]
                    if suspect.lower() in p_cards:
                        card = suspect
                        shows_card = True
                        break
                    elif weapon.lower() in p.cards:
                        card = weapon
                        shows_card = True
                        break
                    elif room.lower() in p.cards:
                        card = room
                        shows_card = True
                        break
                    else:
                        current_player_info += f"{p.name} can't show any card to you. "
                        other_player_info += f"{p.name} can't show any card to {current_player.name}. "
            # Some player held a suggested card
            if shows_card:
                current_player_info += f"{p.name} shows you the card: {card}"
                other_player_info += f"{p.name} shows a card to {current_player.name}"
            # No player can disprove the suggestion.
            else:
                clue = f"None of the players could disprove {current_player.name}'s suggestion."
                current_player_info += clue
                other_player_info += clue
            
        # accusation if correct game-over and win otherwise current_player lost
        elif response["action"].lower() == "accuse":
            # check if solution is true
            if self.solution == {
                "suspect": response["suspect"],
                "weapon": response["weapon"],
                "room": response["room"],
            }:
                self.game_over = True
                current_player_info = f"Your accusation was correct you win!"
                other_player_info = f"{current_player.name}'s accusation is correct he won. The game is over."    
            else:
                current_player.has_lost = True
                current_player_info = f"Your accusation {response} was wrong, the correct solution is {self.solution}. You lost the game."
                other_player_info = f"{current_player.name} has made the accusation: {response}. It was wrong. He has lost and can't continue to play. However, he will continue to answer to your suggestions."
        
        
        return (current_player_info, other_player_info)


class CluedoOrchestrator:
    def __init__(self, game_state: CluedoGameState, players: list):
        self.game_state = game_state
        self.players = players
        self.prompts = self.load_prompts()
    
    def load_prompts(self):
        with open("resources/prompts.json", "r") as f:
            prompts = json.load(f)
        return prompts

    def parse_response(self, response) -> dict:
        # This function will parse the response from the player
        # For simplicity, we will just print the response here
        try:
            parsed_response = json.loads(response['message']['content']) 
            return parsed_response
        except:
            self.game_state.game_over = True
            print(f"Not Json format: {response}")


    def inform_player(self, player: CluedoPlayer, update: tuple, is_current_player: bool):
        # This function will inform the player about the update in the game state
        # For simplicity, we will just print the update here
        current_player_info, other_player_info = update
        if is_current_player:
            prompt = self.create_prompt("update", player, current_player_info)
        else:
            prompt = self.create_prompt("update", player, other_player_info)
        response = self.parse_response(player.get_response(prompt))
        player.notebook = response['notebook']
        print(f"{player.name}'s notebook:\n {player.notebook}\n\n")
        
        

    def advance_game(self) -> bool:
        self.game_state.current_turn += 1
        if self.game_state.current_turn > self.game_state.max_turns:
            self.game_state.game_over = True
            return not self.game_state.game_over
        
        print(f"Advancing to turn {self.game_state.current_turn}\n")
        # so each player has a turn to make a move[suggest, accuse]
        # each player will be informed about the move and update their notebook
        for player in self.players:
            if player.has_lost:
                continue
            # player makes suggestion or accusation
            prompt = self.create_prompt("action", player)
            response = self.parse_response(player.get_response(prompt))
            
            # game state is updated based on the action
            update = self.game_state.update_state(response, player)
            # update contains info such as "Player 1 suggested: miss scarlet" and "Player 2 showed a card to Player 1"
            print("-"*60)
            print("Players update their notebooks:")
            for p in self.players:
                if p.has_lost:
                    continue
                self.inform_player(p, update, p==player)
            print("-"*60)
    
        return not self.game_state.game_over
    
    def create_prompt(self, type: str, player: CluedoPlayer, update="") -> dict:
        # prompts the player to take an action
        if type=="action":
            system_prompt_action = self.prompts["system_prompt_action"]
            # replace placeholders with variables
            user_prompt_action = self.prompts["action_prompt"].replace("$WEAPONS", str(WEAPONS)).replace("$ROOMS", str(ROOMS)).replace("$SUSPECTS", str(SUSPECTS)).replace("$CARDS", str(player.cards)).replace("$NOTEBOOK", player.notebook).replace("PLAYER", player.name)
            prompt = {
                    "system": system_prompt_action,
                    "user": user_prompt_action
                }
            return prompt
        # prompt the player to update their notebook for that we need the update
        elif type=="update":
            system_prompt_notebook = self.prompts["system_prompt_notebook"]
            user_prompt_notebook = self.prompts["notebook_prompt"].replace("$NOTEBOOK", player.notebook).replace("$INFO", update).replace("$CARDS", str(player.cards)).replace("$PLAYER", player.name)
            prompt = {
                    "system": system_prompt_notebook,
                    "user": user_prompt_notebook
                }
            return prompt
    
    def start_game(self):
        while self.advance_game():
            pass
        self.end_game()

    def end_game(self):
        print("Game Over.")


class CluedoGame:
    def __init__(self, models):
        self.game_state = None
        self.players = []
        for i, model in enumerate(models):
            self.players.append(CluedoPlayer(f"Player {i+1}", model))
        self.orchestrator = None
        
    def run_game(self, index=0):
        experiment = json.load(open("instances/instances.json", "r"))
        game = experiment["instances"][index]

        # give cards to players
        for player in self.players:
            player.cards = game['player_cards'][player.name]

        self.game_state = CluedoGameState(
            n_players=experiment["n_players"],
            max_turns=experiment["max_turns"],
            solution=game["solution"],
            players = self.players
        )
        self.orchestrator = CluedoOrchestrator(self.game_state, self.players)
        self.orchestrator.start_game()

if __name__ == "__main__":
    args = parse_args()
    game = CluedoGame(args.models)
    game.run_game()