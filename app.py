import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")

with app.setup(hide_code=True):
    import contextlib
    import dataclasses
    import importlib
    import importlib.abc
    import importlib.machinery
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

    REPOSITORY_DIR = Path(__file__).resolve().parent
    SUBMISSION_DIR = (REPOSITORY_DIR / "submission").resolve()
    STRATEGY_FILE = SUBMISSION_DIR / "strategy.py"
    STRATEGY_CLASS = "MyStrategy"

    class SubmissionLoadError(Exception):
        """Raised when the participant's strategy cannot be imported or instantiated."""


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Spacecraft Operations Challenge

    Your solution is the `submission/` directory.
    The entry point is the `MyStrategy` class in `submission/strategy.py`,
    and every other file it needs (Python modules, planning models, model weights,
    configuration, data) also belongs under `submission/`.

    1. Edit `submission/strategy.py` in the **Strategy** editor below.
       Add or edit any other file under `submission/` from the Files panel.
    2. Select a public scenario and click **Run public scenario**.
       Every run loads the current files from disk,
       so there is no need to restart this notebook.
    3. Inspect the result and iterate.
    4. Prepare and download `submission.zip` when you need the bundle.
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
        return "\n".join([f"| {title} | Value |", "|:---|:---|", *rows])

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
                widths="equal",
                align="start",
                gap=2,
            ),
            mo.accordion(
                {
                    "Nominal spacecraft parameters": mo.md(
                        _table("Parameter", _value_rows(_problem.parameters))
                    )
                }
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _():
    # Send the value only when the editor loses focus, so the file is written once
    # per edit instead of on every keystroke.
    strategy_editor = mo.ui.code_editor(
        value=STRATEGY_FILE.read_text(encoding="utf-8"),
        language="python",
        debounce=True,
    )
    return (strategy_editor,)


@app.cell(hide_code=True)
def _(strategy_editor):
    _sections = [
        mo.md(
            """
            ## Strategy

            The contents of `submission/strategy.py`.
            Changes are saved to disk when the editor loses focus.
            If you change this file outside this editor,
            reload the notebook before editing it here,
            or the editor will overwrite that change.
            """
        ),
        strategy_editor,
    ]
    try:
        if strategy_editor.value != STRATEGY_FILE.read_text(encoding="utf-8"):
            STRATEGY_FILE.write_text(strategy_editor.value, encoding="utf-8")
    except OSError as error:
        _sections.append(
            mo.callout(
                str(error), kind="danger", title="Could not save submission/strategy.py"
            )
        )
    mo.vstack(_sections)
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


@app.function(hide_code=True)
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


@app.class_definition(hide_code=True)
class SourceOnlyLoader(importlib.machinery.SourceFileLoader):
    """Loader that compiles from source and never reads or writes bytecode caches.

    A cache that still matches a file's size and timestamp, which has a resolution of
    one second, could otherwise hide an edit made right after the previous run.
    """

    def get_code(self, fullname):
        return compile(self.get_data(self.path), self.path, "exec", dont_inherit=True)


@app.class_definition(hide_code=True)
class SubmissionFinder(importlib.abc.MetaPathFinder):
    """Import hook that loads source files under `submission/` from source only."""

    def find_spec(self, fullname, path, target=None):
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if not (
            spec is not None
            and isinstance(spec.loader, importlib.machinery.SourceFileLoader)
            and Path(spec.origin).resolve().is_relative_to(SUBMISSION_DIR)
        ):
            return None
        spec.loader = SourceOnlyLoader(fullname, spec.origin)
        return spec


@app.function(hide_code=True)
def load_strategy():
    """Instantiate `MyStrategy` from the current files under `submission/`.

    Like the command-line runner, `submission/` is put first on the import path so that
    `strategy.py` can import sibling modules, which are also read again from disk.
    Raises `SubmissionLoadError`, chained to the participant's exception, if the code
    cannot be imported or instantiated.
    """
    forget_submission_modules()
    importlib.invalidate_caches()
    entry = str(SUBMISSION_DIR)
    while entry in sys.path:
        sys.path.remove(entry)
    sys.path.insert(0, entry)
    if not any(isinstance(finder, SubmissionFinder) for finder in sys.meta_path):
        # Right before the path-based finder, so built-in and frozen modules keep
        # precedence as they do under the command-line runner.
        sys.meta_path.insert(
            sys.meta_path.index(importlib.machinery.PathFinder), SubmissionFinder()
        )
    loader = SourceOnlyLoader("_submission_strategy", str(STRATEGY_FILE))
    module = importlib.util.module_from_spec(
        importlib.util.spec_from_loader(loader.name, loader)
    )
    sys.modules[loader.name] = module
    try:
        loader.exec_module(module)
    except Exception as error:
        raise SubmissionLoadError(f"cannot import {STRATEGY_FILE.name}") from error
    strategy_class = getattr(module, STRATEGY_CLASS, None)
    if not (isinstance(strategy_class, type) and issubclass(strategy_class, Strategy)):
        raise SubmissionLoadError(
            f"{STRATEGY_FILE.name} must define {STRATEGY_CLASS} as a Strategy subclass"
        )
    try:
        return strategy_class()
    except Exception as error:
        raise SubmissionLoadError(f"cannot instantiate {STRATEGY_CLASS}") from error


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
        except SubmissionLoadError as error:
            load_error = "".join(traceback.format_exception(error))
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
                (
                    f"{_metrics.end_time_s:.1f} s "
                    f"(time limit {_metrics.time_limit_s:.1f} s)"
                ),
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
                (
                    f"{_metrics.min_propulsion_temperature_c:.2f} to "
                    f"{_metrics.max_propulsion_temperature_c:.2f} C"
                ),
            ),
            (
                "Maximum absolute wheel momentum",
                f"{_metrics.max_abs_wheel_momentum_nms:.4f} Nms",
            ),
        ]
        _sections.append(
            mo.md(
                "\n".join(
                    ["| Metric | Value |", "|:---|:---|"]
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


@app.function(hide_code=True)
def build_submission_zip():
    """Zip the current `submission/` directory, keeping it as the top-level folder.

    Python bytecode caches are left out.
    Raises `ValueError` for a missing strategy file or a symbolic link, which is
    rejected instead of followed, and `OSError` for a file that cannot be read.
    """
    if (REPOSITORY_DIR / "submission").is_symlink():
        raise ValueError("submission/ is a symbolic link; replace it with a directory")
    if not STRATEGY_FILE.is_file():
        raise ValueError(f"submission/{STRATEGY_FILE.name} is missing")

    def _raise(error):
        raise error

    buffer = io.BytesIO()
    with zipfile.ZipFile(
        buffer, "w", zipfile.ZIP_DEFLATED, strict_timestamps=False
    ) as archive:
        for directory, dirnames, filenames in os.walk(SUBMISSION_DIR, onerror=_raise):
            directory = Path(directory)
            for name in sorted([*dirnames, *filenames]):
                path = directory / name
                relative = path.relative_to(SUBMISSION_DIR)
                if path.is_symlink():
                    raise ValueError(
                        f"submission/{relative.as_posix()} is a symbolic link; "
                        "replace it with a regular file or directory"
                    )
                if path.is_file() and path.suffix not in (".pyc", ".pyo"):
                    archive.write(path, f"submission/{relative.as_posix()}")
            dirnames[:] = sorted(name for name in dirnames if name != "__pycache__")
    return buffer.getvalue()


@app.cell(hide_code=True)
def _():
    prepare_button = mo.ui.run_button(label="Prepare submission.zip")
    return (prepare_button,)


@app.cell(hide_code=True)
def _(prepare_button):
    _sections = [
        mo.md(
            """
            ## Prepare submission

            Pack the whole `submission/` directory as it is on disk now,
            without Python bytecode caches.
            Prepare it again after you change any file.
            """
        ),
        prepare_button,
    ]
    if prepare_button.value:
        try:
            _data = build_submission_zip()
        except (ValueError, OSError) as error:
            _sections.append(
                mo.callout(
                    str(error), kind="danger", title="Could not prepare submission.zip"
                )
            )
        else:
            with zipfile.ZipFile(io.BytesIO(_data)) as _archive:
                _names = _archive.namelist()
            _sections.append(
                mo.download(
                    data=_data,
                    filename="submission.zip",
                    mimetype="application/zip",
                    label="Download submission.zip",
                )
            )
            _sections.append(
                mo.accordion(
                    {
                        f"Contents ({len(_names)} files)": mo.plain_text(
                            "\n".join(_names)
                        )
                    }
                )
            )
    mo.vstack(_sections)
    return


if __name__ == "__main__":
    app.run()
