"""PawPal+ backend: tasks, pets, owner, and the scheduler that plans the day."""

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
    frequency: str = "daily"  # "once" | "daily" | "weekly"
    time: str | None = None  # fixed start as "HH:MM"; None = scheduler picks a slot
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove every task with this title from the pet."""
        self.tasks = [t for t in self.tasks if t.title != title]


@dataclass
class Owner:
    name: str
    available_minutes: int = 120
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Every pet's tasks together, each paired with the pet it belongs to."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class ScheduledItem:
    task: Task
    pet: Pet
    start_minute: int  # minutes since midnight
    reason: str = ""

    def end_minute(self) -> int:
        """Return the minute this item finishes."""
        return self.start_minute + self.task.duration_minutes


def format_time(minute: int) -> str:
    """Turn minutes since midnight into 'HH:MM'."""
    return f"{minute // 60:02d}:{minute % 60:02d}"


def parse_time(text: str) -> int:
    """Turn 'HH:MM' into minutes since midnight."""
    hours, minutes = text.split(":")
    return int(hours) * 60 + int(minutes)


DAY_END_MINUTE = 24 * 60


class Scheduler:
    def __init__(self, owner: Owner, day_start_minute: int = 8 * 60):
        """Set up a scheduler for one owner, starting the day at 08:00 by default."""
        self.owner = owner
        self.day_start_minute = day_start_minute
        self.skipped: list[tuple[Pet, Task, str]] = []

    def build_daily_plan(self) -> list[ScheduledItem]:
        """Plan pending tasks across all pets.

        Tasks with a fixed time are placed first, at that time. The rest go
        highest priority first (shorter first on ties) into the earliest free gap.
        Anything that overlaps or doesn't fit in the owner's time is skipped.
        """
        pending = [(p, t) for p, t in self.owner.get_all_tasks() if not t.completed]
        fixed = sorted((pt for pt in pending if pt[1].time), key=lambda pt: parse_time(pt[1].time))
        flexible = sorted(
            (pt for pt in pending if not pt[1].time),
            key=lambda pt: (-pt[1].priority, pt[1].duration_minutes),
        )

        plan: list[ScheduledItem] = []
        self.skipped = []
        remaining = self.owner.available_minutes

        for pet, task in fixed:
            start = parse_time(task.time)
            if task.duration_minutes > remaining:
                self.skipped.append((pet, task, "not enough time left"))
            elif self._overlaps(plan, start, start + task.duration_minutes):
                self.skipped.append((pet, task, "conflicts with another task"))
            else:
                reason = f"fixed at {task.time}; {task.priority.name.lower()} priority"
                plan.append(ScheduledItem(task, pet, start, reason))
                remaining -= task.duration_minutes

        for pet, task in flexible:
            start = self._first_free_slot(plan, task.duration_minutes)
            if task.duration_minutes > remaining or start is None:
                self.skipped.append((pet, task, "not enough time left"))
                continue
            reason = (
                f"{task.priority.name.lower()} priority; "
                f"{task.duration_minutes} min fits in the {remaining} min left"
            )
            plan.append(ScheduledItem(task, pet, start, reason))
            remaining -= task.duration_minutes

        plan.sort(key=lambda item: item.start_minute)
        return plan

    @staticmethod
    def _overlaps(plan: list[ScheduledItem], start: int, end: int) -> bool:
        """Return True if a time range overlaps anything already in the plan."""
        return any(start < i.end_minute() and i.start_minute < end for i in plan)

    def _first_free_slot(self, plan: list[ScheduledItem], duration: int) -> int | None:
        """Find the earliest start time where a task of this length fits, or None."""
        start = self.day_start_minute
        for item in sorted(plan, key=lambda i: i.start_minute):
            if start + duration <= item.start_minute:
                break
            start = max(start, item.end_minute())
        return start if start + duration <= DAY_END_MINUTE else None

    def explain_plan(self, plan: list[ScheduledItem]) -> str:
        """Return the plan as readable text, including skipped tasks."""
        lines = [f"Today's Schedule for {self.owner.name} ({self.owner.available_minutes} min available):"]
        for item in plan:
            lines.append(
                f"  {format_time(item.start_minute)} - {item.task.title} for {item.pet.name} "
                f"({item.task.duration_minutes} min) [{item.reason}]"
            )
        if not plan:
            lines.append("  Nothing scheduled.")
        for pet, task, why in self.skipped:
            lines.append(f"  Skipped: {task.title} for {pet.name} ({task.duration_minutes} min) - {why}")
        return "\n".join(lines)
