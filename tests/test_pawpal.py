from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", 30)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="cat")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", 10))

    assert len(pet.tasks) == 1


from datetime import date, timedelta

from pawpal_system import Owner, Priority, Scheduler, sort_by_time


def make_owner():
    owner = Owner(name="Jordan")
    dog, cat = Pet("Biscuit", "dog"), Pet("Mochi", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner, dog, cat


def test_sort_by_time_orders_fixed_then_flexible():
    owner, dog, cat = make_owner()
    dog.add_task(Task("Flexible", 10))
    dog.add_task(Task("Late", 10, time="14:00"))
    cat.add_task(Task("Early", 10, time="07:30"))

    titles = [t.title for _, t in sort_by_time(owner.get_all_tasks())]

    assert titles == ["Early", "Late", "Flexible"]


def test_filter_by_pet_and_status():
    owner, dog, cat = make_owner()
    done = Task("Walk", 20)
    dog.add_task(done)
    dog.add_task(Task("Brush", 10))
    cat.add_task(Task("Feed", 5))
    done.mark_complete()

    assert len(owner.filter_tasks(pet_name="biscuit")) == 2
    assert [t.title for _, t in owner.filter_tasks(pet_name="Biscuit", completed=False)] == ["Brush"]
    assert [t.title for _, t in owner.filter_tasks(completed=True)] == ["Walk"]


def test_completing_daily_task_creates_next_day_copy():
    _, dog, _ = make_owner()
    walk = Task("Walk", 20, frequency="daily")
    dog.add_task(walk)

    following = dog.complete_task(walk)

    assert walk.completed and following is not None and not following.completed
    assert following.due_date == date.today() + timedelta(days=1)
    assert len(dog.tasks) == 2


def test_completing_weekly_adds_seven_days_and_once_adds_nothing():
    _, dog, _ = make_owner()
    weekly, once = Task("Bath", 30, frequency="weekly"), Task("Vet", 60, frequency="once")
    dog.add_task(weekly)
    dog.add_task(once)

    assert dog.complete_task(weekly).due_date == date.today() + timedelta(days=7)
    assert dog.complete_task(once) is None
    assert len(dog.tasks) == 3


def test_future_task_not_scheduled_today():
    owner, dog, _ = make_owner()
    walk = Task("Walk", 20)
    dog.add_task(walk)
    dog.complete_task(walk)  # next copy is due tomorrow

    plan = Scheduler(owner).build_daily_plan()

    assert plan == []
    assert len(Scheduler(owner, day=date.today() + timedelta(days=1)).build_daily_plan()) == 1


def test_detect_conflicts_flags_overlap_across_pets():
    owner, dog, cat = make_owner()
    dog.add_task(Task("Walk", 30, time="08:00"))
    cat.add_task(Task("Play", 15, time="08:20"))
    cat.add_task(Task("Feed", 10, time="09:00"))  # adjacent/free, no conflict

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1 and "different pets" in warnings[0]


def test_detect_conflicts_none_when_back_to_back():
    owner, dog, _ = make_owner()
    dog.add_task(Task("A", 30, time="08:00"))
    dog.add_task(Task("B", 30, time="08:30"))

    assert Scheduler(owner).detect_conflicts() == []


def test_late_completion_recurs_from_today_not_old_due_date():
    _, dog, _ = make_owner()
    walk = Task("Walk", 20, frequency="daily", due_date=date.today() - timedelta(days=3))
    dog.add_task(walk)

    following = dog.complete_task(walk)

    assert following.due_date == date.today() + timedelta(days=1)


def test_completing_twice_does_not_duplicate():
    owner, dog, _ = make_owner()
    walk = Task("Walk", 20, frequency="daily")
    dog.add_task(walk)

    Scheduler(owner).mark_task_complete(dog, walk)
    Scheduler(owner).mark_task_complete(dog, walk)

    assert len(dog.tasks) == 2


def test_detect_conflicts_ignores_different_days():
    owner, dog, _ = make_owner()
    dog.add_task(Task("Walk", 30, time="08:00"))
    dog.add_task(Task("Walk", 30, time="08:00", due_date=date.today() + timedelta(days=1)))

    assert Scheduler(owner).detect_conflicts() == []


def test_sort_by_time_is_chronological_not_alphabetical():
    owner, dog, _ = make_owner()
    dog.add_task(Task("Ten", 10, time="10:00"))
    dog.add_task(Task("Nine", 10, time="9:00"))
    dog.add_task(Task("Noon", 10, time="12:00"))

    titles = [t.title for _, t in sort_by_time(owner.get_all_tasks())]

    assert titles == ["Nine", "Ten", "Noon"]


def test_sort_by_time_keeps_input_order_on_ties_and_handles_empty():
    owner, dog, cat = make_owner()
    assert sort_by_time([]) == []

    dog.add_task(Task("First", 10, time="08:00"))
    cat.add_task(Task("Second", 10, time="08:00"))

    titles = [t.title for _, t in sort_by_time(owner.get_all_tasks())]

    assert titles == ["First", "Second"]


def test_scheduler_sort_by_time_accepts_filtered_pairs():
    owner, dog, cat = make_owner()
    dog.add_task(Task("Late", 10, time="15:00"))
    dog.add_task(Task("Early", 10, time="06:00"))
    cat.add_task(Task("Other", 10, time="01:00"))

    scheduler = Scheduler(owner)
    pairs = scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Biscuit"))

    assert [t.title for _, t in pairs] == ["Early", "Late"]


def test_detect_conflicts_flags_duplicate_times():
    owner, dog, cat = make_owner()
    dog.add_task(Task("Walk", 30, time="08:00"))
    cat.add_task(Task("Play", 30, time="08:00"))

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0] and "different pets" in warnings[0]


def test_detect_conflicts_same_pet_duplicate_time():
    owner, dog, _ = make_owner()
    dog.add_task(Task("Walk", 30, time="08:00"))
    dog.add_task(Task("Brush", 10, time="08:00"))

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1 and "same pet" in warnings[0]


def test_detect_conflicts_ignores_completed_and_flexible_tasks():
    owner, dog, _ = make_owner()
    done = Task("Walk", 30, time="08:00")
    dog.add_task(done)
    dog.add_task(Task("Brush", 10, time="08:00"))
    dog.add_task(Task("Flexible", 10))
    done.mark_complete()

    assert Scheduler(owner).detect_conflicts() == []


def test_plan_skips_conflicting_fixed_task_with_reason():
    owner, dog, cat = make_owner()
    dog.add_task(Task("Walk", 30, time="08:00"))
    cat.add_task(Task("Play", 30, time="08:00"))

    scheduler = Scheduler(owner)
    plan = scheduler.build_daily_plan()

    assert len(plan) == 1
    assert [why for _, _, why in scheduler.skipped] == ["conflicts with another task"]


def test_plan_places_high_priority_flexible_first_and_skips_overflow():
    owner, dog, _ = make_owner()
    owner.available_minutes = 30
    dog.add_task(Task("Low", 20, priority=Priority.LOW))
    dog.add_task(Task("High", 20, priority=Priority.HIGH))

    scheduler = Scheduler(owner)
    plan = scheduler.build_daily_plan()

    assert [i.task.title for i in plan] == ["High"]
    assert [t.title for _, t, _ in scheduler.skipped] == ["Low"]


def test_empty_owner_plan_is_empty():
    owner = Owner(name="Nobody")
    scheduler = Scheduler(owner)

    assert scheduler.build_daily_plan() == []
    assert "Nothing scheduled." in scheduler.explain_plan([])
