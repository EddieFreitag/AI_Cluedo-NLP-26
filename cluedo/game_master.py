import json
import re
from time import sleep
from ollama import chat
from google import genai
from groq import Groq
import cohere
from instancegenerator import SUSPECTS, WEAPONS, ROOMS
from utils.card_normalization import normalize_card_name


# Resoponse schemas for Ollama models
ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["suggest", "accuse"]},
        "suspect": {"type": "string"},
        "weapon": {"type": "string"},
        "room": {"type": "string"}
    },
    "required": ["action", "suspect", "weapon", "room"]
}

NOTEBOOK_SCHEMA = {
    "type": "object",
    "properties": {
        "notebook": {"type": "string"}
    },
    "required": ["notebook"]
}


#abstract class for a cluedo player
class CluedoPlayer:
    def __init__(self, name: str, model: str, cards=[]):
        self.has_lost = False
        self.name = name
        self.model = model
        self.cards = cards
        self.context = ""
        self.notebook = ""

    def get_response(self, message: dict, schema=None):
        raise NotImplementedError

    def add_context(self, context: str):
        self.context = self.context + " " + context


class OllamaCluedoPlayer(CluedoPlayer):
    def __init__(self, name: str, model: str, cards=[]):
        super().__init__(name, model, cards)

    def get_response(self, message: dict, schema=None):

        kwargs = {}
        if schema is not None:
            kwargs["format"] = schema

        response = chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': message['system']},
                {'role': 'user', 'content': message['user']}
            ],
            **kwargs
        )
        return response
    

class GeminiCluedoPlayer(CluedoPlayer):
    def __init__(self, name: str, model: str, cards=[], api_key=None):
        super().__init__(name, model, cards)
        self.client = genai.Client(api_key=api_key)
        # set timeout so requests dont surpass rpm
        if model == "gemini-3.5-flash":
            # 5 rpm
            self.timeout = 8
        else:
            #15 rpm
            self.timeout = 3
        

    def get_response(self, message: dict, schema=None):
        # Sleep for timeout
        sleep(self.timeout)
        # we need to convert the message dict to a string for gemini
        prompt = f"System: {message['system']}\nUser: {message['user']}"
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        return response.text
    

class GroqCluedoPlayer(CluedoPlayer):
    def __init__(self, name: str, model: str, cards=[], api_key=None):
        super().__init__(name, model, cards)
        self.client = Groq(api_key=api_key)

    def get_response(self, message: dict, schema=None):
        response = self.client.chat.completions.create(messages=[
                {"role": "system", "content": message['system']}, 
                {"role": "user", "content": message['user']}
            ],
            model=self.model
        )
        return response.choices[0].message.content
    

class CohereCluedoPlayer(CluedoPlayer):
    def __init__(self, name: str, model: str, cards=[], api_key=None):
        super().__init__(name, model, cards)
        self.client = cohere.ClientV2(api_key=api_key)
        self.timeout = 3

    def get_response(self, message: dict, schema=None):
        sleep(self.timeout)
        response = self.client.chat(
            messages=[
                {"role": "system", "content": message['system']}, 
                {"role": "user", "content": message['user']}
            ],
            model=self.model
        )
        return response.message.content[0].text


