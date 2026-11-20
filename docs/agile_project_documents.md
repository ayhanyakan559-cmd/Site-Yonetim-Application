# Site Yönetim Uygulaması — Agile Project Documents

**Project:** Residential Complex Management (Site Yönetim Uygulaması)
**Course:** Object Oriented Analysis and Design — group assignment
**Group members:** Ayhan Yakan (241805017) · Mustafa Ege Türker (241805034) · Nazife Kaya (241805082)
**Process model chosen:** Agile (Scrum, tracked on Trello)
**Source of truth:** *Problem domain description and conceptual UML model* (paragraphs D01–D09, Section 3 business rules, Section 6 fictional example)

### Submission Links *(fill in once published)*

| Resource | URL |
|---|---|
| Trello Sprint Board | `<paste public Trello board URL>` |
| GitHub Repository | `<paste GitHub repo URL>` |
| Live Demo URL | `<paste Render / PythonAnywhere URL>` |

> [!NOTE]
> **Why Agile and not Unified Process:** the team wants a working **demo version first** and wants to refine it from feedback. The domain is small (10 concepts, 13 associations), with three people and a short timeline. Short sprints that each end in a working increment fit this better than UP's phase-based documents. Every user story below traces back to a domain paragraph (Dxx) or business rule (BRxx), so the analysis work from the PDF is kept.

---

## 0. Assumptions (confirm or change)

| # | Assumption |
|---|---|
| A1 | Team = 3 group members: **Ayhan Yakan**, **Mustafa Ege Türker**, **Nazife Kaya**. Suggested Scrum roles (confirm or swap): **Product Owner** (Ayhan Yakan), **Scrum Master** (Mustafa Ege Türker), **Developers** (all 3, including Nazife Kaya). |
| A2 | **Deadline is today, 20 Nov 2026.** The plan is compressed into **one MVP sprint (Sprint 1, 20 Nov 2026)** that delivers every Must story. Should and Could stories stay in the Product Backlog for later sprints. |
| A3 | Sprint 1 commitment = 60 Must points. The team works on it together at the same time. |
| A4 | Technology stack: **Python 3 + Django + SQLite**, server-rendered HTML, UI in English. Code lives in `C:\Users\FEDYA\Desktop\SiteYonetim`. |
| A5 | One residential site per installation in the demo. The model supports more, but the demo UI targets one. |
| A6 | Scope exclusions are taken directly from the PDF §1: ownership, legal debt liability, common-area maintenance, suppliers, payroll, voting, reservations, banking integration, refunds, late-payment interest, money transfer. Currency is always TRY. |

### Business rules referenced below

| ID | Rule (PDF §3 and D-paragraphs) |
|---|---|
| BR01 | Charge and payment amounts must be positive. |
| BR02 | A payment cannot exceed the charge's current outstanding amount. |
| BR03 | `outstandingAmount = amount − Σ payments`. It is derived and never entered by hand. |
| BR04 | Outstanding = 0 → **Settled**. Outstanding > 0 after the due date → **Overdue**. |
| BR05 | An end date cannot be earlier than its start date. |
| BR06 | No duplicate overlapping Residency records for the same Person + Unit. |
| BR07 | History is kept after a Residency or ManagementAssignment ends. Residency and manager roles are independent. |
| BR08 | `blockLabel` is unique within a site. `unitNumber` is unique within a block. (D01, D02) |
| BR09 | A unit has at most one DuesCharge per billingPeriod. (D06) |
| BR10 | A maintenance request may only be submitted by a Person with an active Residency in that Unit. (D08) |
| BR11 | Request status ∈ {Open, In Progress, Resolved} and is updated only by the site's active manager. (D08) |
| BR12 | Announcements are authored only by a Person with an active ManagementAssignment for the site. (D09) |
| BR13 | A site under management has exactly one active ManagementAssignment at a time. (D05) |
| BR14 | Each payment covers exactly one charge. Multi-charge amounts are split into separate payments. (D07) |

---

## 1. Themes

Themes are the large value areas of the product.

