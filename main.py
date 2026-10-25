"""CLI demo: exercise the PawPal+ backend before touching the Streamlit UI."""

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

owner = Owner(name="Jordan", available_minutes=60)

biscuit = Pet(name="Biscuit", species="dog", age=4)
mochi = Pet(name="Mochi", species="cat", age=2)
owner.add_pet(biscuit)
owner.add_pet(mochi)

# Added deliberately out of time order.
mochi.add_task(Task("Give meds", 5, Priority.HIGH, "meds", frequency="once", time="12:00"))
biscuit.add_task(Task("Brush coat", 20, Priority.LOW, "grooming"))
mochi.add_task(Task("Laser play", 15, Priority.MEDIUM, "enrichment", time="09:00"))
biscuit.add_task(Task("Evening walk", 30, Priority.HIGH, "walk", time="18:30"))
mochi.add_task(Task("Feeding", 10, Priority.HIGH, "feeding"))
biscuit.add_task(Task("Morning walk", 30, Priority.HIGH, "walk", time="08:00"))
biscuit.add_task(Task("Vet call", 10, Priority.MEDIUM, "other", time="09:05"))  # overlaps Laser play

# Exact same start time: one clash on the same pet, one across different pets.
biscuit.add_task(Task("Nail trim", 15, Priority.MEDIUM, "grooming", time="14:00"))
biscuit.add_task(Task("Training", 20, Priority.MEDIUM, "enrichment", time="14:00"))
mochi.add_task(Task("Litter clean", 10, Priority.LOW, "other", time="18:30"))  # same time as Evening walk

scheduler = Scheduler(owner)
# Mark one task done so the status filter has something to show.
biscuit.complete_task(next(t for t in biscuit.tasks if t.title == "Morning walk"))


def show(heading, pairs):
    print(f"\n{heading}")
    for pet, task in pairs:
        status = "done" if task.completed else "pending"
        print(f"  {task.time or 'flexible':>8}  {task.title:<13} {pet.name:<8} {status}  due {task.due_date}")


show("Insertion order (unsorted):", owner.get_all_tasks())
show("Sorted by time:", scheduler.sort_by_time())
show("Pet = Mochi:", scheduler.filter_tasks(pet_name="Mochi"))
show("Pending only:", scheduler.filter_tasks(completed=False))
show("Completed only:", scheduler.filter_tasks(completed=True))
show("Biscuit + pending, sorted:", scheduler.sort_by_time(scheduler.filter_tasks("Biscuit", False)))

print("\nConflicts:")
for warning in scheduler.detect_conflicts() or ["none"]:
    print(f"  {warning}")

print()
print(scheduler.explain_plan(scheduler.build_daily_plan()))
