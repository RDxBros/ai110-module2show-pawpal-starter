"""PawPal+ backend: tasks, pets, owner, and the scheduler that plans the day."""

from dataclasses import dataclass, field, replace
from datetime import date, timedelta
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
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> "Task | None":
        """Mark this task as done. Returns the next occurrence for daily/weekly tasks, else None.

        The caller is responsible for adding the returned task to the pet (see Pet.complete_task).
        Completing an already-completed task returns None so it never spawns duplicates.
        """
        if self.completed:
            return None
        self.completed = True
        return self.next_occurrence()

    @property
    def start_minute(self) -> int:
        """Fixed start as minutes since midnight.

        Raises if the task has no fixed time, so check task.time first.
        """
        return parse_time(self.time)

    @property
    def end_minute(self) -> int:
        """Fixed end (start + duration) as minutes since midnight.

        Raises if the task has no fixed time, so check task.time first.
        """
        return self.start_minute + self.duration_minutes

    def next_occurrence(self) -> "Task | None":
        """Build the next copy of a recurring task.

        Daily tasks come back due today + 1 day and weekly tasks today + 7 days
        (using timedelta). The copy is not completed. "once" tasks return None.
        """
        step = {"daily": 1, "weekly": 7}.get(self.frequency)
        if step is None:
            return None
        return replace(self, completed=False, due_date=date.today() + timedelta(days=step))


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

    def complete_task(self, task: Task) -> Task | None:
        """Mark a task done and add its next occurrence to this pet if it recurs.

        Returns the new task, or None for "once" tasks and tasks that were
        already complete (so double-clicking never creates duplicates).
        """
        following = task.mark_complete()
        if following:
            self.tasks.append(following)
        return following


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

    def filter_tasks(
        self, pet_name: str | None = None, completed: bool | None = None
    ) -> list[tuple[Pet, Task]]:
        """Narrow every (pet, task) pair by pet name and/or completion status.

        pet_name ignores case. completed=True keeps done tasks, False keeps
        pending ones, and None (the default) doesn't filter on status at all.
        Leave both out to get everything.
        """
        return [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if (pet_name is None or pet.name.lower() == pet_name.lower())
            and (completed is None or task.completed == completed)
        ]


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


def sort_by_time(pairs: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
    """Order (pet, task) pairs by fixed start time; flexible tasks go last.

    The sort key is a tuple: (has no time, minutes since midnight). False sorts
    before True, so timed tasks come first. Ties and flexible tasks keep their
    original order. Times go through parse_time, so "9:00" sorts before
    "10:00" (plain string comparison would get that wrong).
    """
    return sorted(pairs, key=lambda pt: (pt[1].time is None, parse_time(pt[1].time) if pt[1].time else 0))


DAY_END_MINUTE = 24 * 60


class Scheduler:
    def __init__(self, owner: Owner, day_start_minute: int = 8 * 60, day: date | None = None):
        """Set up a scheduler for one owner, starting the day at 08:00 by default."""
        self.owner = owner
        self.day_start_minute = day_start_minute
        self.day = day or date.today()
        self.skipped: list[tuple[Pet, Task, str]] = []

    def build_daily_plan(self) -> list[ScheduledItem]:
        """Plan pending tasks across all pets.

        Tasks with a fixed time are placed first, at that time. The rest go
        highest priority first (shorter first on ties) into the earliest free gap.
        Anything that overlaps or doesn't fit in the owner's time is skipped.
        """
        pending = [
            (p, t) for p, t in self.owner.filter_tasks(completed=False) if t.due_date <= self.day
        ]
        fixed = sort_by_time([pt for pt in pending if pt[1].time])
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

    def mark_task_complete(self, pet: Pet, task: Task) -> Task | None:
        """Complete a task for a pet; daily/weekly tasks automatically get a next occurrence.

        Returns the new task, or None if nothing recurs. See Pet.complete_task.
        """
        return pet.complete_task(task)

    def sort_by_time(self, pairs: list[tuple[Pet, Task]] | None = None) -> list[tuple[Pet, Task]]:
        """Sort (pet, task) pairs by their "HH:MM" time, flexible tasks last.

        Pass a filtered list to sort just that; leave it out to sort every task
        the owner has. See the module-level sort_by_time for how the key works.
        """
        return sort_by_time(self.owner.get_all_tasks() if pairs is None else pairs)

    def filter_tasks(
        self, pet_name: str | None = None, completed: bool | None = None
    ) -> list[tuple[Pet, Task]]:
        """Filter the owner's tasks by pet name and/or completion status.

        Same as Owner.filter_tasks, here so sorting and filtering can both be
        called on the scheduler.
        """
        return self.owner.filter_tasks(pet_name, completed)

    def detect_conflicts(self) -> list[str]:
        """Warn about fixed-time tasks that overlap (same pet or different pets).

        Only pending tasks with a fixed time on the same day are compared.
        They are sorted by start time, and each task is checked against the
        ones that start after it until one starts at or after its end, since
        nothing later can overlap. Back-to-back tasks (one ends when the next
        starts) are not conflicts.

        Returns a list of warning strings, empty if there are none. It only
        reports problems and never raises or changes anything.
        """
        fixed = sort_by_time([pt for pt in self.owner.filter_tasks(completed=False) if pt[1].time])
        warnings = []
        for i, (pet_a, a) in enumerate(fixed):
            for pet_b, b in fixed[i + 1 :]:
                if b.start_minute >= a.end_minute:
                    break  # sorted by start, so nothing later can overlap a
                if a.due_date == b.due_date:
                    warnings.append(self._conflict_message(pet_a, a, pet_b, b))
        return warnings

    @staticmethod
    def _conflict_message(pet_a: Pet, a: Task, pet_b: Pet, b: Task) -> str:
        """Describe one clash in plain words, e.g. for the warning list."""
        scope = "same pet" if pet_a is pet_b else "different pets"
        return (
            f"Conflict ({scope}): '{a.title}' for {pet_a.name} "
            f"({a.time}-{format_time(a.end_minute)}) overlaps '{b.title}' for {pet_b.name} "
            f"(starts {b.time})"
        )

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