| ID | Theme | Value delivered | Domain coverage |
|---|---|---|---|
| **TH1** | Site Structure & Occupancy | One reliable register of the site, its blocks, units, people and who lives where | D01–D05 |
| **TH2** | Dues & Financial Transparency | The manager knows who owes what. Residents see their charges and payments. | D06, D07, BR01–BR04, BR09, BR14 |
| **TH3** | Maintenance Operations | In-unit problems are reported and followed to resolution | D08, BR10, BR11 |
| **TH4** | Site Communication | Announcements reach all current residents | D09, BR12 |
| **TH5** | Platform & Demo Readiness | Secure role-based access, seed data, deployable demo | Cross-cutting |

## 2. Epics

| ID | Epic | Theme | Stories |
|---|---|---|---|
| EP1 | Site, Block & Unit Registry | TH1 | US03, US04, US05, US06 |
| EP2 | People & Management Roles | TH1 | US07, US08, US09 |
| EP3 | Residency History | TH1 | US10, US11, US12 |
| EP4 | Dues Charges | TH2 | US13, US14, US15 |
| EP5 | Payment Recording & Resident Statement | TH2 | US16, US17 |
| EP6 | Debt Tracking & Reporting | TH2 | US18, US19 |
| EP7 | Maintenance Requests | TH3 | US20, US21, US22, US23 |
| EP8 | Announcements | TH4 | US24, US25 |
| EP9 | Authentication & Role-Based Access | TH5 | US01, US02 |
| EP10 | Demo Readiness | TH5 | EN01, US26, US27 |

---

## 3. User Stories

Format: *As a <role>, I want <goal>, so that <benefit>.* Points use Fibonacci. Priority uses MoSCoW (M = Must, S = Should, C = Could).

### EP9 — Authentication & Role-Based Access

**US01 — Manager login** · 3 pts · M · Trace: D03, D05
As a **manager**, I want to log in with my credentials, so that only authorised people can change site records.
- Given valid manager credentials, when I log in, then I see the manager dashboard.
- Given invalid credentials, then access is denied with a generic error.
- Manager-only pages and actions reject non-manager users.

**US02 — Resident login with own-unit view** · 3 pts · M · Trace: D03, D04
As a **resident**, I want to log in and see only information for the unit(s) I actively reside in, so that my data is private and relevant.
- A resident sees only units where they have an active Residency.
- A resident cannot open another unit's charges, payments or requests, even by changing the URL or ID.
- A person who is both resident and manager can use both roles (D03).

### EP1 — Site, Block & Unit Registry

**US03 — Register site** · 2 pts · M · Trace: D01
As a **manager**, I want to record the site's name and address, so that all records belong to a known complex.
- `siteName` and `address` are required.

**US04 — Manage blocks** · 2 pts · M · Trace: D01, BR08
As a **manager**, I want to add blocks (e.g. A, B, C) to the site, so that units can be organised.
- A block belongs to exactly one site.
- A duplicate `blockLabel` in the same site is rejected.

**US05 — Manage units** · 3 pts · M · Trace: D02, BR08
As a **manager**, I want to add units with a unit number and floor to a block, so that every apartment is registered, including vacant ones.
- A unit belongs to exactly one block.
- A duplicate `unitNumber` in the same block is rejected.
- A unit with no residents is kept and shown as **Vacant**.

**US06 — Site overview & occupancy** · 3 pts · M · Trace: D02, D04
As a **manager**, I want a site overview of blocks → units with Occupied/Vacant status and current residents, so that I understand the complex at a glance.
- Occupied = at least one active Residency today. Otherwise Vacant.
- Clicking a unit opens its detail page (residents, charges, requests).

### EP2 — People & Management Roles

**US07 — Register person** · 2 pts · M · Trace: D03
As a **manager**, I want to register a person with full name, telephone and email, so that I can link them to residencies, payments and requests.
- `fullName` is required. Email format is validated.
- Contact details belong to the person, not to a unit.

