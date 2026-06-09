from pathlib import Path
import json
from collections import defaultdict
import statistics


def compute_metrics(stats):

    n = len(stats["wins"])

    if n == 0:
        return {}

    games_with_solution = sum(
        stats["found_solution"]
        )

    expected_turns = []

    for turn in stats["found_solution_turn"]:
        if turn > 0:
            expected_turns.append(turn)
        else:
            expected_turns.append(10)


    invalid_total = (
        sum(stats["invalid_notebook"])
        + sum(stats["invalid_action"])
        + sum(stats["invalid_card"])
    )

    total_suggestions = sum(stats["suggestions"])

    return {
        "games": n,

        "win_rate":
            sum(stats["wins"]) / n,

        "avg_win_turn":
            statistics.mean(
                [x for x in stats["win_turn"] if x > 0]
            ) if any(x > 0 for x in stats["win_turn"]) else None,

        "avg_info_gain_per_suggestion":
            (
                sum(stats["info_gain"]) /
                max(sum(stats["suggestions"]), 1)
            ),

        "avg_suggestions":
            statistics.mean(stats["suggestions"]),

        "avg_repeated_suggestions":
            statistics.mean(stats["repeated"]),

        "memory_score":
            1 - (
                sum(stats["repeated"])
                / max(total_suggestions, 1)
            ),

        "found_solution_rate":
            games_with_solution / n,

        "avg_found_solution_turn":
            statistics.mean(expected_turns),

        "perfect_knowledge_rate":
            sum(stats["perfect_knowledge"]) / n,


        "solution_conversion_rate":
            (
                sum(stats["wins"]) / games_with_solution
            ) if games_with_solution > 0 else 0,

        "avg_risk":
            statistics.mean(stats["risk"]),

        "wrong_accusations":
            sum(stats["wrong_accusation"]),

        "invalid_notebook":
            sum(stats["invalid_notebook"]),

        "invalid_action":
            sum(stats["invalid_action"]),

        "invalid_card":
            sum(stats["invalid_card"]),

        "reliability_score":
            1 - (
                invalid_total
                / max(n, 1)
            )
    }


def evaluate(summary):

    results = {}

    for model_file, model_data in summary.items():

        target_model = model_file.replace(".jsonl", "")

        overall_stats = defaultdict(list)
        position_stats = defaultdict(lambda: defaultdict(list))

        for key, game in model_data.items():

            if not key.startswith("game_"):
                continue

            for _, player in game.items():

                if player["model"] != target_model:
                    continue

                pos = player["player_pos"]

                stat_sources = [overall_stats, position_stats[pos]]

                for stats in stat_sources:

                    stats["wins"].append(player["wins"])
                    stats["win_turn"].append(player["win_turn"])
                    stats["risk"].append(player["risk"] if player["found_solution"] else 0)
                    stats["suggestions"].append(player["suggestions"])
                    stats["info_gain"].append(player["info_gain"])
                    stats["repeated"].append(
                        player["repeated_suggestion"]
                    )

                    stats["found_solution"].append(
                        player["found_solution"] > 0
                    )

                    stats["found_solution_turn"].append(
                        player["found_solution"]
                    )

                    stats["perfect_knowledge"].append(
                        player["perfect_knowledge"] > 0
                    )

                    stats["invalid_notebook"].append(
                        player["invalid_response_notebook"]["num"]
                    )

                    stats["invalid_action"].append(
                        player["invalid_response_action"]["num"]
                    )

                    stats["invalid_card"].append(
                        player["invalid_card"]["num"]
                    )

                    stats["wrong_accusation"].append(
                        player["wrong_accusation"]["num"]
                    )

        model_results = {
            "overall": compute_metrics(overall_stats)
        }

        for pos, stats in position_stats.items():
            model_results[f"position_{pos}"] = compute_metrics(stats)

        results[target_model] = model_results

    return results


all_results = {}

for file in Path("results").glob("*.json"):

    with open(file, encoding="utf-8") as f:
        summary = json.load(f)

    all_results.update(evaluate(summary))


with open("results/evaluation_summary.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2)

print(json.dumps(all_results, indent=2))