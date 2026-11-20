# Trello Board Setup — Site Yönetim Uygulaması

**Live Board URL:** https://trello.com/b/TJRYcEA2/site-y%C3%B6netim-uygulamas%C4%B1-agile-sprint-board

## What the reference board contains
https://trello.com/b/ZqN99gGN is Trello's public **"Agile Sprint Board" template**. I read it through its public JSON export. Its conventions:

- **Lists, left → right:** `Backlog` → `Sprint Backlog` → `In Progress` → `<date> Sprint – Complete` (one list per finished sprint, newest first).
- **Card title convention:** `(story points) Title`, for example `(5) EditableFieldView`.
- **First Backlog card** names the Product Owner, e.g. `Product Owner: Brian`.
- **Every completed sprint list starts with a `👍 Sprint Review 👎` card:** what went well, what didn't, and what changes next sprint.
- **Card descriptions** hold the plan or branch name. **Checklists** hold the sub-tasks.
- **Labels** mark status and type: Verified on branch / staging, Regression, Blocked, Bugs, Security Issue, Meta, Web.

Our board reuses this structure exactly, synchronized to our compressed 1-sprint MVP plan (20 Nov 2026) in [agile_project_documents.md](agile_project_documents.md).

---

## 1. Create the board
1. Open the template link → **Use template** (or **Copy board**) → name it **"Site Yönetim Uygulaması – Agile Sprint Board"**.
2. Delete the sample cards and the "Agile Development Template" info list.
3. Invite the 3 group members: **Ayhan Yakan (241805017)**, **Mustafa Ege Türker (241805034)**, **Nazife Kaya (241805082)**.

## 2. Lists (left → right)
| List | Purpose |
|---|---|
| `📌 Project Info` | Vision, MVP statement, Definition of Done, Themes & Epics, team roles (one card each) |
| `Product Backlog` | Post-MVP stories not in Sprint 1, ordered by rank (top = next) |
| `Sprint Backlog – S1 (20 Nov)` | Committed MVP Sprint 1 stories (65 pts) |
| `In Progress` | Being worked on (limit: 1 card per person) |
| `Review / Testing` | Done coding, waiting for review and automated/demo verification |
| `20.11.26 Sprint – Complete` | Created at Sprint 1 Review. Starts with a `👍 Sprint Review 👎` card. |

## 3. Labels
| Label | Color | Use |
|---|---|---|
| TH1 Site & Occupancy | green | Theme |
| TH2 Dues & Payments | yellow | Theme |
| TH3 Maintenance | orange | Theme |
| TH4 Communication | sky | Theme |
| TH5 Platform & Demo | purple | Theme |
| Must | red | MoSCoW |
| Should | blue | MoSCoW |
| Could | lime | MoSCoW |
| MVP | pink | Part of the demo version |
| Blocked | black | Same meaning as in the template |
| Bug | orange (dark) | Defects found in review |

**Epics:** make one card per epic in `📌 Project Info` (`EP1`–`EP10`, e.g. `EP4 Dues Charges`). Then use Trello's **Attach card / card link** to connect each story card to its epic.

## 4. Card template (every story)
```
Title:   (3) US13 Create dues charge
Labels:  TH2, Must, MVP
Desc:    As a manager, I want to create a monthly dues charge for a unit ...
         Trace: D06, BR01, BR09
         Acceptance criteria:
         - amount > 0
         - a second charge for the same unit+billingPeriod is rejected
         - the charge belongs to the unit, not a person
Checklist "Tasks":  (copy from the Tasks table, §4 of agile_project_documents.md)
Checklist "DoD":    AC pass · BR tests · server-side checks · reviewed · works on seed data
Members: assignee
Due:     20 Nov 2026
```

## 5. Initial board content