**US08 — Management assignment** · 3 pts · S · Trace: D05, BR05, BR07, BR13
As a **manager**, I want to record who manages the site and from when, so that the system knows the active manager and keeps past managers.
- The assignment has a startDate and an optional endDate, and endDate ≥ startDate.
- Creating a new active assignment requires ending the previous one. Only one is active at a time.
- Past assignments stay visible in history.

**US09 — Edit person contact details** · 1 pt · S · Trace: D03
As a **manager**, I want to update a person's phone and email, so that contact data stays correct.

### EP3 — Residency History

**US10 — Record residency** · 5 pts · M · Trace: D04, BR05, BR06
As a **manager**, I want to record that a person lives in a unit from a start date, so that I know who lives where.
- Several people may live in the same unit at the same time.
- endDate (optional) ≥ startDate.
- An overlapping residency for the same Person + Unit is rejected.
- "Active" = startDate ≤ today and (no endDate or endDate ≥ today).

**US11 — End residency (move-out)** · 2 pts · M · Trace: D04, BR07
As a **manager**, I want to set an end date when a resident moves out, so that occupancy is current but history is kept.
- After move-out, the unit's charges, payments and requests remain unchanged.
- A new resident gets a separate Residency record.

**US12 — Unit residency history** · 2 pts · S · Trace: D04, BR07
As a **manager**, I want to see all past and current residents of a unit, so that I can explain earlier records.

### EP4 — Dues Charges

**US13 — Create dues charge** · 3 pts · M · Trace: D06, BR01, BR09
As a **manager**, I want to create a monthly dues charge for a unit (billing period, amount in TRY, due date), so that what each apartment owes is recorded.
- amount > 0.
- A second charge for the same unit and billingPeriod is rejected.
- The charge belongs to the unit, not to a person (it survives resident changes).

**US14 — Bulk-generate monthly charges** · 5 pts · S · Trace: D06, BR09
As a **manager**, I want to generate the same charge for all units for a billing period in one action, so that monthly billing is fast.
- Units that already have a charge for that period are skipped and reported.
- Vacant units are included by default (accounting attaches to the unit, D06). The manager can untick them.

**US15 — Unit charges with status** · 3 pts · M · Trace: D06, D07, BR03, BR04
As a **manager**, I want to see a unit's charges with paid-so-far, outstanding and status, so that I know its balance.
- Status is one of: **Unpaid**, **Partially paid**, **Settled** (outstanding = 0), **Overdue** (outstanding > 0 and today > dueDate).
- Outstanding is always calculated and never stored as user input.

### EP5 — Payment Recording & Resident Statement

**US16 — Record confirmed payment** · 5 pts · M · Trace: D07, BR01, BR02, BR03, BR14
As a **manager**, I want to record a confirmed payment (payer, charge, date, amount, method, reference number), so that the charge's balance is updated.
- amount > 0 and amount ≤ the current outstanding amount. Overpayment is rejected with a clear message.
- Each payment links to exactly one charge and one paying person.
- Several partial payments can settle one charge (example: 400 + 600 = 1,000 → Settled).
- The system never moves money. It only records confirmed payments.

**US17 — Resident statement** · 3 pts · M · Trace: D06, D07
As a **resident**, I want to see my unit's charges, recorded payments and outstanding balance, so that I know exactly what I owe.

### EP6 — Debt Tracking & Reporting

**US18 — Overdue / debtors list** · 3 pts · M · Trace: BR04, PDF §5 benefits
As a **manager**, I want a list of units with overdue charges and their total outstanding amount, so that I can follow up unpaid dues.
- Can be filtered by block and billing period.
- Sorted by outstanding amount, largest first.

**US19 — Manager dashboard summary** · 3 pts · C
As a **manager**, I want totals for charged, collected and outstanding amounts this period, plus the number of open requests, so that I see the site's health quickly.

### EP7 — Maintenance Requests

**US20 — Submit maintenance request** · 3 pts · M · Trace: D08, BR10
As a **resident**, I want to report a problem in my unit with a subject and description, so that the manager can fix it.
- Allowed only if I have an active Residency in that unit on the submission date.
- submissionDate is set automatically. The initial status is **Open**.

**US21 — View requests by status** · 2 pts · M · Trace: D08
As a **manager**, I want to list all requests and filter them by status and block, so that nothing unresolved is forgotten.

