import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full", layout_file="layouts/app.grid.json")

with app.setup(hide_code=True):
    import contextlib
    import dataclasses
    import enum
    import importlib
    import importlib.abc
    import importlib.machinery
    import importlib.resources
    import importlib.util
    import inspect
    import io
    import os
    import sys
    import traceback
    import typing
    import zipfile
    from pathlib import Path

    import marimo as mo
    from spacecraft_ops_challenge import Commander, Strategy, Telemetry, __version__
    from spacecraft_ops_challenge.challenge import problem, scenario, scenario_names
    from spacecraft_ops_challenge.commands import Command
    from spacecraft_ops_challenge.evaluation import evaluate
    from spacecraft_ops_challenge.judge.dependencies import DependencyError
    from spacecraft_ops_challenge.judge.judging import check_submission
    from spacecraft_ops_challenge.judge.reporting import (
        EvaluationResult,
        ResultFormatError,
    )
    from spacecraft_ops_challenge.judge.submission import (
        SubmissionError,
        build_submission,
    )
    from spacecraft_ops_challenge.judge.views import dependencies_view, results_view
    from spacecraft_ops_challenge.results import TerminationReason
    from spacecraft_ops_challenge.simulation import run

    from submit import (
        FINAL_COLUMNS,
        PRACTICE_COLUMNS,
        TOKEN_VARIABLE,
        URL_VARIABLE,
        EvaluationServer,
        ServerError,
        board_rows,
        boards,
        final_status,
        git_config,
        receipt_lines,
        score_text,
    )

    REPOSITORY_DIR = Path(__file__).resolve().parent
    SUBMISSION_DIR = (REPOSITORY_DIR / "submission").resolve()
    STRATEGY_FILE = SUBMISSION_DIR / "strategy.py"
    STRATEGY_CLASS = "MyStrategy"
    CORE_DOCS_URL = (
        "https://github.com/conjikidow/spacecraft-operations-challenge-core"
        f"/blob/v{__version__}/docs"
    )

    FIELD_UNITS = {
        "_nms_per_s": "Nms/s",
        "_j_per_k": "J/K",
        "_w_per_k": "W/K",
        "_mps2": "m/s²",
        "_mps": "m/s",
        "_nms": "Nms",
        "_wh": "Wh",
        "_w": "W",
        "_c": "°C",
        "_s": "s",
    }

    def field_unit(name):
        """Return the unit encoded in a field name's suffix, or `-` if there is none."""
        for suffix, unit in FIELD_UNITS.items():
            if name.endswith(suffix):
                return unit
        return "-"

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
       Add or edit any other file under `submission/` from the Files panel
       or your own editor, and add packages with `uv add`.
    2. Select a public scenario and click **Run**.
       Every run loads the current files from disk,
       so there is no need to restart this notebook.
    3. Inspect the result and iterate.
    4. Click **Check** to evaluate `submission.zip` on all public scenarios,
       the way an evaluation server runs it.
    5. If your event provides an evaluation server, submit for a practice evaluation
       on hidden cases under **Evaluation server**, and submit your final version
       there as well.
    """)


@app.cell(hide_code=True)
def _():
    def _doc(obj):
        return " ".join(inspect.getdoc(obj).split())

    def _type(annotation):
        return f"`{annotation.__name__}`"

    def _arguments(command):
        fields = dataclasses.fields(command)
        return ", ".join(
            f"`{field.name}`:&nbsp;{_type(field.type)}" for field in fields
        )

    def _table(headers, rows):
        return "\n".join(
            [f"| {' | '.join(headers)} |", "|:---" * len(headers) + "|", *rows]
        )

    _telemetry_rows = [
        f"| `{field.name}` | {_type(field.type)} | {field_unit(field.name)} |"
        for field in dataclasses.fields(Telemetry)
    ]
    _command_rows = [
        f"| `{command.__name__}` | {_arguments(command) or '-'} | {_doc(command)} |"
        for command in typing.get_args(Command)
    ]
    _types = [field.type for field in dataclasses.fields(Telemetry)] + [
        field.type
        for command in typing.get_args(Command)
        for field in dataclasses.fields(command)
    ]
    _enum_lines = [
        f"`{annotation.__name__}` is one of "
        + ", ".join(f"`{member.name}`" for member in annotation)
        + "."
        for annotation in dict.fromkeys(_types)
        if issubclass(annotation, enum.Enum)
    ]
    _figure = mo.image(
        importlib.resources.files("spacecraft_ops_challenge")
        / "figures"
        / "spacecraft-geometry.svg",
        alt="Two thrusters offset from the center of mass "
        "and a single-axis reaction wheel",
        width=480,
        style={"min-width": "0"},
    )
    mo.vstack(
        [
            mo.md("## Spacecraft"),
            mo.vstack(
                [
                    mo.hstack(
                        [
                            mo.md(
                                _table(
                                    ("Telemetry field", "Type", "Unit"), _telemetry_rows
                                )
                            ).style(min_width="max-content"),
                            _figure,
                        ],
                        justify="start",
                        align="center",
                        gap=2,
                    ),
                    mo.md(_table(("Command", "Arguments", "Effect"), _command_rows)),
                ],
                gap=1.5,
            ),
            mo.md("\n\n".join(_enum_lines)),
            mo.md(
                f"Details: [Spacecraft Model]({CORE_DOCS_URL}/spacecraft-model.md), "
                f"[Commands and Timeline]({CORE_DOCS_URL}/timeline.md)"
            ),
        ]
    )


@app.cell(hide_code=True)
def _():
    def _value_rows(obj, prefix=""):
        rows = []
        for field in dataclasses.fields(obj):
            value = getattr(obj, field.name)
            if dataclasses.is_dataclass(value):
                rows.extend(_value_rows(value, f"{prefix}{field.name}."))
            else:
                rows.append(
                    f"| `{prefix}{field.name}` | {value} | {field_unit(field.name)} |"
                )
        return rows

    def _table(title, rows):
        return "\n".join([f"| {title} | Value | Unit |", "|:---|:---|:---|", *rows])

    _problem = problem()
    _goal_rows = [
        f"| `{name}` | {getattr(_problem, name)} | {field_unit(name)} |"
        for name in ("target_delta_v_mps", "time_limit_s", "decision_period_s")
    ]
    mo.vstack(
        [
            mo.md("## Mission"),
            mo.md("The public problem shared by all scenarios."),
            mo.md(
                _table(
                    "Field",
                    [
                        "| **Initial state** | | |",
                        *_value_rows(_problem.initial_state),
                        "| **Goal and timing** | | |",
                        *_goal_rows,
                        "| **Safety limits** | | |",
                        *_value_rows(_problem.limits),
                    ],
                )
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


@app.cell(hide_code=True)
def _():
    def _doc(obj):
        return " ".join(inspect.getdoc(obj).split())

    def _call(function):
        parameters = list(inspect.signature(function).parameters)[1:]
        return f"{function.__name__}({', '.join(parameters)})"

    def _table(headers, rows):
        return "\n".join(
            [f"| {' | '.join(headers)} |", "|:---" * len(headers) + "|", *rows]
        )

    _contents = {
        "brief": "Values under **Mission**, e.g. `brief.decision_period_s`",
        "telemetry": (
            "Fields under **Spacecraft** at the callback time, "
            "e.g. `telemetry.battery_energy_wh`; may differ from the true state"
        ),
        "commander": (
            "Members below, e.g. `commander.schedule(600.0, SetHeater(on=True))`"
        ),
    }
    _callback_rows = [
        f"| `{_call(callback)}` | {_doc(callback)} |"
        for callback in (Strategy.initialize, Strategy.update)
    ]
    _argument_rows = [
        f"| `{name}` | `{parameter.annotation.__name__}` | {_contents.get(name, '')} |"
        for name, parameter in inspect.signature(Strategy.initialize).parameters.items()
        if name != "self"
    ]
    _commander_rows = [
        f"| `{name if isinstance(member, property) else _call(member)}` "
        f"| {_doc(member)} |"
        for name, member in vars(Commander).items()
        if not name.startswith("_")
    ]
    mo.vstack(
        [
            mo.md("## Strategy API"),
            mo.vstack(
                [
                    mo.md(_table(("Callback", "When"), _callback_rows)),
                    mo.md(_table(("Argument", "Type", "Content"), _argument_rows)),
                    mo.md(_table(("Commander member", "Behavior"), _commander_rows)),
                ],
                gap=1.5,
            ),
            mo.md(f"Details: [Writing a Strategy]({CORE_DOCS_URL}/strategy.md)"),
        ]
    )


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
        mo.md("## Strategy"),
        mo.md(
            """
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


