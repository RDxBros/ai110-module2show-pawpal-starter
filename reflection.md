# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design. 

An owner has pets, a pet has tasks, and a separate scheduler looks at everything and builds the day's plan. The idea was to keep the data (who and what) apart from the logic (when and why).

- What classes did you include, and what responsibilities did you assign to each?

1. Owner: holds the owner's name, how much time they have each day, and their preferences. It also keeps the list of pets.
2. Pet: holds the pet's name and species, plus the tasks that pet needs.
3. Task: one task, with a title, duration, priority and category, and whether it's done.
4. Scheduler: it takes the owner's tasks, picks what fits in the available time, orders them by priority, and explains why.
5. ScheduledItem: one task placed at a start time, with a short reason.



**b. Design changes**

- Did your design change during implementation? Yes
- If yes, describe at least one change and why you made it. I changed Task.priority from a string to a Priority enum with LOW = 1, MEDIUM = 2 and HIGH = 3. Strings sort alphabetically, so "high" would be before "medium" and "low" would come last. With numbers behind the names, the scheduler can just sort by priority. A typo like "hgih" will not be accepted anymore, because the enum rejects any name it doesn't have.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

It looks at four things: how many minutes the owner has today, each task's priority, fixed start times, and whether a task is due yet. Preferences are stored on the owner, but the scheduler doesn't use them yet.

- How did you decide which constraints mattered most?

I ordered them by what would hurt a pet most if it went wrong. A fixed time like meds at 12:00 is a promise, so those get placed first. After that, the owner's time limit is a hard stop, and priority decides who gets the time that is left. High priority goes first, and shorter tasks win ties so more things fit.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

Fixed-time tasks are placed in time order, not priority order. If a low priority task is fixed at 08:00 and a high priority one is fixed at 08:15 and they overlap, the earlier one wins and the later one is skipped, even though it matters more. The scheduler also only warns about the clash. It doesn't try to move anything.

I did go with real overlap checking instead of only matching exact start times, so a 30 minute walk at 08:00 does clash with a task at 08:20. Back-to-back tasks (one ends at 08:30, the next starts at 08:30) are not a clash.

- Why is that tradeoff reasonable for this scenario?

The owner picked those times on purpose, so quietly moving them could be worse than a skipped task. Warning them and letting them decide keeps them in control, and it keeps the code simple enough to read and test. For a handful of pets and tasks a day, that is enough. The cost is that the owner sometimes has to fix the clash by hand. If I had more time, I would let priority break the tie.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

I used AI to brainstorm the classes, draft the UML, write the class skeleton, and then fill in the scheduler. I also asked it to review the skeleton for missing relationships and bottlenecks.

- What kinds of prompts or questions were most helpful?

Asking it to review my own skeleton was the most useful. It pointed out that a task doesn't know which pet it belongs to, and that string priorities sort in the wrong order.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

The AI listed several changes after reviewing my skeleton (priority enum, pairing tasks with pets, returning skipped tasks, recurrence, fixed times). I took them one at a time instead of all at once, starting with the priority enum. Its first `main.py` also didn't meet my requirements, because the tasks had no times of their own, so I had it add a per-task time field.

- How did you evaluate or verify what the AI suggested?

I ran `main.py` and read the schedule to check the order and times made sense. That also caught a bug right away, a broken newline in the code that stopped the import. I then wrote two small pytest tests and they pass.

**c. AI strategy**

- Which AI coding assistant features were most effective for building your scheduler?

Three things worked best. First, reading my existing code before answering: asking it to review `pawpal_system.py` produced a list of behaviors and edge cases to test, instead of generic advice. Second, running commands itself. It ran pytest and `main.py` and showed me the real output, so I could put that output in the README without retyping anything. Third, it could drive the Streamlit app headlessly to check that the page loaded and the conflict warning appeared, which caught errors before I opened a browser.

- Give one example of an AI suggestion you rejected or modified to keep your system design clean.

While reviewing the scheduler, the AI called `next_occurrence` a bug because it builds the next date from `date.today()` instead of the task's old due date. I had already decided on that behavior and had a test for it, `test_late_completion_recurs_from_today_not_old_due_date`. A daily walk finished three days late should come back tomorrow, not sit overdue in the past. I kept my design and the test, and the AI dropped the claim. The same thing happened with the conflict warnings. The AI suggested more structure, such as having `detect_conflicts()` return objects so the UI could offer fixes, but that would have changed the backend and its tests. I kept plain warning strings and put the helpful wording in the UI.

- How did using separate chat sessions for different phases help you stay organized?

My commits follow the phases: blueprint and UML, class skeleton, core scheduling, connecting the UI, sorting/filtering/conflicts, then tests and docs. Keeping each phase in its own session meant the AI worked from the code as it was, not from an old plan in a long conversation. The cost was that a new session didn't remember earlier decisions, such as recurrence being based on today, so I had to restate them. The tests turned out to be the best record of those decisions.

- Summarize what you learned about being the "lead architect" when collaborating with powerful AI tools.

The AI is fast, so the risk is that it makes lots of changes and I stop checking them. As lead architect my job was to decide what the system should do, and to check each claim against the code and the tests. I took suggestions one at a time. I rejected the ones that changed design decisions I'd already made. The AI could write code and tests quickly, but only I knew what a good schedule looks like for a pet owner. The diagram, README and reflection also went out of date as the code grew, so keeping them in sync is part of the architect's job too.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

There are 21 pytest tests. They cover sorting (`"9:00"` before `"10:00"`, flexible tasks last, ties keep their order), recurrence (daily +1 day, weekly +7 days, "once" creates nothing, completing twice doesn't duplicate), conflict detection (duplicate times, partial overlaps, same and different pets, and no warning for back-to-back, different-day, completed or flexible tasks), filtering, and plan building (priority order, skipped tasks with reasons, an empty plan).

- Why were these tests important?

These are the behaviors a pet owner relies on. A missed conflict means two tasks at the same time, and a wrong sort order makes the schedule confusing. A duplicate recurring task would clutter every day after it.

**b. Confidence**

- How confident are you that your scheduler works correctly?

4 out of 5. All 21 tests pass and they cover the core behaviors and the main edge cases.

- What edge cases would you test next if you had more time?

Invalid time strings such as `"9am"` currently crash `parse_time` in the backend. An empty `time=""` is sorted as midnight but planned as flexible. Fixed tasks aren't checked against the start or end of the day, so a 23:30 task of 60 minutes is accepted. I would also test removing a task by title when a completed original and its recurring copy share that title.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with how the scheduler stays understandable. The data classes, the sorting and conflict functions, and the planner are separate, so each one can be tested alone, and the Streamlit UI only calls `Scheduler` methods. Conflict detection also checks real overlaps, not just matching start times.

**b. What you would improve**

I would make `detect_conflicts()` return structured data (the two tasks and their times) so the UI could suggest a fix, like moving a task to the next free slot. I would also let priority break ties between overlapping fixed tasks, and validate time strings in the backend, not only in the UI.

**c. Key takeaway**

Design decisions have to be written down where they can be checked, and tests are the best place. When the AI questioned my recurrence rule, the test showed it was deliberate. Working with AI went best when I decided what the system should do and used the AI to build and check it.