**US22 — Update request status** · 2 pts · M · Trace: D08, BR11
As the **active manager**, I want to move a request Open → In Progress → Resolved, so that residents see progress.
- Only the site's active manager can change status.
- Only the three permitted statuses exist.

**US23 — Track my requests** · 1 pt · M · Trace: D08
As a **resident**, I want to see my requests and their current status, so that I know what is happening.
- A request stays visible in the manager's records after the resident moves out.

### EP8 — Announcements

**US24 — Publish announcement** · 2 pts · M · Trace: D09, BR12
As the **active manager**, I want to publish an announcement (title, message) to the site, so that all current residents are informed.
- Only a person with an active ManagementAssignment can publish. publicationDate is set automatically.

**US25 — Read announcements** · 1 pt · M · Trace: D09
As a **resident**, I want to read site announcements, newest first, so that I stay informed.
- Visible to all current residents of the site. There is no per-recipient delivery tracking (out of scope).

### EP10 — Demo Readiness

**EN01 — Technical enabler: project skeleton & data model** · 5 pts · M · Trace: §4 UML model
As the **team**, we need the project skeleton, database schema for the 10 domain classes, and a test setup, so that features can be built on a stable base.

**US26 — Fictional demo seed data** · 2 pts · M · Trace: PDF §6
As the **team**, we want the fictional example loaded (Example Residential Complex in Aydın, blocks A/B/C × 20 units, Ayşe Kaya in A-12, manager Deniz Aras, Nov 2026 charge TRY 1,000, payments P001 TRY 400 and P002 TRY 600, leaking-tap request, Water Maintenance announcement), so that the demo shows realistic behaviour.

**US27 — Deploy demo** · 3 pts · S
As the **team**, we want the demo running at a shareable URL or as a one-command local run, so that the instructor can try it.

---

## 4. Tasks (per story)

| Story | Tasks |
|---|---|
| EN01 | Pick stack and repo structure · Create DB schema/migrations for ResidentialSite, Block, Unit, Person, Residency, ManagementAssignment, DuesCharge, Payment, MaintenanceRequest, Announcement · Add uniqueness constraints (BR08, BR09) · Set up test runner and linter · README with run instructions |
| US01 | Auth model linked to Person · Login/logout endpoint and page · Session/token handling · Manager role guard middleware · Tests for denied access |
| US02 | Resident role guard · "Active residency" query helper (reused by US10, US20) · Ownership check on every unit-scoped endpoint · IDOR negative tests |
| US03 | Site form + endpoint · Validation · Test |
| US04 | Block CRUD endpoint/UI · Unique-label validation · Test duplicate rejection |
| US05 | Unit CRUD endpoint/UI · Unique number-per-block validation · Vacant display · Tests |
| US06 | Overview query (blocks → units → active residents) · Occupancy calculation · Overview page · Unit detail page shell |
| US07 | Person CRUD endpoint/UI · Email validation · Test |
| US08 | Assignment endpoint/UI · Single-active-assignment validation (BR13) · Date validation (BR05) · History view · Tests |
| US09 | Edit form · Endpoint · Test |
| US10 | Residency endpoint/UI · Date validation (BR05) · Overlap check (BR06) · Active-residency helper · Boundary-date tests |
| US11 | "End residency" action · Verify related records untouched · Test |
| US12 | History list on unit detail page |
| US13 | Charge endpoint/UI · Positive-amount check (BR01) · One-per-period check (BR09) · Tests |
| US14 | Bulk-generation endpoint · Skip/report existing charges · Confirmation UI · Tests |
| US15 | Derived outstanding calculation (BR03) · Status calculation (BR04) · Charge table on unit page · Date-boundary tests |
| US16 | Payment endpoint/UI · Overpayment guard (BR02) inside a transaction · Positive check · Partial-payment test (400 + 600) · Overpayment-rejection test |
| US17 | Resident statement page · Ownership-scoped query · Test |
| US18 | Overdue query · Filters · Debtors page · Tests |
| US19 | Aggregate queries · Dashboard cards |
| US20 | Request form/endpoint · Active-residency check (BR10) · Default status Open · Tests |
| US21 | Request list + filters for manager |
| US22 | Status transition endpoint · Active-manager check (BR11) · Allowed-status validation · Tests |
| US23 | "My requests" page for residents |
| US24 | Announcement form/endpoint · Active-manager check (BR12) · Test |
| US25 | Announcement feed page (newest first) |
| US26 | Seed script built from PDF §6 · Demo login accounts (manager Deniz, resident Ayşe) · Reset-demo command |
| US27 | Hosting/run configuration · Smoke-test the deployed demo · Share the link/instructions |

