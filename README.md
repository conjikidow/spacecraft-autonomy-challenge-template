# Spacecraft Operations Challenge: Submission Template

[![License](https://img.shields.io/badge/license-MIT--0-blue.svg?style=flat)](LICENSE)

**English** | [日本語](README.ja.md)

Start here to write a strategy for the Spacecraft Operations Challenge.
A strategy operates a simulated spacecraft: it reads telemetry and schedules commands
so that the spacecraft accumulates a target delta-v without violating its limits.

The challenge problem, the simulator, and the `spacecraft-ops-challenge` command come from the
[`spacecraft-operations-challenge-core`](https://github.com/conjikidow/spacecraft-operations-challenge-core) package,
pinned to a release tag in `pyproject.toml`.

## Requirements

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
uv sync
```

## Running Your Strategy

Your strategy is the `MyStrategy` class in `submission/strategy.py`.
Run it on the `nominal` scenario:

```sh
uv run spacecraft-ops-challenge run submission/strategy.py:MyStrategy
```

The command prints how the run ended and its metrics, computed from the true spacecraft state.

List the available scenarios and run another one:

```sh
uv run spacecraft-ops-challenge scenarios
uv run spacecraft-ops-challenge run submission/strategy.py:MyStrategy --scenario thruster-degradation
```

Add `--json` to print the metrics as JSON.

## Writing Your Strategy

Put all of your code and files under `submission/`.
The directory of the strategy file is put first on the import path,
so `submission/strategy.py` can import other modules in `submission/`.
To read a data file next to your code, build its path from `Path(__file__).parent`.

Add the Python packages you need with uv, for example:

```sh
uv add numpy
```

## Working in the Notebook

```sh
uv run marimo edit app.py
```

The notebook shows the spacecraft, the mission, and the strategy API,
edits `submission/strategy.py`, runs it on a public scenario, checks the submission,
and submits it to an evaluation server.

## Checking Your Submission

```sh
uv run spacecraft-ops-challenge check
```

packs `submission/` and `pyproject.toml` into `submission.zip` in memory and evaluates it on all public scenarios
the way an evaluation server runs it: each scenario starts your strategy in a new Python process,
and packages of `pyproject.toml` that are missing are installed for the check only.
It prints the scores, a summary, and a table of the cases.
`uv run spacecraft-ops-challenge pack` writes `submission.zip` to a file without evaluating it.

## Submitting to an Evaluation Server

If your event provides an evaluation server, the organizers give you its URL and, if it needs one, a token:

```sh
export EVALUATION_SERVER_URL=<URL>
export EVALUATION_SERVER_TOKEN=<token>
uv run submit.py            # practice evaluation on hidden cases: waits for the result and shows it
uv run submit.py --final    # final submission: shows the receipt
```

On Windows, or instead of the environment variables, pass `--server <URL>` and `--token <token>`.
If you stop waiting for a practice evaluation, it continues on the server; `uv run submit.py --status <id>` shows it later.
You are identified by `git config user.email` and `git config user.name`;
`--participant-id` and `--participant-name` override them, and `uv run submit.py --help` lists all options.
The **Evaluation server** section of the notebook does the same.

If the server has a leaderboard, `uv run submit.py --board` shows it,
with whether final submissions are open and the time left, and the final ranking once it is published;
`--mine` lists only your practice submissions.
The **Leaderboard** section of the notebook shows the same.

## Documentation

The core repository documents the API and the challenge, at the commit this template uses:

- [Writing a Strategy](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.2.0/docs/strategy.md): lifecycle, mission brief, and commander
- [Commands and Timeline](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.2.0/docs/timeline.md): command types and ordering rules
- [Spacecraft Model](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.2.0/docs/spacecraft-model.md): state, dynamics, and telemetry
- [Simulation](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.2.0/docs/simulation.md): order of events and termination
- [Challenge Problem](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.2.0/docs/challenge.md): the problem and its public scenarios
- [Evaluation](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.2.0/docs/evaluation.md): the metrics printed after a run
- [Command-Line Runner](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.2.0/README.md#command-line-runner): options and exit status of `run`, `pack`, and `check`
- [Submission Archives](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.2.0/docs/submission.md): what `submission.zip` contains
- [Participant Packages](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.2.0/docs/dependencies.md): how the packages of `pyproject.toml` are reproduced
- [Scoring](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.2.0/docs/scoring.md): how a case and a suite are scored

## License

This template is licensed under [MIT-0](LICENSE), so you can build your submission on it without carrying a notice along.
Files you add are yours, and you may license them however you like.
