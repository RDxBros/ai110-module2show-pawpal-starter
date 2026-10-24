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
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