class CluedoGameState:

    def __init__(self, n_players: int, max_turns: int, solution: dict, players: list):
        self.game_over = False
        self.current_turn = 0
        self.n_players = n_players
        self.max_turns = max_turns
        self.solution = solution
        self.players = players
        self.winner = None | CluedoPlayer
        print(f"Initial game state: {self.__dict__}")
        for player in self.players:
            print(f"{player.name}: {player.model}")

    def update_state(self, response, current_player: CluedoPlayer) -> tuple:
        # This function will update the game state based on the player's response
        has_won = False    
        try:    
            suspect = normalize_card_name(response['suspect'])
            weapon = normalize_card_name(response['weapon'])
            room = normalize_card_name(response['room'])
        except Exception as e:
            print(e)
            print("--> Error normalizing card.")
            current_player_info = ""
            current_player.has_lost = True
            other_player_info = f"{current_player.name} has made a move containing a card that does not belong to the game. He has lost and can't continue to play. However, he will continue to answer to your suggestions."
            log = {
                "event": "player_excluded",
                "reason": "invalid_card",
                "turn": self.current_turn,
                "player": current_player.name,
                "model": current_player.model,
                "raw_response": response
            }
            return current_player_info, other_player_info, log, has_won

        log = {
            "type": "",
            "cards":
            {
                "suspect": suspect,
                "weapon": weapon,
                "room": room,
            }
        }
        
        if response['action'].lower() == "suggest":
            log["type"] = "suggest"
            log["reactions"] = []
            # need to check wether a player holds any of the suggested cards and show one
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
                        log["reactions"].append(
                            {
                                "player": p.name,
                                "model": p.model,
                                "action": "cannot_disprove",
                            }
                        )

            # Some player held a suggested card
            if shows_card:
                print(f"--> {p.name} shows {card} to {current_player.name}.\n")
                current_player_info += f"{p.name} shows you their card: {card}."
                other_player_info += f"{p.name} show a card to {current_player.name}."
                log["reactions"].append(
                    {
                        "player": p.name,
                        "model": p.model,
                        "action": "shows_card",
                        "card": card,
                    }
                )
                
            # No player can disprove the suggestion.
            else:
                clue = f"None of the other players could disprove {current_player.name}'s suggestion."
                print(f"--> {clue}\n")
                current_player_info += clue
                other_player_info += clue
            
        # accusation if correct game-over and win otherwise current_player lost
        elif response["action"].lower() == "accuse":
            log["type"] = "accuse"
            # check if solution is true
            print(f"--> {current_player.name} made an accusation: suspect: {suspect}, weapon: {weapon}, room: {room}.\n")
            if self.solution == {
                "suspect": suspect,
                "weapon": weapon,
                "room": room
            }:
                print(f"--> {current_player.name} has correctly identified the solution!")
                self.game_over = True
                has_won = True
                self.winner = current_player
                current_player_info = f"Your accusation was correct you win!"
                other_player_info = f"{current_player.name}'s accusation is correct he won. The game is over."
                log["has_won"] = has_won
            else:
                print(f"--> {current_player.name}'s accusation is wrong. He has lost and can't continue to play. However, he will continue to answer to your suggestions.\n")
                current_player.has_lost = True
                log["has_won"] = has_won
                current_player_info = f"Your accusation {response} was wrong, the correct solution is {self.solution}. You lost the game."
                other_player_info = f"{current_player.name} has made the accusation: {response}. It was wrong. He has lost and can't continue to play. However, he will continue to answer to your suggestions."
        
        
        return current_player_info, other_player_info, log, has_won


class GameLogger:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.events = []

    def log(self, event: dict):
        self.events.append(event)
    
    def finalize(self):
        return {"game_id": self.game_id, "events": self.events}


