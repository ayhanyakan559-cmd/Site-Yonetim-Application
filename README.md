# Site Yönetim Uygulaması — Residential Complex Management (MVP Demo)

**Course:** Object Oriented Analysis and Design — Group Assignment  
**Group Members:** Ayhan Yakan (241805017) · Mustafa Ege Türker (241805034) · Nazife Kaya (241805082)  
**Stack:** Python 3.14 + Django 6.0 + SQLite  

This MVP web application implements the 10-entity conceptual UML domain model and business rules (`BR01`–`BR14`) from the *Residential Complex Management* specification (`D01`–`D09`, Section 3, and Section 6 fictional worked example).

---

## Quick Start

From `C:\Users\FEDYA\Desktop\SiteYonetim` (PowerShell):

```powershell
# 1. Activate the local virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Apply migrations (already applied if using the existing db.sqlite3)
python manage.py migrate

# 3. Load (or reset) the fictional PDF §6 demo data
python manage.py seed_demo --reset

# 4. Run the development server
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

---

## Free Hosting Deployment

### Option A — Render (recommended 3-click Blueprint using `render.yaml`)
1. Push this project folder to a GitHub repository.
2. On Render, click **New → Blueprint**, select the repository, and apply [`render.yaml`](render.yaml).
3. Render automatically installs dependencies, runs migrations, seeds the PDF §6 demo data, and gives you a permanent free URL (`https://<name>.onrender.com`). Free instances sleep after 15 min idle (~30–50s wake-up) and re-seed clean demo data on each wake.

### Option B — PythonAnywhere (persistent SQLite, no sleep)
1. Clone your GitHub repository on PythonAnywhere, create a virtualenv (`pip install -r requirements.txt`), and run:
   ```bash
   python manage.py migrate
   python manage.py seed_demo
   python manage.py collectstatic --noinput
   ```
2. In the **Web** tab, point WSGI to `config.wsgi`, set `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY=<random>`, and `DJANGO_ALLOWED_HOSTS=<username>.pythonanywhere.com`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://<username>.pythonanywhere.com`.
3. Click **Reload** to publish `https://<username>.pythonanywhere.com`.

---

## Demo Accounts

All seeded demo accounts use password **`demo-pass-2026`**:

| Username | Person | Role | Notes |
|---|---|---|---|
| `deniz` | Deniz Aras | **Active Manager** | Manages *Example Residential Complex* from 1 Jan 2026 |
| `ayse` | Ayşe Kaya | **Active Resident** | Lives in **A-12** (floor 3) from 1 Sep 2026 |
| `mehmet` | Mehmet Demir | **Active Resident** | Lives in **B-05** (overdue `TRY 1,000` charge) |
| `selin` | Selin Yılmaz | **Active Resident** | Lives in **C-03** (overdue `TRY 700` balance after `P003`) |
| `kemal` | Kemal Aydın | Former Resident | Resided in A-12 (`2025-01-01` – `2026-08-31`) — history only |
| `canan` | Canan Öztürk | Former Manager | Managed site (`2025-01-01` – `2025-12-31`) — history only |

---

## Useful Commands

```powershell
# Reset the database to the clean fictional PDF §6 dataset
.\.venv\Scripts\python.exe manage.py seed_demo --reset

# Run automated tests (business rules BR01-BR14, access control / IDOR, workflows, seed data)
.\.venv\Scripts\python.exe manage.py test -v 2

# Django system checks
.\.venv\Scripts\python.exe manage.py check
```

---

## 5-Minute MVP Demo Script

1. **Manager overview (`deniz`):** Log in as `deniz`. Show *Example Residential Complex* (`A`, `B`, `C` × 20 units = 60 units). Check **Managers** to show former manager *Canan Öztürk* retained in history (`D05`, `BR13`).
2. **Unit A-12 (`D02`, `D04`):** Open **A-12** (floor 3). Show active resident *Ayşe Kaya* (since 1 Sep 2026) and former resident *Kemal Aydın* in history.
3. **Partial payments & derived balance (`D06`, `D07`, `BR03`, `BR04`):** Inspect the seeded **November 2026** charge (`TRY 1,000`, settled by `P001 TRY 400` + `P002 TRY 600`). Then click **Record payment** on the **December 2026** charge (`TRY 1,000`, due 10 Dec) and record `TRY 400` → status becomes **Partially paid**, outstanding `TRY 600`.
4. **Overpayment guard (`BR01`, `BR02`):** Attempt to record `TRY 700` on December 2026 → rejected with an overpayment validation error. Record `TRY 600` → charge becomes **Settled** (`TRY 0.00` outstanding).
5. **Overdue dues list (`BR04`):** Open **Overdue dues** → shows **B-05** (`TRY 1,000`) above **C-03** (`TRY 700`), filterable by block and period.
6. **Resident portal & privacy (`US02`, `D08`, `D09`):** Log out and log in as `ayse`. Show her apartment statement (only `A-12`, not other units), the *Water Maintenance* announcement (2 Nov), and submit a new maintenance request (or review her seeded *Leaking tap* request).
7. **Request lifecycle (`D08`, `BR11`):** Log back in as `deniz`, open **Maintenance**, and advance *Leaking tap* from `Open` → `In Progress` → `Resolved`.
8. **History retention on move-out (`D04`, `BR07`):** Open **A-12** → **Move out** on Ayşe Kaya with end date `2026-11-19` (yesterday, so the unit immediately becomes **Vacant** today). Confirm all charges, payments, and maintenance requests remain in `A-12`'s records.

---

## Project Documents

- [docs/agile_project_documents.md](docs/agile_project_documents.md) — Themes, Epics, User Stories, Acceptance Criteria, Tasks, Product Backlog, Sprint Plan, PSI, Definition of Done, MVP
- [docs/trello_board_setup.md](docs/trello_board_setup.md) — Trello sprint board configuration aligned with the reference Agile Sprint Board template
