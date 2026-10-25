# Spacecraft Operations Challenge: Submission Template

[![License](https://img.shields.io/badge/license-MIT--0-blue.svg?style=flat)](LICENSE)

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

## Documentation

The core repository documents the API and the challenge, at the commit this template uses:

- [Writing a Strategy](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.0/docs/strategy.md): lifecycle, mission brief, and commander
- [Commands and Timeline](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.0/docs/timeline.md): command types and ordering rules
- [Spacecraft Model](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.0/docs/spacecraft-model.md): state, dynamics, and telemetry
- [Simulation](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.0/docs/simulation.md): order of events and termination
- [Challenge Problem](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.0/docs/challenge.md): the problem and its public scenarios
- [Evaluation](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.0/docs/evaluation.md): the metrics printed after a run
- [Command-Line Runner](https://github.com/conjikidow/spacecraft-operations-challenge-core/blob/v0.1.0/README.md#command-line-runner): options and exit status

## License

This template is licensed under [MIT-0](LICENSE), so you can build your submission on it without carrying a notice along.
Files you add are yours, and you may license them however you like.
