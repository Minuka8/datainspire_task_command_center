# DatAInspire Task Command Center

A centralized task management platform for the AI & Data Science Club — replacing WhatsApp messages, verbal instructions, and scattered documents with one organized system.

Built with **Python + Streamlit + SQLite**. No external database server, no complicated setup — just Python.

---

## What This System Does

- **President** creates tasks, assigns them to members or departments, sets deadlines and priority, reviews submitted work, and approves or sends it back for revision.
- **EXCO members** see their assigned tasks, update progress, upload files, comment, and submit work for review.
- Every action is timestamped and recorded — full audit trail, no more "I never got that message."
- Built-in dashboard, calendar, analytics, and performance tracking.

---

## 1. Installing the Application

### Step 1 — Install Python

You need **Python 3.10 or newer**. Check if you already have it:

```bash
python3 --version
```

If you don't have Python, download it from [python.org/downloads](https://www.python.org/downloads/) and install it. On Windows, make sure to check **"Add Python to PATH"** during installation.

### Step 2 — Get the project files

Unzip the project folder you received (`datainspire/`) anywhere on your computer — for example, your Desktop.

### Step 3 — Open a terminal in the project folder

- **Windows:** Open the `datainspire` folder, click the address bar, type `cmd`, and press Enter.
- **Mac:** Open Terminal, type `cd ` (with a space), then drag the `datainspire` folder into the Terminal window, and press Enter.

### Step 4 — Install the required packages

```bash
pip install -r requirements.txt
```

If `pip` doesn't work, try `pip3 install -r requirements.txt`.

That's it — installation is done.

---

## 2. Running the Application Locally

From inside the `datainspire` folder, run:

```bash
streamlit run Home.py
```

A browser tab will open automatically at `http://localhost:8501`. If it doesn't, copy that address into your browser manually.

To stop the app, go back to the terminal and press `Ctrl + C`.

---

## 3. Creating the Database & First Administrator Account

**You don't need to run any separate database setup command.** The first time you launch the app, it automatically:

1. Creates the SQLite database file at `data/db/datainspire.db`
2. Creates the database tables
3. Seeds the default departments (PR, Secretary, Treasury, Sergeant-at-Arms, Membership, Webmaster, Events, Project Committees)

The very first screen you see will ask you to **create the first President account** — this is your club's administrator login. Fill in:

