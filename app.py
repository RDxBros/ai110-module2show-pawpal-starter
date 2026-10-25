import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task, parse_time, sort_by_time

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()


# The "vault": create the Owner once, then reuse it on every rerun.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner = st.session_state.owner

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_minutes = st.number_input(
    "Minutes available today", min_value=10, max_value=1440, value=owner.available_minutes
)

st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Please enter a pet name.")
        elif any(p.name.lower() == pet_name.strip().lower() for p in owner.pets):
            st.error(f"You already have a pet named {pet_name.strip()}.")
        else:
            owner.add_pet(Pet(name=pet_name.strip(), species=species))
            st.success(f"Added {pet_name.strip()}!")

if owner.pets:
    st.write("Your pets:")
    st.table([{"name": p.name, "species": p.species, "tasks": len(p.tasks)} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.subheader("Add a Task")
if owner.pets:
    with st.form("add_task_form", clear_on_submit=True):
        pet_choice = st.selectbox("For which pet?", [p.name for p in owner.pets])
        task_title = st.text_input("Task title", placeholder="Morning walk")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col3:
            fixed_time = st.text_input("Fixed time (optional)", placeholder="HH:MM")
        with col4:
            frequency = st.selectbox("Repeats", ["once", "daily", "weekly"], index=1)
        if st.form_submit_button("Add task"):
            fixed_time = fixed_time.strip()
            try:
                if fixed_time:
                    parse_time(fixed_time)
            except ValueError:
                st.error("Time must look like 08:30.")
            else:
                if not task_title.strip():
                    st.error("Please enter a task title.")
                else:
                    pet = next(p for p in owner.pets if p.name == pet_choice)
                    pet.add_task(
                        Task(
                            title=task_title.strip(),
                            duration_minutes=int(duration),
                            priority=Priority[priority.upper()],
                            time=fixed_time or None,
                            frequency=frequency,
                        )
                    )
                    st.success(f"Added '{task_title.strip()}' for {pet_choice}.")
else:
    st.info("Add a pet first, then you can give it tasks.")

if owner.get_all_tasks():
    st.write("Current tasks:")
    for warning in Scheduler(owner).detect_conflicts():
        st.warning(warning)

    f1, f2 = st.columns(2)
    pet_filter = f1.selectbox("Filter by pet", ["All"] + [p.name for p in owner.pets])
    status_filter = f2.selectbox("Filter by status", ["All", "Pending", "Completed"])
    shown = owner.filter_tasks(
        pet_name=None if pet_filter == "All" else pet_filter,
        completed={"All": None, "Pending": False, "Completed": True}[status_filter],
    )
    st.table(
        [
            {
                "pet": pet.name,
                "task": task.title,
                "minutes": task.duration_minutes,
                "priority": task.priority.name.lower(),
                "time": task.time or "flexible",
                "repeats": task.frequency,
                "due": str(task.due_date),
                "done": task.completed,
            }
            for pet, task in sort_by_time(shown)
        ]
    )

    pending = owner.filter_tasks(completed=False)
    if pending:
        labels = {f"{pet.name}: {task.title} ({task.due_date})": (pet, task) for pet, task in pending}
        choice = st.selectbox("Mark a task complete", list(labels))
        if st.button("Complete task"):
            pet, task = labels[choice]
            following = pet.complete_task(task)
            if following:
                st.success(f"Done! Next '{task.title}' scheduled for {following.due_date}.")
            else:
                st.success("Done!")
            st.rerun()

st.divider()

st.subheader("Build Schedule")
if st.button("Generate schedule"):
    if not owner.get_all_tasks():
        st.warning("Add at least one task first.")
    else:
        scheduler = Scheduler(owner)
        plan = scheduler.build_daily_plan()
        st.code(scheduler.explain_plan(plan), language=None)
