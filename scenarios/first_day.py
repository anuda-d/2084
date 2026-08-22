"""Configured first-day living simulation and terminal command."""

from __future__ import annotations

import argparse
from collections.abc import Callable

from policies.model_focal_policy import ModelFocalPolicy
from policies.ollama_client import OllamaDecisionClient
from simulation.agents import AgentState, DecisionPolicy
from simulation.institutions import (
    InstitutionState,
    OfficialRecordPublication,
    OfficialRecordRewrite,
)
from simulation.engine import Simulation, SimulationRules
from simulation.official_record import OfficialRecord
from simulation.world import PhysicalDiary, ResourceState, WorldState
from policies.focal_policy import FocalPolicy
from policies.institution_policy import InstitutionPolicy
from policies.supporting_policy import AllocationClerkPolicy, CoworkerPolicy


FOCAL_AGENT_ID = "mara-vale"
CO_WORKER_ID = "ilan-reed"
CLERK_ID = "sena-orr"
RATION_SCHEDULE_ARTIFACT_ID = "weekly-household-ration-schedule"
RATION_SCHEDULE_VERSION_ONE_ID = "weekly-household-ration-schedule-v1"
RATION_SCHEDULE_VERSION_TWO_ID = "weekly-household-ration-schedule-v2"
RATION_SCHEDULE_PERIOD_ID = "first-day-week"
_MF10_OLLAMA_MODEL = "qwen3:4b-instruct"


def build_first_day(
    seed: int = 42, *, focal_policy: DecisionPolicy | None = None
) -> Simulation:
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    agents = {
        FOCAL_AGENT_ID: AgentState(
            agent_id=FOCAL_AGENT_ID,
            display_name="Mara Vale",
            role="focal",
            location="home",
            aim="complete work and secure the household allocation",
            required_resource_id="household_allocation",
            required_units=3,
            obligations=("workplace shift", "household allocation"),
        ),
        CO_WORKER_ID: AgentState(
            agent_id=CO_WORKER_ID,
            display_name="Ilan Reed",
            role="co-worker",
            location="workplace",
            aim="complete the morning ledger shift",
        ),
        CLERK_ID: AgentState(
            agent_id=CLERK_ID,
            display_name="Sena Orr",
            role="allocation clerk",
            location="allocation_office",
            aim="staff the allocation counter",
        ),
    }
    world = WorldState(
        tick=0,
        seed=seed,
        travel_graph={
            "home": ("workplace",),
            "workplace": ("home", "allocation_office"),
            "allocation_office": ("workplace",),
        },
        agents=agents,
        resource=ResourceState(total_units=3, committed_units=1),
        institution=InstitutionState(
            institution_id="civic-allocation-office",
            display_name="Civic Allocation Office",
            official_record=OfficialRecord(artifact_id=RATION_SCHEDULE_ARTIFACT_ID),
            official_record_rewrite_authorized_actor_ids=(
                "civic-allocation-office",
            ),
        ),
        diaries={
            "mara-private-diary": PhysicalDiary(
                object_id="mara-private-diary",
                location="home",
            )
        },
    )
    return Simulation(
        world=world,
        policies={
            FOCAL_AGENT_ID: FocalPolicy() if focal_policy is None else focal_policy,
            CO_WORKER_ID: CoworkerPolicy(),
            CLERK_ID: AllocationClerkPolicy(),
        },
        institution_policy=InstitutionPolicy(
            {},
            initial_publication_schedule={
                1: OfficialRecordPublication(
                    artifact_id=RATION_SCHEDULE_ARTIFACT_ID,
                    version_id=RATION_SCHEDULE_VERSION_ONE_ID,
                    period_id=RATION_SCHEDULE_PERIOD_ID,
                    entitlement_packets=3,
                )
            },
            official_record_rewrite_schedule={
                10: OfficialRecordRewrite(
                    actor_id="civic-allocation-office",
                    reason="align the published schedule with the two-packet issue",
                    artifact_id=RATION_SCHEDULE_ARTIFACT_ID,
                    expected_current_version_id=RATION_SCHEDULE_VERSION_ONE_ID,
                    version_id=RATION_SCHEDULE_VERSION_TWO_ID,
                    period_id=RATION_SCHEDULE_PERIOD_ID,
                    entitlement_packets=2,
                )
            },
        ),
        rules=SimulationRules(
            work_location="workplace",
            allocation_location="allocation_office",
            resource_id="household_allocation",
            resource_proposition="daily_allocation_units",
            official_record_access_location="allocation_office",
            official_record_artifact_id=RATION_SCHEDULE_ARTIFACT_ID,
            public_conformity_threshold=0.7,
        ),
        focal_agent_id=FOCAL_AGENT_ID,
        max_ticks=30,
        completion_tick=28,
        scenario_configuration={
            "scenario_id": "first_day_v3",
            "completion_tick": 28,
            "agent_ids": [FOCAL_AGENT_ID, CO_WORKER_ID, CLERK_ID],
            "starting_locations": {
                FOCAL_AGENT_ID: "home",
                CO_WORKER_ID: "workplace",
                CLERK_ID: "allocation_office",
            },
            "travel_graph": {
                "home": ["workplace"],
                "workplace": ["home", "allocation_office"],
                "allocation_office": ["workplace"],
            },
            "initial_resource": {"total_units": 3, "committed_units": 1},
            "initial_official_record_publication": {
                "tick": 1,
                "artifact_id": RATION_SCHEDULE_ARTIFACT_ID,
                "version_id": RATION_SCHEDULE_VERSION_ONE_ID,
                "period_id": RATION_SCHEDULE_PERIOD_ID,
                "entitlement_packets": 3,
            },
            "official_record_access_location": "allocation_office",
            "official_record_rewrite": {
                "tick": 10,
                "actor_id": "civic-allocation-office",
                "reason": "align the published schedule with the two-packet issue",
                "authorized_actor_ids": ["civic-allocation-office"],
                "artifact_id": RATION_SCHEDULE_ARTIFACT_ID,
                "expected_current_version_id": RATION_SCHEDULE_VERSION_ONE_ID,
                "version_id": RATION_SCHEDULE_VERSION_TWO_ID,
                "period_id": RATION_SCHEDULE_PERIOD_ID,
                "entitlement_packets": 2,
            },
            "public_pressure": 0.8,
            "public_conformity_threshold": 0.7,
            "action_durations": {
                "travel": 2,
                "work": 2,
                "write_diary": 2,
                "read_diary": 1,
            },
            "resource_id": "household_allocation",
            "resource_proposition": "daily_allocation_units",
            "diary_id": "mara-private-diary",
            "diary_starting_location": "home",
        },
    )