- Full Name
- Username (this is what you'll log in with)
- Email (optional)
- Password (at least 8 characters, with at least one letter and one number)

After this account is created, the system switches to the normal login screen. From there, the President can log in and use **User Management** to create accounts for every other EXCO member.

> 🔐 **Tip:** Give each member their own login rather than sharing one account — this keeps the audit trail (who-did-what-when) accurate.

---

## 4. Day-to-Day Use — Quick Tour

| Page | What it's for |
|---|---|
| 🏠 **Dashboard** | Club-wide stats at a glance: active tasks, overdue tasks, tasks awaiting approval, department performance |
| ✅ **Tasks** | Create tasks (President), view/update/submit tasks (everyone), approve or return submissions (President) |
| 📅 **Calendar** | Monthly calendar, weekly timeline, and an overdue/upcoming deadline monitor |
| 📊 **Analytics** | Department and individual performance — completion rates, late submissions, average completion time |
| 👥 **User Management** *(President only)* | Create and manage member accounts, assign departments |
| 🏷️ **Departments** *(President only)* | Manage standing departments and create custom project groups (e.g. "Data Odyssey 2026 Committee") |
| ⚙️ **My Profile** | Change your password, view your account details |

### The task workflow

```
Not Started → In Progress → Submitted for Review → Approved ✓
                                    ↓
                          Returned for Revision → (back to In Progress)
```

EXCO members can move a task forward through their own steps. Only the **President** can approve a task or return it for revision — this is enforced by the system, not just a suggestion.

---

## 5. Resetting the Database (optional, for testing/demos only)

If you want to wipe everything and start fresh (e.g., after testing), run:

```bash
python3 reset_database.py
```

You'll be asked to type `RESET` to confirm. **This permanently deletes all users, tasks, and records** — only do this if you're sure. (It does not delete previously uploaded files on disk, only their database records.)

---

## 6. Deploying Online (so club members can access it from anywhere)

The easiest free option is **Streamlit Community Cloud**.

### Step 1 — Put the project on GitHub

1. Create a free account at [github.com](https://github.com) if you don't have one.
2. Create a new repository (e.g. `datainspire-task-center`).
3. Upload all the project files to it (everything in the `datainspire` folder, including `Home.py`, the `app/`, `pages/`, and `data/` folders, `requirements.txt`, and `.streamlit/config.toml`).

   > The `data/db/` and `data/uploads/` folders should be present but empty (the `.gitkeep` files inside them ensure Git keeps the empty folders) — the database will be created automatically on first launch.

### Step 2 — Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.
2. Click **"New app"**.
3. Select your repository, branch (`main`), and set the **main file path** to `Home.py`.
4. Click **Deploy**.

Within a minute or two, your app will be live at a public URL like:
`https://your-app-name.streamlit.app`

Share this link with all club members.

### ⚠️ Important note on cloud storage (SQLite + file uploads)

Streamlit Community Cloud's filesystem is **not permanent** — if the app restarts or redeploys, anything written to disk (including the SQLite database and uploaded files) can be lost. This is fine for testing and small-scale use, but for serious long-term use by the club, you have two options:

1. **Lightweight option:** Periodically download a backup of `data/db/datainspire.db` (there's no built-in download button for this yet, but you can add one, or access it via your hosting provider's file browser if using a VPS instead of Streamlit Cloud).
2. **Production option (recommended for long-term use):** Move to a host with persistent disk storage — a small VPS (e.g. DigitalOcean, Render, Railway with a persistent volume) running `streamlit run Home.py` works identically to local use, since SQLite just needs a real, persistent file path. The codebase doesn't need to change — only the deployment target.

The file storage code (`app/utils/file_storage.py`) is already written with a narrow, swappable interface so that migrating to cloud storage (e.g. AWS S3 or Google Cloud Storage) later requires changing only that one file, not the rest of the application.

---

## 7. Project Structure

```
datainspire/
├── Home.py                      # Entry point — login & first-run setup
├── requirements.txt
├── reset_database.py            # Optional: wipe & reseed the database
├── .streamlit/
│   └── config.toml              # Theme & server settings
├── app/
│   ├── database/
│   │   ├── schema.sql           # Full database schema
│   │   ├── db.py                # Connection helper
│   │   └── seed.py              # Default roles & departments
│   ├── services/
│   │   ├── auth_service.py      # Login, user creation, sessions
│   │   ├── task_service.py      # Task CRUD & workflow enforcement
│   │   ├── admin_service.py     # User & department management
│   │   └── analytics_service.py # Dashboard stats & performance tracking
│   ├── components/
│   │   ├── theme.py             # CSS / visual design system
│   │   ├── widgets.py           # Reusable UI components
│   │   ├── sidebar.py           # Navigation sidebar
│   │   └── page_init.py         # Shared page bootstrap
│   └── utils/
│       ├── security.py          # Password hashing (PBKDF2)
│       └── file_storage.py      # File upload handling
├── pages/
│   ├── 1_Dashboard.py
│   ├── 2_Tasks.py
│   ├── 3_Calendar.py
│   ├── 4_Analytics.py
│   ├── 5_User_Management.py
│   ├── 6_Departments.py
│   └── 7_My_Profile.py
└── data/
    ├── db/                      # SQLite database lives here
    └── uploads/                 # Uploaded files, organized per task
```

---

## 8. Database Design

Nine tables with proper foreign-key relationships:

- **roles** — President / EXCO
- **departments** — standing departments + custom task groups
- **users** — accounts, hashed passwords, role & department links
- **tasks** — full task record (title, priority, status, deadline, etc.)
- **task_status_history** — full audit trail of every status change
- **comments** — discussion thread per task
- **attachments** — uploaded file metadata per task
- **performance_records** — periodic performance snapshots (feeds future MERITRACK integration)
- **activity_log** — system-wide action log

---

## 9. Security Notes

- Passwords are never stored in plain text — they're hashed using PBKDF2-HMAC-SHA256 with a unique random salt per user (260,000 iterations).
- Role permissions are enforced at the service layer (not just hidden in the UI), so an EXCO member cannot approve their own task even by crafting a direct request.
- Session state resets on logout; there is no "remember me" token stored on disk.

---

## 10. Future Scalability (already designed for)

- **MERITRACK integration:** the `performance_records` table and `analytics_service.snapshot_performance_records()` function are designed as the bridge to a future, more sophisticated club-wide evaluation system.
- **Cloud file storage:** `file_storage.py` has a narrow save/read interface, ready to be backed by S3/GCS instead of local disk.
- **Additional roles:** the `roles` table isn't hardcoded to just two — new roles can be added without schema changes (permission logic would need extending in the service layer).
- **More departments:** Presidents can create unlimited custom task groups for one-off projects/committees without touching code.

---

## Support

This is a self-contained system — there's no external service to "go down." If something looks wrong, the most common fixes are:

1. **App won't start:** make sure you ran `pip install -r requirements.txt` inside the project folder.
2. **"Module not found" error:** make sure you're running `streamlit run Home.py` from *inside* the `datainspire` folder, not from somewhere else.
3. **Forgot the President password:** another President account can reset it via... actually, for the very first account, you'd need to either ask another President to create you a new account, or use `reset_database.py` to start over (this wipes all data, so only do this if necessary).
