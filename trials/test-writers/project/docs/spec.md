# Spec — slugger

Status: Approved

What to build. Written with `/write-spec`. Change only with the user's approval. Each requirement is
in EARS syntax and has an ID that tests cite.

## 1. Purpose and scope

A command-line tool that turns a title into a URL slug. A blog author pastes a title and copies
the slug into the address of the post. In scope: one title per run, from the command line. Out of
scope: files, batches, other languages' transliteration (for example Japanese to Latin letters).

## 2. Roles and glossary

Role: the author, who runs the tool in a terminal.

| Term | Meaning | Avoid |
| --- | --- | --- |
| Title | The text that the author gives to the tool | name, input string |
| Slug | The result: lowercase ASCII letters, digits and single hyphens | permalink, handle |
| Word | A run of letters and digits in the slug, between hyphens | token |
| Maximum length | The most characters that the slug may hold | limit, width |

## 3. User scenarios

### SCN-001 Make a slug

- Actor and goal: the author wants a slug for a new post.
- Trigger: the author runs `python main.py "<title>"`, with or without `--max N`.
- Main success path: the tool prints the slug and exits with 0.
- Failure paths: a title with no letters or digits; a `--max` value that is not valid.
- Observable result: the slug on standard output, or an error on standard error.
- Source: the author, confirmed.

## 4. Functional requirements

| ID | EARS requirement | Priority | Status | Business reason | Source | Scenarios | Examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SLUG-001 | The tool shall make a slug that holds only the lowercase ASCII letters a to z, the digits 0 to 9 and hyphens. | Must | Confirmed | Safe in every URL | Author | SCN-001 | EX-001 |
| SLUG-002 | When a letter of the title has an accent or a compatibility form, the tool shall use its plain ASCII letter (NFKD decomposition), and it shall drop each character that has no ASCII form. | Must | Confirmed | Readable slugs for French and German titles | Author | SCN-001 | EX-002, EX-009, EX-010 |
| SLUG-003 | The tool shall replace each run of characters that are not letters or digits with one hyphen, and the slug shall not start or end with a hyphen. | Must | Confirmed | Clean addresses | Author | SCN-001 | EX-001, EX-003 |
| SLUG-004 | When the slug is longer than the maximum length, the tool shall keep the longest run of whole words, from the start, that fits in the maximum length. If the first word alone is longer, the tool shall keep its first characters, up to the maximum length. | Must | Confirmed | Short addresses | Author | SCN-001 | EX-004, EX-005 |
| SLUG-005 | When the author runs `python main.py TITLE [--max N]`, the tool shall print the slug and a newline to standard output and exit with 0. The default maximum length is 60. | Must | Confirmed | Use from a terminal | Author | SCN-001 | EX-006 |
| SLUG-006 | If the title gives an empty slug, then the tool shall print `error: the title has no letters or digits` and a newline to standard error, print nothing to standard output, and exit with 2. | Must | Confirmed | A clear error | Author | SCN-001 | EX-007 |
| SLUG-007 | If the value of `--max` is not an integer from 1 to 200, then the tool shall print `error: --max must be an integer from 1 to 200` and a newline to standard error, print nothing to standard output, and exit with 2. | Must | Confirmed | A clear error | Author | SCN-001 | EX-008 |

## 5. Non-functional requirements

| ID | EARS requirement | Priority | Status | Business reason | Source | Acceptance evidence |
| --- | --- | --- | --- | --- | --- | --- |

## 6. Acceptance examples

| ID | Requirement IDs | Situation and input | Expected result | Reviewed by |
| --- | --- | --- | --- | --- |
| EX-001 | SLUG-001, SLUG-003 | Title `Hello, World!` | `hello-world` | Author |
| EX-002 | SLUG-002 | Title `Crème Brûlée` | `creme-brulee` | Author |
| EX-003 | SLUG-003 | Title `  --Rock & Roll--  ` | `rock-roll` | Author |
| EX-004 | SLUG-004 | Title `The quick brown fox jumps`, maximum length 15 | `the-quick-brown` | Author |
| EX-005 | SLUG-004 | Title `Supercalifragilistic`, maximum length 5 | `super` | Author |
| EX-006 | SLUG-005 | `python main.py "Hello World"` | Standard output `hello-world` and a newline, exit code 0 | Author |
| EX-007 | SLUG-006 | `python main.py "!!!"` | The error on standard error, nothing on standard output, exit code 2 | Author |
| EX-008 | SLUG-007 | `python main.py "Hello" --max 0` | The error on standard error, nothing on standard output, exit code 2 | Author |
| EX-009 | SLUG-002 | Title `50 K` (the last character is the Kelvin sign, U+212A) | `50-k` | Author |
| EX-010 | SLUG-002 | Title `日本 Tokyo` | `tokyo` | Author |

## 7. Assumptions and open questions

| Item | Evidence or assumption | Consequence if wrong | Owner | Resolution or revisit condition |
| --- | --- | --- | --- | --- |

## 8. Review and approval

Approved by the author on November 21, 2026, in full.
