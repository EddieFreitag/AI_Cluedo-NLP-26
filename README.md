# Multi-Agent Cluedo Benchmark for LLM Evaluation

## Overview

This project evaluates large language models (LLMs) using a multi-agent version of the deductive reasoning game Cluedo.
It is designed to measure reasoning, long-term information retention, planning, rule adherence, and decision-making under uncertainty.
The game environment generates rich, natural evaluation scenarios across many random instances, rather than relying solely on manually curated datasets.

## Motivation

LLMs are widely used in conversational and decision-making applications, but existing benchmarks often miss multi-step reasoning, memory-dependent strategies, and emergent multi-agent behavior.
Multi-Agent Cluedo provides a controlled game environment to assess:

- deductive reasoning
- long-term memory and notebook consistency
- risk-taking and decision quality
- rule adherence and action validity
- emergent opponent modeling and theory-of-mind behavior

## Research Objectives

### Overall Objective
Can Multi-Agent Cluedo serve as a reliable benchmark for evaluating reasoning and decision-making in LLMs?

### Key Research Questions

- How do deductive reasoning capabilities compare across model families and sizes?
- How well do models retain information across many turns?
- Can models follow game rules reliably while operating from a limited notebook-based state?

## Game Description

Cluedo is a deduction game where players infer a hidden solution with three elements: suspect, weapon, and room.
In this implementation, dice rolls and board movement are removed for simplicity.
Gameplay proceeds in discrete turns and each agent may perform one of two actions:

- **Suggestion**: propose a suspect–weapon–room combination
- **Accusation**: make a final guess of the full solution

Other players privately reveal a matching card when available, creating partial evidence used to eliminate possibilities.
Incorrect accusations remove the player from winning, while a correct accusation decides the winner.

### Memory and State Tracking

Each agent maintains a private notebook containing all gathered information.
This notebook is the only persistent memory available to the agent, along with new information received during each turn.
The notebook quality and consistency are therefore central to reasoning and decision-making.

## Repository Structure

```
README.md
environment.yml
cluedo/
  __init__.py
  experiment_runner.py
  game_master.py
  instancegenerator.py
  keys.json
  models.json
  test.py
  test_LLMs.py
  evaluation/
    analysis.py
    metrics.py
    evaluation_summary.json
    analysis_summary.json
  instances/
    instances.json
  resources/
    prompts.json
  results/
    *.jsonl
```

## Key Components

### `cluedo/experiment_runner.py`

- `ExperimentRunner`
  - orchestrates multi-agent game execution for a given language model
  - loads instance definitions and model configurations
  - writes game traces to `cluedo/results/{model}.jsonl`

### `cluedo/game_master.py`

- `CluedoPlayer` and model-specific subclasses
- `CluedoGameState`
- `CluedoOrchestrator`
- `CluedoGame`
- `GameLogger`

This module builds and manages the game state, constructs prompts, parses model responses, and logs full interaction traces.

### `cluedo/instancegenerator.py`

- `CluedoInstanceGenerator`
- generates random Cluedo game instances
- saves instances to `cluedo/instances/instances.json`

### `cluedo/evaluation/analysis.py`

- `CluedoAnalyzer`
  - loads `.jsonl` game trace files
  - computes per-game model statistics and summary information

### `cluedo/evaluation/metrics.py`

- `compute_metrics(stats)`
- `evaluate(summary)`
- `generate_evaluation_summary()`

This module transforms analysis summaries into final evaluation metrics across reasoning, memory, and decision-quality dimensions.

### `cluedo/test_LLMs.py`

- runs experiments, analysis, and metrics together
- uses `ExperimentRunner`, `CluedoAnalyzer`, and `evaluate()`
- saves results to `cluedo/results`, `cluedo/results/analysis_summary.json`, and `cluedo/evaluation/evaluation_summary.json`

## Evaluated Models

The benchmark includes a diverse set of LLMs across families and parameter scales, including:

- Google Gemini 3.1 Flash Lite
- Google Gemma 4 31B
- Google Gemma 3 12B
- Google Gemma 3 4B
- Cohere Command A
- Cohere Command R
- Cohere Command R7B 7B
- Meta Llama 4 Scout 17B
- Meta Llama 3 8B
- Mistral Ministral 3 14B
- Alibaba Qwen 2.5 7B
- NVIDIA Nemotron 3 Nano 4B

## Evaluation Metrics

Metrics are computed globally and by player position, allowing analysis of performance variation across turn order.

- `games` — number of evaluated games
- `win_rate` — fraction of games won
- `avg_win_turn` — mean winning turn
- `avg_info_gain_per_suggestion` — average information gain per suggestion
- `avg_suggestions` — mean suggestions per game
- `avg_repeated_suggestions` — repeated suggestion count
- `memory_score` — notebook consistency score
- `found_solution_rate` — fraction of games where solution was found
- `avg_found_solution_turn` — average turn when solution was found
- `perfect_knowledge_rate` — fraction with all cards known before accusation
- `solution_conversion_rate` — wins conditional on found solution
- `avg_risk` — mean accusation risk
- `wrong_accusations` — incorrect accusations count
- `invalid_notebook` — malformed notebook responses
- `invalid_action` — illegal or malformed actions
- `invalid_card` — invalid card references
- `reliability_score` — rule-following consistency

## Setup

### Using conda

```bash
conda env create -f environment.yml
conda activate nlp
```

If you are already inside a conda environment and want to update it:

```bash
conda env update -f environment.yml
```

### Required files

- `cluedo/models.json`
- `cluedo/instances/instances.json`
- `cluedo/resources/prompts.json`
- provider-specific keys in `cluedo/keys.json` or environment variables

## Running the benchmark

### Run the full LLM evaluation pipeline

From the repository root:

```bash
python cluedo/test_LLMs.py
```

This executes:

1. game generation and experiment execution for missing model results
2. analysis aggregation via `CluedoAnalyzer`
3. metric computation via `evaluate()`

### Run a single module directly

Analyze existing results:

```bash
python cluedo/evaluation/analysis.py
```

Generate evaluation metrics from summary files:

```bash
python cluedo/evaluation/metrics.py
```

## Notes

- The agent notebook is the only persistent state available to models.
- The benchmark uses centralized logging to capture full interaction traces, enabling replay and trace-based evaluation.
- API-based models are evaluated against a local baseline to control token usage.

## Conclusion

Multi-Agent Cluedo is a scalable, game-based benchmark for measuring LLM performance on multi-step reasoning, memory retention, and decision-making under uncertainty.
It is intended to complement existing benchmarks with a focus on long-horizon multi-agent behavior and notebook-based state tracking.