class CluedoOrchestrator:
    def __init__(self, game_state: CluedoGameState, logger: GameLogger, players: list):
        self.game_state = game_state
        self.logger = logger
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
        try:
            # Extract raw text from different providers
            if isinstance(response, str):
                text = response

            elif isinstance(response, dict):
                text = response["message"]["content"]

            elif hasattr(response, "message"):
                text = response.message.content

            else:
                text = str(response)

            # Remove <think>...</think> blocks (Qwen)
            text = re.sub(
                r"<think>.*?</think>",
                "",
                text,
                flags=re.DOTALL | re.IGNORECASE
            )

            # Remove markdown code fences
            text = re.sub(
                r"```(?:json)?",
                "",
                text,
                flags=re.IGNORECASE
            )

            text = text.strip()

            # Extract first JSON object
            match = re.search(
                r"\{.*\}",
                text,
                flags=re.DOTALL
            )

            if not match:
                raise ValueError("No JSON object found")

            json_text = match.group(0)

            parsed = json.loads(json_text)

            return parsed, True

        except Exception as e:
            print(f"Error: {e}")
            print(f"Not Json format: {response}")

            # Don't end the whole game because one model
            # wrapped JSON in weird formatting
            return {"notebook": ""}, False

    def inform_player(self, player: CluedoPlayer, current_player_info, other_player_info, is_current_player: bool) -> None:
        # This function will inform the player about the update in the game state        
        # for other players we want to replace their name with "you" for easier understanding
        other_player_info = other_player_info.replace(player.name, "You")

        prompt = self.create_prompt("update", player, update=current_player_info if is_current_player else other_player_info)
        response, is_valid = self.parse_response(player.get_response(prompt, schema=NOTEBOOK_SCHEMA))
        if not is_valid:
            print(f"--> Invalid response from {player.name} when updating the notebook. Excluding player.")
            player.has_lost = True

            self.logger.log({
                "event": "player_excluded",
                "reason": "invalid_response_notebook",
                "turn": self.game_state.current_turn,
                "player": player.name,
                "model": player.model,
                "raw_response": response
            })
        else:
            self.logger.log({
                "event": "player_notebook",
                "turn": self.game_state.current_turn,
                "player": player.name,
                "model": player.model,
                "is_valid": True,
                "raw_response": response['notebook']
            })
            player.notebook = response['notebook']
        
    def advance_game(self) -> bool:
        self.game_state.current_turn += 1
        if self.game_state.current_turn > self.game_state.max_turns:
            self.game_state.game_over = True
            print(f"--> Max turns reached.")
            self.logger.log({
                "event": "game_over",
                "reason": "max_turns_reached",
                "turn": self.game_state.current_turn,
                "winner": None,
            })

            return not self.game_state.game_over
        
        # check if all players have lost
        if all(player.has_lost for player in self.players):
            print(f"--> Round {self.game_state.current_turn}: All players have lost.")
            self.game_state.game_over = True

            self.logger.log({
                "event": "game_over",
                "reason": "all_players_lost",
                "turn": self.game_state.current_turn,
                "winner": None,
            })

            return not self.game_state.game_over
        
        print(f"Advancing to turn {self.game_state.current_turn}\n")
        # so each player has a turn to make a move[suggest, accuse]
        # each player will be informed about the move and update their notebook
        for player in self.players:
            if player.has_lost:
                continue
            # player makes suggestion or accusation
            print(f"\t{player.name}'s turn.\n")
            prompt = self.create_prompt("action", player)
            response, is_valid = self.parse_response(player.get_response(prompt, schema=ACTION_SCHEMA))

            if not is_valid:
                print(f"--> Invalid response from {player.name} when making a move. Excluding player.")
                player.has_lost = True

                self.logger.log({
                    "event": "player_excluded",
                    "reason": "invalid_response_action",
                    "turn": self.game_state.current_turn,
                    "player": player.name,
                    "model": player.model,
                    "raw_response": response
                })
                continue

            # game state is updated based on the action
            current_player_info, other_player_info, logs, has_won = self.game_state.update_state(response, player)

            self.logger.log({
                "event": "player_action",
                "turn": self.game_state.current_turn,
                "player": player.name,
                "model": player.model,
                "action": logs
            })

            # if player has won then we end
            if has_won:
                break

            # update contains info such as "Player 1 suggested: miss scarlet" and "Player 2 showed a card to Player 1"
            for p in self.players:
                if p.has_lost:
                    continue
                self.inform_player(p, current_player_info, other_player_info, p==player)
            #print(f"Context for {player.name}: {player.context}\n")
            #print(f"--> Notebook for {player.name}:\n{player.notebook}\n")
    
        return not self.game_state.game_over
    
    def create_prompt(self, type: str, player: CluedoPlayer, update="") -> str:
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
    def __init__(self, models, instance, n_players, max_turns, id):
        self.models = models
        self.instance = instance
        self.n_players = n_players
        self.max_turns = max_turns
        self.id = id

    def run_game(self):
        players = []
        model_api_mapping = json.load(open("models.json", "r"))
        for i, model in enumerate(self.models):
            if model in model_api_mapping["ollama"]:
                players.append(OllamaCluedoPlayer(f"Player {i+1}", model))
            elif model in model_api_mapping["gemini"]:
                key = json.load(open("keys.json", "r"))["gemini"]
                players.append(GeminiCluedoPlayer(f"Player {i+1}", model, api_key=key))
            elif model in model_api_mapping["groq"]:
                key = json.load(open("keys.json", "r"))["groq"]
                players.append(GroqCluedoPlayer(f"Player {i+1}", model, api_key=key))
            elif model in model_api_mapping["cohere"]:
                key = json.load(open("keys.json", "r"))["cohere"]
                players.append(CohereCluedoPlayer(f"Player {i+1}", model, api_key=key))
            else:
                print("--> Warning no players matched.")
                return
        # give cards to players
        for player in players:
            player.cards = self.instance['player_cards'][player.name]

        logger = GameLogger(self.id)
        logger.log(
            {
                "event": "init_game",
                "models": self.models,
                "player_cards": self.instance['player_cards']
            }
        )

        game_state = CluedoGameState(
            n_players=self.n_players,
            max_turns=self.max_turns,
            solution=self.instance["solution"],
            players = players
        )
        self.orchestrator = CluedoOrchestrator(game_state, logger, players)
        self.orchestrator.start_game()
