import json
import argparse
from ollama import chat
from google import genai
from groq import Groq
from instancegenerator import SUSPECTS, WEAPONS, ROOMS
from utils.card_normalization import normalize_card_name

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="*")
    return parser.parse_args()

#abstract class for a cluedo player
class CluedoPlayer:
    def __init__(self, name: str, model: str, cards=[]):
        self.has_lost = False
        self.name = name
        self.model = model
        self.cards = cards
        self.context = ""
        self.notebook = ""

    def get_response(self, message: dict):
        pass

    def add_context(self, context: str):
        self.context = self.context + " " + context


class OllamaCluedoPlayer(CluedoPlayer):
    def __init__(self, name: str, model: str, cards=[]):
        super().__init__(name, model, cards)

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
    
class GeminiCluedoPlayer(CluedoPlayer):
    def __init__(self, name: str, model: str, cards=[], api_key=None):
        super().__init__(name, model, cards)
        self.client = genai.Client(api_key=api_key)
        

    def get_response(self, message: dict):
        # we need to convert the message dict to a string for gemini
        prompt = f"System: {message['system']}\nUser: {message['user']}"
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        return response.text
    
class GroqCluedoPlayer(CluedoPlayer):
    def __init__(self, name: str, model: str, cards=[], api_key=None):
        super().__init__(name, model, cards)
        self.client = Groq(api_key=api_key)

    def get_response(self, message: dict):
        response = self.client.chat.completions.create(messages=[
                {"role": "system", "content": message['system']}, 
                {"role": "user", "content": message['user']}
            ],
            model=self.model
        )
        return response.choices[0].message.content

class CluedoGameState:
    def __init__(self, n_players: int, max_turns: int, solution: dict, players: list):
        self.game_over = False
        self.current_turn = 0
        self.n_players = n_players
        self.max_turns = max_turns
        self.solution = solution
        self.players = players
        self.player_knowledge = {player.name: player.cards for player in self.players}
        print(f"Initial game state: {self.__dict__}")

    def print_current_state(self):
        print(f"Turn: {self.current_turn}")
        print(f"Player Knowledge:")
        for player, knowledge in self.player_knowledge.items():
            print(f"{player}: {knowledge}")

    def update_state(self, response, current_player: CluedoPlayer) -> tuple:
        # This function will update the game state based on the player's response        

        if response['action'].lower() == "suggest":
            # need to check wether a player holds any of the suggested cards and show one
            suspect = normalize_card_name(response['suspect'])
            weapon = normalize_card_name(response['weapon'])
            room = normalize_card_name(response['room'])
            print(f"--> {current_player.name} suggested: suspect: {suspect} weapon: {weapon} room: {room}.\n")

            current_player_info = f"You suggested: suspect: {suspect} weapon: {weapon} room: {room}. "
            other_player_info = f"{current_player.name} suggested: suspect: {suspect} weapon: {weapon} room: {room}. "
            card = ""
            shows_card = False

            for p in self.players:
                # if p holds a suggested card he shows it and we stop
                if p != current_player:
                    p_cards = [c.lower().strip() for c in p.cards]
                    if suspect.lower().strip() in p_cards:
                        card = suspect
                        shows_card = True
                        break
                    elif weapon.lower().strip() in p_cards:
                        card = weapon
                        shows_card = True
                        break
                    elif room.lower().strip() in p_cards:
                        card = room
                        shows_card = True
                        break
                    else:
                        current_player_info += f"{p.name} can't show any card to you. "
                        other_player_info += f"{p.name} can't show any card to {current_player.name}. "

            # Some player held a suggested card
            if shows_card:
                print(f"--> {p.name} shows {card} to {current_player.name}.\n")
                self.player_knowledge[current_player.name].append(card)
                current_player_info += f"{p.name} shows you the card: {card}."
                other_player_info += f"{p.name} show a card to {current_player.name}."

            # No player can disprove the suggestion.
            else:
                clue = f"None of the players could disprove {current_player.name}'s suggestion."
                print(f"--> {clue}\n")
                current_player_info += clue
                other_player_info += clue
            
        # accusation if correct game-over and win otherwise current_player lost
        elif response["action"].lower() == "accuse":
            # check if solution is true
            print(f"--> {current_player.name} made an accusation: suspect: {response['suspect']} weapon: {response['weapon']} room: {response['room']}.\n")
            if self.solution == {
                "suspect": normalize_card_name(response["suspect"]),
                "weapon": normalize_card_name(response["weapon"]),
                "room": normalize_card_name(response["room"]),
            }:
                print(f"--> {current_player.name} has correctly identified the solution!")
                self.game_over = True
                current_player_info = f"Your accusation was correct you win!"
                other_player_info = f"{current_player.name}'s accusation is correct he won. The game is over."    
            else:
                print(f"--> {current_player.name}'s accusation is wrong. He has lost and can't continue to play. However, he will continue to answer to your suggestions.\n")
                current_player.has_lost = True
                current_player_info = f"Your accusation {response} was wrong, the correct solution is {self.solution}. You lost the game."
                other_player_info = f"{current_player.name} has made the accusation: {response}. It was wrong. He has lost and can't continue to play. However, he will continue to answer to your suggestions."
        
        
        return (current_player_info, other_player_info)


