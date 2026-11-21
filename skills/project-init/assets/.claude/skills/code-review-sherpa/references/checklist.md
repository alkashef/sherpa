# Review checklist

The parts follow "What to look for in a code review" of Google's Engineering Practices. The smell
names come from the catalog of refactoring.guru. Sources are at the end.

## The four standards

1. **Write for the average programmer.** Ask of each function: can a programmer who did not write
   this code explain it after one reading?
2. **No complicated patterns.** A design pattern is permitted only when a `Decided` decision in
   `docs/design.md` names it. Signs of a pattern that nobody asked for: a factory, a strategy, a
   visitor, an observer, a registry of plug-ins, a base class with one subclass, a decorator or
   a metaclass that hides the flow of the program.
3. **Readable code comes before clever code.** When two rules disagree, the more readable code
   wins. Signs of clever code: a nested comprehension, a nested conditional expression, a trick
   with an operator, behavior that happens with no visible call, a name that is an abbreviation.
4. **Only the 8 smells below.** Do not look for other smells.

## What to look for

### Design

- The change obeys the table "Module boundaries" and the interfaces of `docs/design.md`.
- The change follows each `Decided` decision that applies to it.
- Each new function, class and module does one thing.

### Function

- The code does what its requirement says, for each acceptance example of that requirement.
- The code is not written only for the test data: no result that is fixed to the value that a
  test expects.
- A failure stays visible: no silent fallback, no swallowed error, and no retry that no
  requirement asks for.

### Complexity

- No over-engineering: the code is not more general than the present requirement needs, and it
  adds no function that the system does not use now.
- The same holds for a test: a test is code that someone must maintain.

### Tests

- A test asserts behavior that the spec states, not how the code is built.
- The reviewer and the repair session do not change a test. Report a test that is wrong as a
  finding. It stays in the report for the user.

### Naming

- A name says what the thing is or does. One thing has one name in the whole change.

### Comments

- A comment says why, not what. It does not repeat the code, and it does not tell the history of
  the change.

## The 8 smells

| Smell | What it looks like | Simplest remedy |
| --- | --- | --- |
| Speculative Generality | An option, a parameter, a layer, an interface or a hook that no requirement and no caller uses | Delete it, or put the one case in line |
| Duplicate Code | New logic or a new helper that the project already has | Use the code that exists. Extract a helper on the second use |
| Dead Code | A function, a parameter or a branch that nothing uses, or code that is kept "for compatibility" | Delete it |
| Middle Man and Lazy Class | A class or a function that only passes a call on, or a class that is too small to have a reason | Call the target directly, or put the code in line |
| Comments | A comment that repeats the code | Delete the comment. Rename, so that the code says it |
| Long Method | A function that does two things. The tools already limit its length and its complexity | Extract a function |
| Long Parameter List | Values that always travel together. The tools already limit the count | Group them in one typed object |
| Large Class | A class or a module with more than one responsibility | Divide it by responsibility, one class per file |

## Never

- Never propose "Replace Conditional with Polymorphism". A plain `if` chain or a lookup table is
  the remedy for a long conditional.
- Never report Switch Statements, Primitive Obsession or Data Clumps.
- Never propose a design pattern as a remedy.

## Sources

- [Google Engineering Practices: What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html)
- [refactoring.guru: Code smells](https://refactoring.guru/refactoring/smells)
