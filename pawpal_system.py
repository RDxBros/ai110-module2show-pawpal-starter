"""PawPal+ backend class stubs. Logic is intentionally not implemented yet."""

from dataclasses import dataclass, field
from enum import IntEnum


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    category: str = "general"  # walk, feeding, meds, enrichment, grooming...
    completed: bool = False

    def mark_complete(self) -> None:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, title: str) -> None:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int = 120
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> list[Task]:
        pass


@dataclass
class ScheduledItem:
    task: Task
    pet: Pet
    start_minute: int  # minutes since midnight
    reason: str = ""

    def end_minute(self) -> int:
        pass


class Scheduler:
    def __init__(self, owner: Owner, day_start_minute: int = 8 * 60):
        self.owner = owner
        self.day_start_minute = day_start_minute

    def build_daily_plan(self) -> list[ScheduledItem]:
        pass

    def explain_plan(self, plan: list[ScheduledItem]) -> str:
        pass