@app.cell(hide_code=True)
def _():
    _names = scenario_names()
    scenario_picker = mo.ui.dropdown(
        options=_names,
        value="nominal" if "nominal" in _names else _names[0],
        label="Scenario",
    )
    run_button = mo.ui.run_button(label="Run", kind="success")
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
    load_error = ""
    result = None
    strategy_output = ""
    if run_button.value:
        _output = io.StringIO()
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
    mo.stop(
        result is None and not load_error,
        mo.vstack(
            [
                *_sections,
                mo.md("Select a scenario and click **Run** to see the result."),
            ]
        ),
    )
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
                    f"{_metrics.max_propulsion_temperature_c:.2f} °C"
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


@app.cell(hide_code=True)
def _():
    prepare_button = mo.ui.run_button(label="Prepare submission.zip")
    return (prepare_button,)


@app.cell(hide_code=True)
def _(prepare_button):
    _sections = [
        mo.md("## Prepare submission"),
        mo.md(
            """
            Pack the `submission/` directory and `pyproject.toml` as they are now,
            as `uv run spacecraft-ops-challenge pack` does.
            Prepare it again after you change any file.
            """
        ),
        prepare_button,
    ]
    if prepare_button.value:
        try:
            _data = build_submission(REPOSITORY_DIR)
        except (SubmissionError, OSError) as error:
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


