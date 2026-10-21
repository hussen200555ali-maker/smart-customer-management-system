# Smart Customer Management System (MySQL v4.0)

A desktop **customer & service management** system built with **Python (OOP / MVC + Repository pattern)**, **MySQL**, and **CustomTkinter** — with full Arabic RTL support and AI-powered demand forecasting.

## Features

- **Customers**: full CRUD, search by name/phone/email
- **Services & Categories**: CRUD with soft delete (`is_active` flag)
- **Orders / Sales**: multi-item orders, status workflow (pending → in_progress → completed / cancelled), automatic total recalculation
- **Invoices**: preview, print, and **PDF export** with reshaped Arabic text (reportlab + bidi + Cairo fonts)
- **Statistics Dashboard**: KPIs, monthly revenue, top customers/services, hand-drawn charts, date filtering
- **Import / Export**: Excel & CSV with Arabic templates
- **Backup**: automatic/manual backup & restore via `mysqldump` with programmatic fallback
- **Security**: PBKDF2 + salt password hashing, role-based access control (admin / employee / viewer), account lockout with exponential backoff, activity log
- **AI**: demand & revenue forecasting (LinearRegression, RandomForest, GradientBoosting, XGBoost, LightGBM, Prophet, Ensemble/Stacking), customer segmentation, service recommendations
- **UI**: CustomTkinter, full RTL Arabic interface (arabic_reshaper + python-bidi + Cairo fonts), dark mode, async loading (no UI freezing)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3 (OOP — ~97 classes, dataclasses models) |
| GUI | CustomTkinter |
| Database | MySQL (7 tables, ~24 indexes) |
| Architecture | MVC + Repository pattern |
| AI/ML | scikit-learn, XGBoost, LightGBM, Prophet |
| PDF | reportlab |
| Import/Export | pandas, openpyxl |

## Database Schema (7 tables)

`users`, `customers`, `service_categories`, `services`, `orders`, `order_details`, `activity_log`

## Quick Start

```bash
# 1. Start MySQL (XAMPP) and create the database
C:\xampp\mysql\bin\mysql -u root < init_db.sql

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

### Configure the database connection

Connection settings live in **`config.py`** — edit these before running if your
MySQL setup differs from the XAMPP default:

```python
DB_HOST = "localhost"        # MySQL host
DB_PORT = 3306               # MySQL port
DB_NAME = "service_management"
DB_USER = "root"
DB_PASSWORD = ""             # empty by default in XAMPP
```

Alternatively, you can override them via environment variables
(`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`) without touching the code.

**Default login:** `admin` / `admin123`

## Migrate from SQLite

```bash
python migrate_to_mysql.py path/to/old_database.db
```

## Project Structure

```
service_management_mysql/
├── main.py                # Entry point
├── config.py              # MySQL & system settings
├── init_db.sql            # Database schema script
├── requirements.txt
├── repositories/          # Data access layer (DatabaseManager)
├── models/                # Dataclass models
├── services/              # Business logic
├── controllers/           # Controllers (Auth, Customer, Order...)
├── ui/                    # CustomTkinter screens (RTL)
├── ai/                    # Prediction models & metrics
├── utils/                 # Invoice PDF, encryption, dialogs
├── exceptions/            # Custom exceptions
└── templates/             # Import/export CSV templates
```

## License

MIT — see [LICENSE](LICENSE).

---

**Version**: 4.0
