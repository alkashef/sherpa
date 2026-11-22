# Spec — ledger

Status: Approved

What to build. Written with `/write-spec`. Change only with the user's approval. Each requirement is
in EARS syntax and has an ID that tests cite.

## 1. Purpose and scope

A command-line tool that keeps a ledger of small expenses in one data file. A person adds an
expense after each purchase, and reads the total of a category at the end of the month. In scope:
add, total and list, from the command line, one data file. Out of scope: edit or delete an entry,
currencies, reports, more than one user.

## 2. Roles and glossary

Role: the owner of the ledger, who runs the tool in a terminal.

| Term | Meaning | Avoid |
| --- | --- | --- |
| Entry | One expense in the ledger: ID, amount, category, note and time | record, row, item |
| Amount | The money of one entry, in euros and cents | value, price, sum |
| Category | A word that groups entries, such as `food` | tag, label, type |
| Note | A free text of one entry; it can be empty | comment, description |
| Data file | The JSON file that holds the entries | database, store file |
| Total | The sum of the amounts of the entries | balance |

## 3. User scenarios

### SCN-001 Add an expense

- Actor and goal: the owner wants to record one purchase.
- Trigger: the owner runs `python main.py add AMOUNT CATEGORY [--note TEXT]`.
- Main success path: the tool stores the entry, prints its ID and exits with 0.
- Failure paths: an amount that is not valid; a category that is not valid; a data file that is
  not a valid ledger.
- Observable result: the ID on standard output, or an error on standard error.
- Source: the owner, confirmed.

### SCN-002 Read the ledger

- Actor and goal: the owner wants the total of a category, or all the entries.
- Trigger: the owner runs `python main.py total [--category CATEGORY]` or `python main.py list`.
- Main success path: the tool prints the total or the entries and exits with 0.
- Failure paths: a data file that is not a valid ledger.
- Observable result: the total or the entries on standard output, or an error on standard error.
- Source: the owner, confirmed.

## 4. Functional requirements

| ID | EARS requirement | Priority | Status | Business reason | Source | Scenarios | Examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LEDG-001 | When the owner runs `python main.py add AMOUNT CATEGORY [--note TEXT]`, the tool shall store one entry with a new ID (a UUID 4 string), the amount, the category, the note (empty when none) and the time of the entry (ISO 8601 in UTC, such as `2026-11-23T10:00:00Z`), print the ID and a newline to standard output, and exit with 0. | Must | Confirmed | Record each purchase | Owner | SCN-001 | EX-001, EX-004 |
| LEDG-002 | If the amount is not a number from 0.01 to 1000000.00 with at most two decimals, then the tool shall print `error: the amount must be a number from 0.01 to 1000000.00 with at most two decimals` and a newline to standard error, store nothing, and exit with 2. | Must | Confirmed | No wrong money in the ledger | Owner | SCN-001 | EX-002, EX-003, EX-004 |
| LEDG-003 | If the category is not 1 to 20 lowercase letters from a to z, then the tool shall print `error: the category must be 1 to 20 lowercase letters` and a newline to standard error, store nothing, and exit with 2. | Must | Confirmed | Categories that group well | Owner | SCN-001 | EX-005 |
| LEDG-004 | When the owner runs `python main.py total [--category CATEGORY]`, the tool shall print the sum of the amounts of the entries, of that category only when one is given, with two decimals and a newline, and exit with 0. The total of no entry is `0.00`. | Must | Confirmed | The money spent | Owner | SCN-002 | EX-006, EX-007 |
| LEDG-005 | When the owner runs `python main.py list`, the tool shall print one line for each entry, in the order of entry: the ID, the amount with two decimals, the category and the note, separated by tab characters, and exit with 0. | Must | Confirmed | Check the entries | Owner | SCN-002 | EX-008 |
| LEDG-006 | The tool shall keep the entries in the data file that the environment variable `LEDGER_DATA` names, by default `data/ledger.json` from the folder where it runs. A data file that does not exist is an empty ledger, and the tool makes its folder when it stores the first entry. | Must | Confirmed | One place for the data | Owner | SCN-001, SCN-002 | EX-009 |
| LEDG-007 | If the data file is not a valid ledger, then the tool shall print `error: the data file is not a valid ledger` and a newline to standard error, change nothing, and exit with 3. | Must | Confirmed | No silent loss of data | Owner | SCN-001, SCN-002 | EX-010 |

## 5. Non-functional requirements

| ID | EARS requirement | Priority | Status | Business reason | Source | Acceptance evidence |
| --- | --- | --- | --- | --- | --- | --- |

## 6. Acceptance examples

| ID | Requirement IDs | Situation and input | Expected result | Reviewed by |
| --- | --- | --- | --- | --- |
| EX-001 | LEDG-001 | An empty ledger. `add 12.50 food --note lunch` | Standard output is one UUID 4 and a newline, exit code 0. `list` then prints `<that ID>`, tab, `12.50`, tab, `food`, tab, `lunch` | Owner |
| EX-002 | LEDG-002 | `add 12.345 food` | The amount error on standard error, exit code 2, and the ledger is unchanged | Owner |
| EX-003 | LEDG-002 | `add 0 food` | The amount error on standard error, exit code 2 | Owner |
| EX-004 | LEDG-001, LEDG-002 | `add 1000000.00 food`, then `add 1000000.01 food` | The first is stored (exit code 0); the second gives the amount error, exit code 2 | Owner |
| EX-005 | LEDG-003 | `add 5 Food` | The category error on standard error, exit code 2, and nothing stored | Owner |
| EX-006 | LEDG-004 | Entries `12.50 food`, `7.25 food`, `3 bus`. `total`, then `total --category food` | `22.75`, then `19.75` | Owner |
| EX-007 | LEDG-004 | An empty ledger. `total` | `0.00`, exit code 0 | Owner |
| EX-008 | LEDG-005 | Entries `4.10 bus` (no note), then `2 food --note bread` | Two lines, in that order: `<ID 1>`, tab, `4.10`, tab, `bus`, tab, nothing; then `<ID 2>`, tab, `2.00`, tab, `food`, tab, `bread` | Owner |
| EX-009 | LEDG-006 | `LEDGER_DATA` names `new/ledger.json` in a folder where `new/` does not exist. `add 1 food` | Exit code 0; `new/ledger.json` exists and `total` prints `1.00` | Owner |
| EX-010 | LEDG-007 | The data file holds `not json`. `total` | The data-file error on standard error, exit code 3, and the data file is unchanged | Owner |

## 7. Assumptions and open questions

| Item | Evidence or assumption | Consequence if wrong | Owner | Resolution or revisit condition |
| --- | --- | --- | --- | --- |

## 8. Review and approval

Approved by the owner on November 23, 2026, in full.