---

## 5. Product Backlog (ordered)

| Rank | ID | Title | Epic | Pts | MoSCoW | Sprint |
|---|---|---|---|---|---|---|
| 1 | EN01 | Project skeleton & data model | EP10 | 5 | M | S1 |
| 2 | US01 | Manager login | EP9 | 3 | M | S1 |
| 3 | US03 | Register site | EP1 | 2 | M | S1 |
| 4 | US04 | Manage blocks | EP1 | 2 | M | S1 |
| 5 | US05 | Manage units | EP1 | 3 | M | S1 |
| 6 | US07 | Register person | EP2 | 2 | M | S1 |
| 7 | US10 | Record residency | EP3 | 5 | M | S1 |
| 8 | US11 | End residency | EP3 | 2 | M | S1 |
| 9 | US06 | Site overview & occupancy | EP1 | 3 | M | S1 |
| 10 | US13 | Create dues charge | EP4 | 3 | M | S1 |
| 11 | US15 | Unit charges with status | EP4 | 3 | M | S1 |
| 12 | US02 | Resident login, own-unit view | EP9 | 3 | M | S1 |
| 13 | US16 | Record confirmed payment | EP5 | 5 | M | S1 |
| 14 | US17 | Resident statement | EP5 | 3 | M | S1 |
| 15 | US18 | Overdue / debtors list | EP6 | 3 | M | S1 |
| 16 | US20 | Submit maintenance request | EP7 | 3 | M | S1 |
| 17 | US21 | View requests by status | EP7 | 2 | M | S1 |
| 18 | US22 | Update request status | EP7 | 2 | M | S1 |
| 19 | US23 | Track my requests | EP7 | 1 | M | S1 |
| 20 | US24 | Publish announcement | EP8 | 2 | M | S1 |
| 21 | US25 | Read announcements | EP8 | 1 | M | S1 |
| 22 | US26 | Fictional demo seed data | EP10 | 2 | M | S1 |
| 23 | US08 | Management assignment | EP2 | 3 | S | S1 |
| 24 | US14 | Bulk-generate monthly charges | EP4 | 5 | S | Backlog |
| 25 | US12 | Unit residency history | EP3 | 2 | S | S1 |
| 26 | US27 | Deploy demo | EP10 | 3 | S | Backlog |
| 27 | US19 | Manager dashboard summary | EP6 | 3 | C | Backlog |
| 28 | US09 | Edit person contact details | EP2 | 1 | S | Backlog |

**Total: 77 pts** — Must 60 · Should 14 · Could 3.

---

## 6. Sprint Planning

**Cadence (compressed, deadline today):** Sprint Planning (30 min) → build with short check-ins every ~2 h (stand-up substitute) → Sprint Review (demo the MVP) + Retrospective, written up as a "👍 Sprint Review 👎" card on Trello, the same way the template does it.

| Sprint | Date | Sprint Goal | Stories | Pts |
|---|---|---|---|---|
| **S1 – MVP Sprint** | 20 Nov 2026 | "Deliver a working demo where a manager runs the complex's structure, residents, dues, payments, maintenance and announcements, and a resident sees their own unit's data." | EN01, US01–US07, US08, US10–US13, US15–US18, US20–US26 | 65 |
| Later sprints | after the demo | Feedback-driven improvements | US14, US27, US19, US09 + review findings | 12 + |

