import json
from collections import defaultdict, Counter
from pathlib import Path


class CluedoAnalyzer:

    def __init__(self, jsonl_path: str):
        self.jsonl_path = jsonl_path
        self.data = self._load()
        self.inst_games = self._load_instances()

    # -------------------------
    # LOAD DATA
    # -------------------------
    def _load(self):
        data = []
        with open(self.jsonl_path, "r") as f:
            for line in f:
                data.append(json.loads(line))
        return data
    
    def _load_instances(self):
        temp = json.load(open("cluedo/instances/instances.json", "r"))
        inst_games = temp['games']
        return inst_games

    # -------------------------
    # BASIC STATS
    # -------------------------
    def model_stats(self):

        stats = {
            "games": 0,
            "wins": 0,
            "losses": 0,
            "max_turns_reached": 
            {
                "num": 0,
                "turn": 0,
            },
            "all_players_lost": 
            {
                "num": 0,
                "turn": 0,
            }
        }

        player_cards = {}


        for exp in self.data:
            n_players = exp.get("players")
            
            for j, game in enumerate(exp["game_logs"]):
                stats["games"] += 1
                game_stats = {}
                suggested_cards = {}
                solution = frozenset(self.inst_games[j]['solution'].values())

                for i in range(n_players):
                    suggested_cards[f"Player {i+1}"] = set()

                    game_stats[f"Player {i+1}"] = {
                        "player_pos": i+1,
                        "model": "None",
                        "wins": 0,
                        "win_turn": 0,
                        "risk": 0,
                        "suggestions": 0,
                        "info_gain": 0,
                        "perfect_knowledge": 0,
                        "found_solution": 0,
                        "repeated_suggestion": 0,
                        "invalid_response_notebook": 
                        {
                            "num": 0,
                            "turn": 0,
                        },
                        "invalid_card": 
                        {
                            "num": 0,
                            "turn": 0,
                        },
                        "invalid_response_action": 
                        {
                            "num": 0,
                            "turn": 0,
                        },
                        "wrong_accusation": 
                        {
                            "num": 0,
                            "turn": 0,
                        },
                    }



                for event in game["events"]:
                    turn = event.get("turn")
                    player = event.get("player")

                    # get initial cards
                    if event.get("event") == "init_game":
                        player_cards = event.get("player_cards")
                        models = event.get("models")
                        for i, model in enumerate(models):
                            game_stats[f"Player {i+1}"]["model"] = model
                    elif event.get("event") == "player_action":
                        action = event.get("action")
                        # Accusation -> get turn, in case of win get turn of win,
                        if action.get("type") == "accuse":

                            # Calculate the risk the model takes, there are 21 cards and 18 it can possibly know
                            n_known = len(set(player_cards[player]))
                            risk = 1 - (n_known/18)
                            game_stats[player]["risk"] = risk

                            if action.get("has_won"):
                                stats["wins"] += 1
                                game_stats[player]["wins"] += 1
                                game_stats[player]["win_turn"] += turn
                            else: # suggest
                                game_stats[player]["wrong_accusation"]["num"] += 1
                                game_stats[player]["wrong_accusation"]["turn"] += turn
                        # Suggestion get number of suggestions and info gain
                        elif action.get("type") == "suggest":
                                game_stats[player]["suggestions"] += 1
                                sug_cards = {card for card in action.get("cards").values()}
                                suggestion = frozenset(sug_cards)

                                if suggestion == solution:
                                    game_stats[player]["found_solution"] = turn


                                if suggestion in suggested_cards[player]:
                                    game_stats[player]["repeated_suggestion"] += 1
                                suggested_cards[player].add(suggestion)

                                game_stats[player]["info_gain"] += (len(sug_cards - set(player_cards[player]))) / 3
                                
                                for res in action.get("reactions"):
                                    if res.get("action") == "shows_card":
                                        #print(f"Player cards before add: {player_cards[player]}")
                                        card = res.get("card")
                                        player_cards[player].append(card)
                                        #print(f"{player} cards after adding {card}: {player_cards[player]}")
                                        if 18 == len(set(player_cards[player])):
                                            game_stats[player]["perfect_knowledge"] = turn




                    # failures
                    elif event.get("event") == "player_excluded":
                        
                        game_stats[player][event.get("reason")]["num"] += 1
                        game_stats[player][event.get("reason")]["turn"] += turn

                    elif event.get("event") == "game_over":
                        stats[event.get("reason")]["num"] += 1
                        stats[event.get("reason")]["turn"] += turn
                        stats["losses"] += 1
                stats[f"game_{j}"] = game_stats
        
        return stats

    # -------------------------
    # SUMMARY
    # -------------------------
    def summary(self):
        
        return self.model_stats() 
    

if __name__ == "__main__":
    results_dir = Path("results")
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir.resolve()}")

    output_path = results_dir / "analysis_summary.json"
    json_paths = sorted(
        p for p in results_dir.rglob("*")
        if p.is_file()
        and p.suffix in {".json", ".jsonl"}
        and p.name != output_path.name
    )

    if not json_paths:
        print(f"No JSON files found under {results_dir.resolve()}")

    all_summaries = {}
    for path in json_paths:
        ca = CluedoAnalyzer(path)
        summary = ca.summary()
        all_summaries[path.relative_to(results_dir).as_posix()] = summary
        print(f"=== {path} ===")
        #print(summary)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=4, ensure_ascii=False)

    print(f"Saved aggregated analysis to {output_path}")