**📌 Project Info**
- `Product Owner: Ayhan Yakan (241805017)` *(confirm/swap on Trello if needed)*
- `Scrum Master: Mustafa Ege Türker (241805034)`
- `Developer: Nazife Kaya (241805082)` *(all 3 members contribute as Developers)*
- `Vision & MVP` (Python + Django + SQLite demo at `C:\Users\FEDYA\Desktop\SiteYonetim`)
- `Definition of Done`
- `TH1`–`TH5` (one card per theme)
- `EP1`–`EP10` (one card per epic)

**Sprint Backlog – S1 MVP Sprint (20 Nov 2026) — 65 pts (24 cards)**
- (5) EN01 Project skeleton & data model *(TH5, Must, MVP)*
- (3) US01 Manager login *(TH5, Must, MVP)*
- (2) US03 Register site *(TH1, Must, MVP)*
- (2) US04 Manage blocks *(TH1, Must, MVP)*
- (3) US05 Manage units *(TH1, Must, MVP)*
- (2) US07 Register person *(TH1, Must, MVP)*
- (5) US10 Record residency *(TH1, Must, MVP)*
- (2) US11 End residency *(TH1, Must, MVP)*
- (3) US06 Site overview & occupancy *(TH1, Must, MVP)*
- (3) US13 Create dues charge *(TH2, Must, MVP)*
- (3) US15 Unit charges with status *(TH2, Must, MVP)*
- (3) US02 Resident login, own-unit view *(TH5, Must, MVP)*
- (5) US16 Record confirmed payment *(TH2, Must, MVP)*
- (3) US17 Resident statement *(TH2, Must, MVP)*
- (3) US18 Overdue / debtors list *(TH2, Must, MVP)*
- (3) US20 Submit maintenance request *(TH3, Must, MVP)*
- (2) US21 View requests by status *(TH3, Must, MVP)*
- (2) US22 Update request status *(TH3, Must, MVP)*
- (1) US23 Track my requests *(TH3, Must, MVP)*
- (2) US24 Publish announcement *(TH4, Must, MVP)*
- (1) US25 Read announcements *(TH4, Must, MVP)*
- (2) US26 Fictional demo seed data *(TH5, Must, MVP)*
- (3) US08 Management assignment *(TH1, Should, MVP)*
- (2) US12 Unit residency history *(TH1, Should, MVP)*

**Product Backlog (post-MVP, in rank order — 12 pts, 4 cards)**
- (5) US14 Bulk-generate monthly charges *(TH2, Should)*
- (3) US27 Deploy demo *(TH5, Should)*
- (3) US19 Manager dashboard summary *(TH2, Could)*
- (1) US09 Edit person contact details *(TH1, Should)*

**`20.11.26 Sprint – Complete` (created at Sprint 1 Review)**
- First card: `👍 Sprint Review 👎`
  - **What went well:** Core 10-entity domain model, all 14 business rules (BR01–BR14), seeded PDF §6 demo dataset, role/IDOR protections, and automated test suite delivered in Sprint 1.
  - **What didn't / deferred:** Bulk charge generation (`US14`), cloud hosting (`US27`), period summary cards (`US19`), and person contact editing (`US09`) remained in `Product Backlog` due to the 1-day deadline.
  - **Next sprint focus:** Gather feedback from today's demo and pull top `Product Backlog` items (`US14`, `US27`) into Sprint 2.

## 6. Sprint workflow rules
1. **Sprint planning:** move the sprint's cards from `Product Backlog` → `Sprint Backlog`, and confirm total points fit capacity.
2. **During sprint:** drag cards `Sprint Backlog` → `In Progress` → `Review / Testing`. Add the `Blocked` label and a comment when stuck.
3. **Sprint review:** move finished cards into `<dd.mm.yy> Sprint – Complete` (for Sprint 1: `20.11.26 Sprint – Complete`) and put `👍 Sprint Review 👎` at the top of the list. Unfinished cards return to the top of `Product Backlog`.
4. **Velocity:** sum the `(n)` points in `20.11.26 Sprint – Complete` (65 pts) to calibrate Sprint 2.
