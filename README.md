# Nova Management Solutions

**Stack:** FastAPI · Pandas · SciPy · scikit-learn · React 18 · Recharts · Vite

---

## Project Structure

```
Novams_project/
├── data/
│   └── zepto_sales_dataset.csv        ← Your dataset (external, decoupled)
│
├── backend/
│   ├── main.py                        ← FastAPI server (all analytics endpoints)
│   └── requirements.txt
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx                   ← React entry point
        ├── App.jsx                    ← Full dashboard UI
        ├── utils/
        │   └── api.js                 ← Centralised fetch client
        ├── hooks/
        │   └── useDashboard.js        ← Custom data-fetching hook
        └── components/
            ├── KPICard.jsx            ← Reusable KPI card
            ├── ChartCard.jsx          ← Reusable chart wrapper
            ├── Sidebar.jsx            ← Sidebar + filters
            └── StatisticsPanel.jsx    ← Stats, outliers, correlation
```

---

## Quick Start

### 1 — Backend (Python / FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --port 8000
```

API will be live at **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

---

### 2 — Frontend (React / Vite)

```bash
cd frontend

# Install Node dependencies
npm install

# Start dev server
npm run dev
```

Dashboard will open at **http://localhost:5173**

---

## API Endpoints

| Method | Endpoint              | Description                                |
|--------|-----------------------|--------------------------------------------|
| GET    | `/health`             | Server health + row count                  |
| GET    | `/meta`               | Filter options (cities, categories)        |
| GET    | `/kpis`               | Revenue, profit, orders, margin            |
| GET    | `/city-revenue`       | Revenue grouped by city                    |
| GET    | `/category-revenue`   | Revenue grouped by category                |
| GET    | `/top-products`       | Top N products by revenue                  |
| GET    | `/scatter`            | Orders vs Revenue scatter data             |
| GET    | `/heatmap`            | City × Category pivot matrix               |
| GET    | `/influencer-impact`  | Avg revenue by influencer status           |
| GET    | `/discount-analysis`  | Revenue/orders by discount tier            |
| GET    | `/price-ranges`       | Revenue by current price bucket            |
| GET    | `/statistics`         | Mean, std, skewness, Z-scores, outliers    |
| GET    | `/correlation`        | Pearson r, p-values between variables      |
| GET    | `/forecast`           | Linear regression + confidence bands       |
| GET    | `/insights`           | AI-generated business insights             |
| GET    | `/data`               | Paginated raw data                         |
| POST   | `/upload`             | Upload new CSV to replace dataset          |

All GET endpoints accept query params: `city`, `category`, `influencer`, `search`

---

## Key Features vs v1.0

| Feature                        | v1.0       | v2.0                          |
|-------------------------------|------------|-------------------------------|
| Data location                 | Hardcoded  | External CSV / POST upload     |
| Backend                       | None       | FastAPI + Pandas               |
| Statistical analytics         | None       | Z-scores, outliers, Shapiro-Wilk, Pearson r |
| Forecast confidence           | None       | ±1.96σ confidence band + R²    |
| Component architecture        | Single HTML| React components + custom hook |
| CSV upload                    | JS-only    | FastAPI multipart upload       |
| Filter logic                  | JS         | Python / Pandas                |

---

## Scaling to a Live Database (Next Steps)

To move from CSV to a real-time database:

```python
# backend/database.py  (add this)
import databases, sqlalchemy

DATABASE_URL = "postgresql://user:pass@localhost/zepto"
database = databases.Database(DATABASE_URL)

# Replace pd.read_csv() with:
async def load_data_from_db():
    query = "SELECT * FROM sales"
    rows = await database.fetch_all(query)
    return pd.DataFrame(rows)
```

Recommended: **Supabase** (hosted Postgres + real-time subscriptions) — free tier available.

---

## Developed by Ayush Mishra
