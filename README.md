# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

## Core user actions

1. **Add a pet** - enter owner info and a pet (name, species).
2. **Add a care task** - give a pet a task (walk, feeding, meds...) with duration and priority.
3. **Generate and view today's plan** - build a daily schedule that fits the owner's available time, ordered by priority, with an explanation of each choice.

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Implementation summary

The backend lives in `pawpal_system.py` and is tested from the command line (`main.py`) before any UI work.

- **Owner** keeps a list of pets and how many minutes the owner has today. `get_all_tasks()` collects every pet's tasks into one list.
- **Pet** stores its details and its own list of **Task**s.
- **Task** is one activity: title, duration, priority, frequency, an optional fixed time, and whether it's done.
- **Scheduler** reads everything through `owner.get_all_tasks()`, so it plans across all pets at once. Fixed-time tasks go in first, the rest fill the gaps by priority, and anything that conflicts or doesn't fit is skipped with a reason.
- **ScheduledItem** is the result: a task, its pet, a start time and the reason it was chosen.

## 🖥️ Sample Output

Output from `python main.py`:

```
Today's Schedule for Jordan (60 min available):
  08:00 - Morning walk for Biscuit (30 min) [fixed at 08:00; high priority]
  08:30 - Feeding for Mochi (10 min) [high priority; 10 min fits in the 10 min left]
  09:00 - Laser play for Mochi (15 min) [fixed at 09:00; medium priority]
  12:00 - Give meds for Mochi (5 min) [fixed at 12:00; high priority]
  Skipped: Brush coat for Biscuit (20 min) - not enough time left
```

Tasks with a fixed time keep it, flexible tasks fill the gaps by priority, and anything that doesn't fit in the owner's time is skipped with a reason.

## Testing PawPal+

Run the full suite from the project root:

```bash
python -m pytest
```

**What the tests cover** (`tests/test_pawpal.py`, 21 tests):

- **Sorting:** tasks come back in chronological order (`"9:00"` before `"10:00"`), flexible tasks go last, ties keep input order, and an empty list is fine.
- **Recurrence:** completing a daily task adds a copy due tomorrow, a weekly task adds one due in 7 days, and a "once" task adds nothing. Completing twice never duplicates, and next-day copies stay out of today's plan.
- **Conflict detection:** duplicate start times and partial overlaps are flagged (same pet and different pets). Back-to-back tasks, tasks on different days, completed tasks and flexible tasks are not.
- **Planning and filtering:** fixed tasks keep their time, high priority is placed first, overflow and conflicting tasks are skipped with a reason, an empty owner gives an empty plan, and filtering by pet name (case-insensitive) and status works.

Sample test output:

```
============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\todee\Downloads\ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 21 items

tests\test_pawpal.py .....................                               [100%]

============================= 21 passed in 0.07s ==============================
```

**Confidence Level: ★★★★☆ (4/5)**

All 21 tests pass and they cover the core behaviors and the main edge cases. I'm holding back one star because a few cases are untested: invalid time strings such as `"9am"` crash `parse_time`, an empty `time=""` is treated differently by sorting and planning, and fixed tasks aren't checked against the end of the day.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting | `Scheduler.sort_by_time()` (uses `sort_by_time()`) | By fixed `HH:MM` time; flexible tasks last |
| Filtering | `Scheduler.filter_tasks()` (uses `Owner.filter_tasks()`) | By pet name and/or completion status |
| Conflict detection | `Scheduler.detect_conflicts()` | Warns about overlapping fixed-time tasks |
| Recurring tasks | `Task.mark_complete()`, `Task.next_occurrence()`, `Pet.complete_task()`, `Scheduler.mark_task_complete()` | Daily = +1 day, weekly = +7 days |

### Sorting

`Scheduler.sort_by_time(pairs=None)` orders `(pet, task)` pairs by their fixed time. It uses `sorted()` with a lambda key that returns a tuple, `(has no time, minutes since midnight)`. Timed tasks come first in clock order and flexible tasks go last. Times are converted with `parse_time()` instead of compared as text, so `"9:00"` correctly comes before `"10:00"`. Pass in a filtered list to sort only that, or leave it out to sort everything.

### Filtering

`Scheduler.filter_tasks(pet_name=None, completed=None)` narrows the owner's tasks by pet name (ignores case) and/or status. `completed=True` gives done tasks, `False` gives pending ones, and `None` doesn't filter on status. It's a thin wrapper over `Owner.filter_tasks()`. Filtering and sorting chain together, for example `scheduler.sort_by_time(scheduler.filter_tasks("Mochi", completed=False))`.

### Conflict detection

`Scheduler.detect_conflicts()` is a lightweight check that returns a list of warning strings instead of raising or changing anything. It looks at pending, fixed-time tasks on the same day, sorts them by start time, and checks each one only against the tasks that start before it ends. It catches real overlaps, not just identical start times, and works for the same pet or different pets. Back-to-back tasks are fine. Example:

```
Conflict (same pet): 'Nail trim' for Biscuit (14:00-14:15) overlaps 'Training' for Biscuit (starts 14:00)
```

`build_daily_plan()` also skips a fixed task that overlaps one already placed, and lists it under "Skipped" with the reason. The earlier task wins, even if the later one has a higher priority.

### Recurring tasks

Each `Task` has a `frequency` of `"once"`, `"daily"` or `"weekly"` and a `due_date`. `Task.mark_complete()` marks the task done and returns the next occurrence from `Task.next_occurrence()`, due `today + timedelta(days=1)` for daily or `today + timedelta(days=7)` for weekly. It returns `None` for `"once"` tasks, and for a task that was already complete, so it never duplicates. `Pet.complete_task()` (also reachable as `Scheduler.mark_task_complete(pet, task)`) adds the new task to the pet. Because the next copy is based on today, finishing a task late doesn't leave it overdue. The scheduler only plans tasks whose `due_date` is today or earlier.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