- **Scope-cut order if time runs out:** US12 → US08 (its rule is still enforced through seeded assignments). Must stories are never dropped silently.
- **Risk:** a single sprint has no buffer. Mitigation: the build order follows the backlog rank, so a working subset exists at every point.

---

## 7. PSI — Potentially Shippable Increment

The sprint ends in a working, tested increment that can be demonstrated on its own. Build order gives intermediate PSIs within the day:

| Checkpoint | PSI (what can be demonstrated) |
|---|---|
| PSI-1 | Manager logs in → sees site, blocks A/B/C, units, people. Duplicate block/unit is rejected. |
| PSI-2 | Residencies (with history and move-out), Occupied/Vacant overview, dues charges with status. Resident sees only their unit. |
| PSI-3 | P001 (400) → Partially paid, P002 (600) → Settled, overpayment rejected. Overdue list. Maintenance request Open → In Progress → Resolved. |
| **PSI-4 = MVP release** | Announcements live, PDF §6 data seeded, active-manager rule enforced, automated tests pass. |

### Definition of Done (applies to every story)
1. All acceptance criteria pass.
2. Business rules in the story have automated tests, including rejection cases.
3. Role/ownership checks are enforced server-side, not just hidden in the UI.
4. Code reviewed by one other team member and merged.
5. Works on the seeded demo data.
6. Trello card has its checklist complete and is moved to `<dd.mm.yy> Sprint – Complete` (for Sprint 1: `20.11.26 Sprint – Complete`).

---

## 8. MVP — Demo Version

**MVP statement:** the minimum product that shows the system solves the PDF's core problem, which is records scattered across notebooks, spreadsheets and chat groups. With the MVP, a manager can see unpaid dues and unresolved requests in one place, and a resident can see their charges, payments and announcements.

**In MVP (Sprint 1):** all **Must** stories (EN01, US01–US07, US10, US11, US13, US15–US18, US20–US26) plus US08 and US12.
**Backlog after demo:** US14, US27, US19, US09, plus everything listed as out of scope in assumption A6.

### MVP demo script (≈ 5 min, uses the PDF §6 data)
1. Log in as **Deniz Aras** (`deniz`, manager) → site overview: Example Residential Complex, 3 blocks × 20 units, previous manager Canan Öztürk in history.
2. Open **A-12** (floor 3) → Ayşe Kaya is the active resident since 1 Sep 2026, with Kemal Aydın in history.
3. Inspect the seeded **November 2026** charge (`TRY 1,000`, settled via `P001 TRY 400` + `P002 TRY 600`), then open the **December 2026** charge (`TRY 1,000`, due 10 Dec) → record `TRY 400` → Partially paid, outstanding `TRY 600`.
4. Try to record `TRY 700` on December 2026 → **rejected (overpayment)**. Record `TRY 600` → **Settled**.
5. Open **Overdue dues** → shows `B-05` (`TRY 1,000`) and `C-03` (`TRY 700`, after partial payment `P003`), sorted largest first.
6. Log in as **Ayşe** (`ayse`) → statement for A-12, Water Maintenance announcement (2 Nov), submit a new maintenance request (or inspect her seeded "Leaking tap" request).
7. Back to **Deniz** → move "Leaking tap" `Open → In Progress → Resolved`.
8. End Ayşe's residency with end date `2026-11-19` (yesterday, so A-12 immediately becomes **Vacant** today under D04) → the charges, payments and request all remain in A-12's history.

**MVP success criteria:** every step above works with no manual database edits, and every business rule BR01–BR14 has at least one passing test.

---

## 9. Decisions

| # | Decision | Status |
|---|---|---|
| OD1 | Technology stack | **Decided:** Python + Django + SQLite, English UI |
| OD2 | Real member names and roles | **Populated from PDF p. 1:** Ayhan Yakan (PO), Mustafa Ege Türker (SM), Nazife Kaya (Developer); confirm/adjust PO/SM assignments on Trello if desired |
| OD3 | Sprint length | **Decided:** one compressed MVP sprint on 20 Nov 2026 (deadline) |
| OD4 | Demo delivery | **Decided for now:** local run (`runserver`). Hosting = US27, backlog |
