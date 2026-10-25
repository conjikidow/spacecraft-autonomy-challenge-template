"""Your strategy for the Spacecraft Operations Challenge."""

from spacecraft_ops_challenge import (  # noqa: F401
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
        print(brief)
        print(telemetry)

    def update(self, telemetry: Telemetry, commander: Commander) -> None:
        """Called every `brief.decision_period_s` seconds with the latest telemetry."""