@app.cell(hide_code=True)
def _():
    check_button = mo.ui.run_button(label="Check", kind="success")
    return (check_button,)


@app.cell(hide_code=True)
def _(check_button):
    _sections = [
        mo.md("## Check"),
        mo.md(
            """
            Evaluate `submission.zip`, packed from the files as they are now,
            on all public scenarios, as `uv run spacecraft-ops-challenge check` does:
            each scenario runs your strategy in a new Python process,
            and the packages of `pyproject.toml` that are missing are installed
            for this check only.
            """
        ),
        check_button,
    ]
    if check_button.value:
        try:
            with mo.status.spinner(
                title="Checking on the public scenarios"
            ) as _spinner:
                _evaluation = check_submission(
                    build_submission(REPOSITORY_DIR),
                    on_status=lambda message: _spinner.update(subtitle=message),
                    on_case_done=lambda outcome: _spinner.update(
                        subtitle=f"{outcome.case_id}: {outcome.status.value}"
                    ),
                )
        except (SubmissionError, DependencyError, OSError) as error:
            _sections.append(
                mo.callout(str(error), kind="danger", title="Could not check")
            )
        else:
            _result = EvaluationResult.from_evaluation(_evaluation)
            _sections += [
                results_view(_result),
                mo.accordion({"Packages": dependencies_view(_result.dependencies)}),
            ]
    mo.vstack(_sections)


@app.cell(hide_code=True)
def _():
    server_form = mo.ui.dictionary(
        {
            "url": mo.ui.text(
                value=os.environ.get(URL_VARIABLE, ""),
                label="Server URL",
                full_width=True,
            ),
            "token": mo.ui.text(
                value=os.environ.get(TOKEN_VARIABLE, ""),
                kind="password",
                label="Token (if any)",
                full_width=True,
            ),
            "participant_id": mo.ui.text(
                value=git_config("user.email") or "",
                label="Your id (git config user.email)",
                full_width=True,
            ),
            "participant_name": mo.ui.text(
                value=git_config("user.name") or "",
                label="Your name (git config user.name)",
                full_width=True,
            ),
        }
    )
    practice_button = mo.ui.run_button(label="Submit for practice", kind="success")
    final_button = mo.ui.run_button(label="Submit as final", kind="warn")
    return final_button, practice_button, server_form


