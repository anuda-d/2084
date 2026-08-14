"""Narrow current projection for the authored ration-schedule experiment."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RationScheduleVersion:
    version_id: str
    artifact_id: str
    period_id: str
    entitlement_packets: int
    previous_version_id: str | None = None


class OfficialRecord:
    """Own one ration schedule's immutable versions and current pointer."""

    def __init__(self, *, artifact_id: str) -> None:
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            raise ValueError("official record requires a non-empty artifact_id")
        self._artifact_id = artifact_id
        self._versions: tuple[RationScheduleVersion, ...] = ()
        self._current_version_id: str | None = None

    @property
    def artifact_id(self) -> str:
        return self._artifact_id

    @property
    def versions(self) -> tuple[RationScheduleVersion, ...]:
        return self._versions

    @property
    def current_version_id(self) -> str | None:
        return self._current_version_id

    @property
    def current_version(self) -> RationScheduleVersion | None:
        if self._current_version_id is None:
            return None
        return next(
            version
            for version in self._versions
            if version.version_id == self._current_version_id
        )

    def publish_initial(
        self,
        *,
        version_id: str,
        artifact_id: str,
        period_id: str,
        entitlement_packets: int,
    ) -> RationScheduleVersion:
        if self._versions:
            raise ValueError("official record already has an initial publication")
        if artifact_id != self.artifact_id:
            raise ValueError("publication artifact_id does not match the official record")
        if not isinstance(version_id, str) or not version_id.strip():
            raise ValueError("publication requires a non-empty version_id")
        if not isinstance(period_id, str) or not period_id.strip():
            raise ValueError("publication requires a non-empty period_id")
        if (
            not isinstance(entitlement_packets, int)
            or isinstance(entitlement_packets, bool)
            or entitlement_packets <= 0
        ):
            raise ValueError("publication entitlement_packets must be positive")
        version = RationScheduleVersion(
            version_id=version_id,
            artifact_id=artifact_id,
            period_id=period_id,
            entitlement_packets=entitlement_packets,
        )
        self._versions = (version,)
        self._current_version_id = version.version_id
        return version

    def to_data(self) -> dict[str, object]:
        """Return detached, JSON-compatible inspector data."""
        return {
            "artifact_id": self.artifact_id,
            "current_version_id": self.current_version_id,
            "versions": [
                {
                    "version_id": version.version_id,
                    "artifact_id": version.artifact_id,
                    "period_id": version.period_id,
                    "entitlement_packets": version.entitlement_packets,
                    "previous_version_id": version.previous_version_id,
                }
                for version in self.versions
            ],
        }
