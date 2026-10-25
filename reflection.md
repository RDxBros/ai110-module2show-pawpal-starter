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

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