@app.cell(hide_code=True)
def _(final_button, practice_button, server_form):
    _sections = [
        mo.md("## Evaluation server"),
        mo.md(
            f"""
            If your event provides an evaluation server, submit `submission.zip`,
            packed from the files as they are now, to it.
            A **practice** submission runs on hidden cases and shows the result here.
            A **final** submission is stored and answered with a receipt.
            The server URL and token can also come from the environment variables
            `{URL_VARIABLE}` and `{TOKEN_VARIABLE}`.
            """
        ),
        server_form,
        mo.hstack([practice_button, final_button], justify="start", gap=1),
    ]
    if practice_button.value or final_button.value:
        _final = bool(final_button.value)
        _form = server_form.value
        try:
            if not (
                _form["participant_id"].strip() and _form["participant_name"].strip()
            ):
                raise ServerError("enter your id and your name")
            _server = EvaluationServer(_form["url"], _form["token"])
            _receipt = _server.submit(
                build_submission(REPOSITORY_DIR),
                _form["participant_id"].strip(),
                _form["participant_name"].strip(),
                final=_final,
            )
            _document = _receipt
            if not _final:
                with mo.status.spinner(
                    title="Waiting for the practice evaluation"
                ) as _spinner:
                    _document = _server.wait(
                        _receipt["id"],
                        on_status=lambda status: _spinner.update(subtitle=status),
                    )
        except (ServerError, SubmissionError, OSError) as error:
            _sections.append(
                mo.callout(str(error), kind="danger", title="Could not submit")
            )
        else:
            _sections.append(
                mo.callout(
                    mo.plain_text("\n".join(receipt_lines(_document))),
                    kind="success" if _document.get("status") != "failed" else "danger",
                    title="Final submission received" if _final else "Submission",
                )
            )
            if _document.get("status") == "failed":
                _sections.append(mo.md(f"**Not evaluated:** {_document.get('error')}"))
            elif _document.get("result") is not None:
                try:
                    _sections.append(
                        results_view(EvaluationResult.from_dict(_document["result"]))
                    )
                except ResultFormatError as error:
                    _sections.append(
                        mo.callout(
                            str(error), kind="danger", title="Invalid result document"
                        )
                    )
    mo.vstack(_sections)
    return


@app.cell(hide_code=True)
def _():
    board_button = mo.ui.run_button(label="Show leaderboard")
    mine_checkbox = mo.ui.checkbox(label="Only my practice submissions")
    return board_button, mine_checkbox


@app.cell(hide_code=True)
def _(board_button, mine_checkbox, server_form):
    _sections = [
        mo.md("## Leaderboard"),
        mo.md(
            """
            If the evaluation server has a leaderboard, show it, and whether final
            submissions are open. It uses the server URL and token above.
            Click again to update it, also after changing the options.
            """
        ),
        mo.hstack([board_button, mine_checkbox], justify="start", gap=1),
    ]
    if board_button.value:
        _form = server_form.value
        try:
            _server = EvaluationServer(_form["url"], _form["token"])
            _mine = _form["participant_id"].strip() if mine_checkbox.value else None
            if mine_checkbox.value and not _mine:
                raise ServerError("enter your id above to see only your submissions")
            _practice, _final = boards(_server, _mine)
        except ServerError as error:
            _sections.append(
                mo.callout(str(error), kind="danger", title="Could not load the board")
            )
        else:
            _score = {"Score": score_text}
            if _final is not None:
                _status = final_status(_final)
                if _status is not None:
                    _sections.append(mo.callout(_status, kind="info"))
                if _final.get("published"):
                    _final_rows = board_rows(_final, *FINAL_COLUMNS, formatted=False)
                    _sections += [
                        mo.md("### Final ranking"),
                        mo.ui.table(_final_rows, selection=None, format_mapping=_score)
                        if _final_rows
                        else mo.md("No final ranking."),
                    ]
            if _practice is not None:
                _rows = board_rows(_practice, *PRACTICE_COLUMNS, formatted=False)
                _total = _practice.get("total", len(_rows))
                _empty = (
                    "None of your practice submissions has been evaluated."
                    if mine_checkbox.value
                    else "No evaluated practice submissions."
                )
                _sections += [
                    mo.md(f"### Practice leaderboard ({len(_rows)} of {_total})"),
                    mo.ui.table(_rows, selection=None, format_mapping=_score)
                    if _rows
                    else mo.md(_empty),
                ]
            if len(_sections) == 3:
                _sections.append(
                    mo.md(f"No leaderboard at {_server.url}; check the server address.")
                )
    mo.vstack(_sections)
    return


if __name__ == "__main__":
    app.run()
