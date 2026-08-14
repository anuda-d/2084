"""Configured first-day living simulation and terminal command."""

from __future__ import annotations

import argparse

from simulation.agents import AgentState
from simulation.institutions import InstitutionState
from simulation.engine import Simulation, SimulationRules
from simulation.world import PhysicalDiary, ResourceState, WorldState
from policies.focal_policy import FocalPolicy
from policies.institution_policy import InstitutionPolicy
from policies.supporting_policy import AllocationClerkPolicy, CoworkerPolicy


FOCAL_AGENT_ID = "mara-vale"
CO_WORKER_ID = "ilan-reed"
CLERK_ID = "sena-orr"


def build_first_day(seed: int = 42) -> Simulation:
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
            records={"public_claim_schedule_authorized": True},
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
            FOCAL_AGENT_ID: FocalPolicy(),
            CO_WORKER_ID: CoworkerPolicy(),
            CLERK_ID: AllocationClerkPolicy(),
        },
        institution_policy=InstitutionPolicy({8: 5, 16: 1}),
        rules=SimulationRules(
            work_location="workplace",
            allocation_location="allocation_office",
            resource_id="household_allocation",
            resource_proposition="daily_allocation_units",
        ),
        focal_agent_id=FOCAL_AGENT_ID,
        max_ticks=30,
        completion_tick=24,
        scenario_configuration={
            "scenario_id": "first_day_v1",
            "completion_tick": 24,
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
            "official_claim_schedule": {8: 5, 16: 1},
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the 2084 first living slice")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ticks", type=_positive_ticks, default=30)
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="show explicitly omniscient development records",
    )
    args = parser.parse_args(argv)

    simulation = build_first_day(seed=args.seed)
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
