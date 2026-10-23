import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")

with app.setup:
    import contextlib
    import dataclasses
    import importlib
    import importlib.util
    import io
    import os
    import sys
    import traceback
    import zipfile
    from pathlib import Path

    import marimo as mo
    from spacecraft_ops_challenge import Strategy
    from spacecraft_ops_challenge.challenge import problem, scenario, scenario_names
    from spacecraft_ops_challenge.evaluation import evaluate
    from spacecraft_ops_challenge.results import TerminationReason
    from spacecraft_ops_challenge.simulation import run

    SUBMISSION_DIR = (Path(__file__).parent / "submission").resolve()
    STRATEGY_FILE = SUBMISSION_DIR / "strategy.py"
    STRATEGY_CLASS = "MyStrategy"


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Spacecraft Operations Challenge

    Your solution is the `submission/` directory.
    The entry point is the `MyStrategy` class in `submission/strategy.py`,
    and every other file it needs (Python modules, planning models, model weights,
    configuration, data) also belongs under `submission/`.

    1. Edit the files under `submission/`.
    2. Select a public scenario and click **Run public scenario**.
       Every run loads the current files from disk,
       so there is no need to restart this notebook.
    3. Inspect the result and iterate.
    4. Download `submission.zip` when you need the bundle.
    """)
    return


@app.cell(hide_code=True)
def _():
    def _value_rows(obj, prefix=""):
        rows = []
        for field in dataclasses.fields(obj):
            value = getattr(obj, field.name)
            if dataclasses.is_dataclass(value):
                rows.extend(_value_rows(value, f"{prefix}{field.name}."))
            else:
                rows.append(f"| `{prefix}{field.name}` | {value} |")
        return rows

    def _table(title, rows):
        return "\n".join([f"**{title}**", "", "| Field | Value |", "|---|---|", *rows])

    _problem = problem()
    _goal_rows = [
        f"| `{name}` | {getattr(_problem, name)} |"
        for name in ("target_delta_v_mps", "time_limit_s", "decision_period_s")
    ]
    mo.vstack(
        [
            mo.md("## Mission"),
            mo.md(
                "The public problem shared by all scenarios. "
                "Units are part of every field name."
            ),
            mo.hstack(
                [
                    mo.md(_table("Goal and timing", _goal_rows)),
                    mo.md(_table("Safety limits", _value_rows(_problem.limits))),
                    mo.md(_table("Initial state", _value_rows(_problem.initial_state))),
                ],
                wrap=True,
                justify="start",
                gap=2,
            ),
            mo.accordion(
                {
                    "Nominal spacecraft parameters": mo.md(
                        _table("Parameters", _value_rows(_problem.parameters))
                    )
                }
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _():
    _names = scenario_names()
    scenario_picker = mo.ui.dropdown(
        options=_names,
        value="nominal" if "nominal" in _names else _names[0],
        label="Scenario",
    )
    run_button = mo.ui.run_button(label="Run public scenario", kind="success")
    return run_button, scenario_picker


@app.cell(hide_code=True)
def _(run_button, scenario_picker):
    mo.vstack(
        [
            mo.md("## Public scenarios"),
            mo.hstack([scenario_picker, run_button], justify="start", gap=1),
            mo.md(scenario(scenario_picker.value).description),
        ]
    )
    return


@app.function
def forget_submission_modules():
    """Remove imported modules whose files are under `submission/`.

    All other modules stay imported.
    """
    for name, module in list(sys.modules.items()):
        locations = [
            getattr(module, "__file__", None),
            *getattr(module, "__path__", ()),
        ]
        if any(
            location and Path(location).resolve().is_relative_to(SUBMISSION_DIR)
            for location in locations
        ):
            del sys.modules[name]


@app.function
def load_strategy():
    """Instantiate `MyStrategy` from the current files under `submission/`.

    Like the command-line runner, `submission/` is put first on the import path so that
    `strategy.py` can import sibling modules, which are also read again from disk.
    """
    forget_submission_modules()
    importlib.invalidate_caches()
    if str(SUBMISSION_DIR) not in sys.path:
        sys.path.insert(0, str(SUBMISSION_DIR))
    spec = importlib.util.spec_from_file_location("_submission_strategy", STRATEGY_FILE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    # Without bytecode caches, an edit made within a second of the previous run
    # cannot be masked by a cache that still matches the file's size and timestamp.
    dont_write_bytecode, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = dont_write_bytecode
    strategy_class = getattr(module, STRATEGY_CLASS, None)
    if not (isinstance(strategy_class, type) and issubclass(strategy_class, Strategy)):
        raise TypeError(
            f"{STRATEGY_FILE.name} must define {STRATEGY_CLASS} as a Strategy subclass"
        )
    return strategy_class()


@app.cell(hide_code=True)
def _(run_button, scenario_picker):
    mo.stop(
        not run_button.value,
        mo.md("Select a scenario and click **Run public scenario** to see the result."),
    )
    _output = io.StringIO()
    load_error = ""
    result = None
    with contextlib.redirect_stdout(_output), contextlib.redirect_stderr(_output):
        try:
            _strategy = load_strategy()
        except Exception:
            load_error = traceback.format_exc()
        else:
            result = run(_strategy, scenario(scenario_picker.value))
    strategy_output = _output.getvalue()
    return load_error, result, strategy_output


@app.cell(hide_code=True)
def _(load_error, result, strategy_output):
    _sections = [mo.md("## Result")]
    if load_error:
        _sections.append(
            mo.callout(
                mo.plain_text(load_error),
                kind="danger",
                title=f"Could not load submission/strategy.py:{STRATEGY_CLASS}",
            )
        )
    else:
        _metrics = evaluate(result)
        _declared = (
            f"yes, at {_metrics.completion_declared_time_s:.1f} s"
            if _metrics.completion_declared
            else "no"
        )
        _rows = [
            ("Scenario", f"`{result.scenario.name}` (seed {result.seed})"),
            ("Termination reason", f"`{_metrics.termination_reason}`"),
            (
                "End time",
                f"{_metrics.end_time_s:.1f} s "
                f"(time limit {_metrics.time_limit_s:.1f} s)",
            ),
            ("Completion declared", _declared),
            ("Safe", "yes" if _metrics.safe else "no"),
            ("Achieved delta-v", f"{_metrics.delta_v_mps:.4f} m/s"),
            ("Target delta-v", f"{_metrics.target_delta_v_mps:.4f} m/s"),
            (
                "Delta-v error (achieved - target)",
                f"{_metrics.delta_v_error_mps:+.4f} m/s",
            ),
            ("Minimum battery energy", f"{_metrics.min_battery_energy_wh:.2f} Wh"),
            (
                "Propulsion temperature range",
                f"{_metrics.min_propulsion_temperature_c:.2f} to "
                f"{_metrics.max_propulsion_temperature_c:.2f} C",
            ),
            (
                "Maximum absolute wheel momentum",
                f"{_metrics.max_abs_wheel_momentum_nms:.4f} Nms",
            ),
        ]
        _sections.append(
            mo.md(
                "\n".join(
                    ["| Metric | Value |", "|---|---|"]
                    + [f"| {label} | {value} |" for label, value in _rows]
                )
            )
        )
        _sections.append(
            mo.md(
                "Declaring completion is not success: "
                "judge the run from the metrics above."
            )
        )
        if _metrics.safety_violations:
            _sections.append(
                mo.callout(
                    mo.md(
                        "\n".join(
                            f"- `{violation.reason}` at {violation.time_s:.1f} s: "
                            f"{violation.message}"
                            for violation in _metrics.safety_violations
                        )
                    ),
                    kind="warn",
                    title="Safety violations",
                )
            )
        if _metrics.termination_reason in (
            TerminationReason.STRATEGY_ERROR,
            TerminationReason.INVALID_COMMAND,
        ):
            _sections.append(
                mo.callout(
                    mo.plain_text(result.termination.detail),
                    kind="danger",
                    title=f"The run ended with {_metrics.termination_reason}",
                )
            )
    _sections.append(
        mo.accordion(
            {
                "Strategy output (stdout and stderr)": mo.plain_text(strategy_output)
                if strategy_output
                else mo.md("The strategy printed nothing.")
            }
        )
    )
    mo.vstack(_sections)
    return


@app.function
def build_submission_zip():
    """Zip the current `submission/` directory, keeping it as the top-level folder.

    Python bytecode caches are left out.
    Symbolic links are rejected instead of followed.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for directory, dirnames, filenames in os.walk(SUBMISSION_DIR):
            directory = Path(directory)
            dirnames[:] = sorted(name for name in dirnames if name != "__pycache__")
            for name in [*dirnames, *sorted(filenames)]:
                path = directory / name
                relative = path.relative_to(SUBMISSION_DIR)
                if path.is_symlink():
                    raise ValueError(
                        f"submission/{relative.as_posix()} is a symbolic link; "
                        "replace it with a regular file or directory"
                    )
                if path.is_file() and path.suffix not in (".pyc", ".pyo"):
                    archive.write(path, f"submission/{relative.as_posix()}")
    return buffer.getvalue()


@app.cell(hide_code=True)
def _():
    mo.vstack(
        [
            mo.md(
                """
                ## Prepare submission

                The download packs the whole `submission/` directory as it is on disk
                when you click, without Python bytecode caches.
                """
            ),
            mo.download(
                data=build_submission_zip,
                filename="submission.zip",
                mimetype="application/zip",
                label="Download submission.zip",
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
