import json
from collections import defaultdict, Counter


class CluedoAnalyzer:

    def __init__(self, jsonl_path: str):
        self.jsonl_path = jsonl_path
        self.data = self._load()

    # -------------------------
    # LOAD DATA
    # -------------------------
    def _load(self):
        data = []
        with open(self.jsonl_path, "r") as f:
            for line in f:
                data.append(json.loads(line))
        return data

    # -------------------------
    # BASIC STATS
    # -------------------------
    def model_stats(self):

        stats = {
            "games": 0,
            "wins": 0,
            "losses": 0,
        }

        breakdown = defaultdict(int)

        for exp in self.data:

            for game in exp["game_logs"]:

                stats["games"] += 1

                for event in game["events"]:

                    if event.get("event") == "player_action":
                        action = event.get("action")
                        if action.get("type") == "accuse":
                            if action.get("has_won"):
                                stats["wins"] += 1
                                stats[event.get("player")] += 1
                            else:
                                stats['losses'] +=1
                                breakdown["wrong_accusation"] += 1
                                breakdown[event.get("player")] += 1
                    # failures
                    elif event.get("event") == "player_excluded":
                        breakdown[event.get("reason")] += 1
                        breakdown[event.get("player")] += 1
                        stats["losses"] += 1
                    elif event.get("event") == "game_over":
                        breakdown[event.get("reason")] += 1
                        stats["losses"] += 1
        
        
        return stats, dict(breakdown)

    # -------------------------
    # INFORMATION GAIN (basic version)
    # -------------------------
    def info_gain_proxy(self):

        gains = []

        for exp in self.data:
            for game in exp["game_logs"]:

                known = set()
                per_turn_gain = []

                for event in game["events"]:

                    if event["event_type"] == "knowledge_update":

                        before = len(known)
                        known.update(event.get("added_not_solution", []))
                        after = len(known)

                        per_turn_gain.append(after - before)

                if per_turn_gain:
                    gains.append(sum(per_turn_gain))

        return {
            "avg_info_gain": sum(gains) / max(1, len(gains))
        }

    # -------------------------
    # SUMMARY
    # -------------------------
    def summary(self):
        stats, breakdown = self.model_stats()
        return {
            "model_stats": stats,
            "breakdown": breakdown,
            #"info_gain": self.info_gain_proxy()
        }
    

if __name__ == "__main__":
    ca = CluedoAnalyzer("results/llama3:8b.jsonl")
    print(ca.summary())
    cb = CluedoAnalyzer("results/gemma3:12b.jsonl")
    print(cb.summary())
    cb = CluedoAnalyzer("results/meta-llama/llama-4-scout-17b-16e-instruct.jsonl")
    print(cb.summary())