"""CLI demo: exercise the PawPal+ backend before touching the Streamlit UI."""

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

owner = Owner(name="Jordan", available_minutes=60)

biscuit = Pet(name="Biscuit", species="dog", age=4)
mochi = Pet(name="Mochi", species="cat", age=2)
owner.add_pet(biscuit)
owner.add_pet(mochi)

biscuit.add_task(Task("Morning walk", 30, Priority.HIGH, "walk", time="08:00"))
biscuit.add_task(Task("Brush coat", 20, Priority.LOW, "grooming"))
mochi.add_task(Task("Feeding", 10, Priority.HIGH, "feeding"))
mochi.add_task(Task("Laser play", 15, Priority.MEDIUM, "enrichment", time="09:00"))
mochi.add_task(Task("Give meds", 5, Priority.HIGH, "meds", frequency="once", time="12:00"))

scheduler = Scheduler(owner)
plan = scheduler.build_daily_plan()
print(scheduler.explain_plan(plan))