def _positive_ticks(value: str) -> int:
    ticks = int(value)
    if ticks <= 0:
        raise argparse.ArgumentTypeError("ticks must be positive")
    return ticks


def _cli_focal_policy(
    *,
    policy_name: str,
    ollama_base_url: str | None,
    ollama_model: str | None,
    ollama_client_factory: Callable[..., OllamaDecisionClient],
) -> DecisionPolicy | None:
    if policy_name == "scripted":
        return None
    if policy_name != "ollama":
        raise ValueError("unsupported focal policy")
    if ollama_base_url is None or not ollama_base_url.strip():
        raise ValueError("Ollama base URL is required")
    if ollama_model is None or not ollama_model.strip():
        raise ValueError("Ollama model is required")
    if ollama_model.strip() != _MF10_OLLAMA_MODEL:
        raise ValueError(
            f"Ollama model must be {_MF10_OLLAMA_MODEL} for this integration"
        )
    client = ollama_client_factory(
        base_url=ollama_base_url,
        model=ollama_model.strip(),
    )
    return ModelFocalPolicy(
        client,
        configuration_id=client.configuration_id,
        authorship_identity=client.authorship_identity,
    )


def main(
    argv: list[str] | None = None,
    *,
    ollama_client_factory: Callable[..., OllamaDecisionClient] = OllamaDecisionClient,
) -> int:
    parser = argparse.ArgumentParser(description="Run the 2084 first living slice")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ticks", type=_positive_ticks, default=30)
    parser.add_argument(
        "--focal-policy",
        choices=("scripted", "ollama"),
        default="scripted",
        help="choose the scripted default or the explicit live Ollama policy",
    )
    parser.add_argument(
        "--ollama-base-url",
        help="private Ollama origin, required only with --focal-policy ollama",
    )
    parser.add_argument(
        "--ollama-model",
        help="Ollama model name, required only with --focal-policy ollama",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="show explicitly omniscient development records",
    )
    args = parser.parse_args(argv)

    if args.focal_policy == "ollama" and (
        args.ollama_base_url is None
        or not args.ollama_base_url.strip()
        or args.ollama_model is None
        or not args.ollama_model.strip()
    ):
        parser.error(
            "--ollama-base-url and --ollama-model are required with "
            "--focal-policy ollama"
        )
    if args.focal_policy == "scripted" and (
        args.ollama_base_url is not None or args.ollama_model is not None
    ):
        parser.error("--ollama-base-url and --ollama-model require --focal-policy ollama")

    try:
        focal_policy = _cli_focal_policy(
            policy_name=args.focal_policy,
            ollama_base_url=args.ollama_base_url,
            ollama_model=args.ollama_model,
            ollama_client_factory=ollama_client_factory,
        )
    except ValueError as error:
        parser.error(str(error))
    simulation = build_first_day(seed=args.seed, focal_policy=focal_policy)
    simulation.run(max_ticks=args.ticks)
    if args.inspect:
        from observer.inspector import render_inspector

        output = render_inspector(simulation)
    else:
        from observer.terminal import render_terminal

        output = render_terminal(simulation.snapshots)
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
