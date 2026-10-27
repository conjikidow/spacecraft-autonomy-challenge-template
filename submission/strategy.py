"""Your strategy for the Spacecraft Autonomy Challenge."""

import pprint

from spacecraft_autonomy_challenge import (  # noqa: F401
    Commander,
    CommandError,
    CommandId,
    DeclareCompletion,
    MissionBrief,
    PropulsionMode,
    SafetyLimits,
    ScheduledCommand,
    SetHeater,
    SetPropulsionMode,
    SpacecraftParameters,
    Strategy,
    Telemetry,
    ThrusterParameters,
)


class MyStrategy(Strategy):
    def initialize(
        self, brief: MissionBrief, telemetry: Telemetry, commander: Commander
    ) -> None:
        """Called once at time 0.

        Schedule commands with `commander.schedule(time_s, command)`.
        """
        pprint.pp(brief)
        pprint.pp(telemetry)

    def update(self, telemetry: Telemetry, commander: Commander) -> None:
        """Called every `brief.decision_period_s` seconds with the latest telemetry."""