class CluedoOrchestrator:
    #  TODO set initial context for each player, then just append the updates to the context and when creating the prompt for the player use their context + the notebook
    def __init__(self, game_state: CluedoGameState, players: list):
        self.game_state = game_state
        self.players = players
        self.prompts = self.load_prompts()
        self.set_initial_context()
        print("Orchestrator initialized with game state and players.")
    
    def load_prompts(self):
        with open("resources/prompts.json", "r") as f:
            prompts = json.load(f)
        return prompts

    def set_initial_context(self):
         for player in self.players:
            initial_context = self.prompts["initial_context"].replace("$PLAYER", player.name).replace("$CARDS", str(player.cards)).replace("$WEAPONS", str(WEAPONS)).replace("$ROOMS", str(ROOMS)).replace("$SUSPECTS", str(SUSPECTS))
            player.add_context(initial_context)

    def parse_response(self, response) -> tuple:
        # This function will parse the response from the player
        # For simplicity, we will just print the response here
        try:
            if isinstance(response, str):
                return json.loads(response), True

            return json.loads(response["message"]["content"]), True
        except Exception as e:
            self.game_state.game_over = True
            print(f"Error: {e}")
            print(f"Not Json format: {response}")
            return {"notebook": ""}, False


    def inform_player(self, player: CluedoPlayer, update: tuple, is_current_player: bool) -> None:
        # This function will inform the player about the update in the game state
        # Add info to context
        current_player_info, other_player_info = update
        # for other players we want to replace their name with "you" for easier understanding
        other_player_info = other_player_info.replace(player.name, "You")

        prompt = self.create_prompt("update", player, update=current_player_info if is_current_player else other_player_info)
        response, is_valid = self.parse_response(player.get_response(prompt))
        if not is_valid:
            print(f"--> Invalid response from {player.name} when informing about the update. Excluding player.")
            player.has_lost = True
            return
        player.notebook = response['notebook']
        
        

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

            #Debug
            print(f"\t{player.name}'s turn.\n")
            prompt = self.create_prompt("action", player)
            response, is_valid = self.parse_response(player.get_response(prompt))
            if not is_valid:
                print(f"--> Invalid response from {player.name} when making a move. Excluding player.")
                player.has_lost = True
                continue
            # game state is updated based on the action
            update = self.game_state.update_state(response, player)

            # update contains info such as "Player 1 suggested: miss scarlet" and "Player 2 showed a card to Player 1"
            for p in self.players:
                if p.has_lost:
                    continue
                self.inform_player(p, update, p==player)
            #print(f"Context for {player.name}: {player.context}\n")
            print(f"--> Notebook for {player.name}:\n{player.notebook}\n")
    
        return not self.game_state.game_over
    
    def create_prompt(self, type: str, player: CluedoPlayer, update="") -> str:
        # TODO rewrite this to use the context
        # prompts the player to take an action
        if type=="action":
            system_prompt_action = self.prompts["system_prompt_action"]
            # replace placeholders with variables
            user_prompt_action = f"{player.context}\n\n{self.prompts['action_prompt'].replace('$NOTEBOOK', player.notebook)}"
            prompt = {
                    "system": system_prompt_action,
                    "user": user_prompt_action
                }
            return prompt
        # prompt the player to update their notebook for that we need the update
        elif type=="update":
            system_prompt_notebook = self.prompts["system_prompt_notebook"]
            user_prompt_notebook = f"{player.context}\n\n{self.prompts['notebook_prompt'].replace('$NOTEBOOK', player.notebook).replace('$INFO', update)}"
            # add context to player after creating the prompt so it isnt shown twice
            #player.add_context(update)
            prompt = {
                    "system": system_prompt_notebook,
                    "user": user_prompt_notebook
                }
            return prompt
    
    def start_game(self):
        print("Starting game loop.")
        while self.advance_game():
            pass
        self.end_game()

    def end_game(self):
        print("Game Over.")


class CluedoGame:
    def __init__(self, models):
        print(f"Initializing game with models: {models}")
        self.game_state = None
        self.players = []
        model_api_mapping = json.load(open("models.json", "r"))
        for i, model in enumerate(models):
            if model in model_api_mapping["ollama"]:
                self.players.append(OllamaCluedoPlayer(f"Player {i+1}", model))
            elif model in model_api_mapping["gemini"]:
                key = json.load(open("keys.json", "r"))["gemini"]
                self.players.append(GeminiCluedoPlayer(f"Player {i+1}", model, api_key=key))
            elif model in model_api_mapping["groq"]:
                key = json.load(open("keys.json", "r"))["groq"]
                self.players.append(GroqCluedoPlayer(f"Player {i+1}", model, api_key=key))
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