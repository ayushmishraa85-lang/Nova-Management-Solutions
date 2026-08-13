"""
data_engine/dashboard_recommender.py
Dashboard Recommendation Engine — Part 16 of the NovaMS Data Engine spec.

Maps a detected business domain (+ available metrics/entities) to a
recommended set of dashboard sections. Returned as plain JSON so a
Streamlit/Plotly layer (or NovaMS's existing sidebar nav) can render it
dynamically — nothing here is hardcoded into the UI layer itself.
"""
from __future__ import annotations

from typing import Any, Dict, List

_DOMAIN_SECTIONS: Dict[str, List[str]] = {
    "ecommerce": ["Executive Overview", "Sales", "Products", "Customers", "Marketing", "Website/Funnel", "Refunds"],
    "retail": ["Executive Overview", "Sales", "Inventory", "Stores", "Customers"],
    "finance": ["Financial Overview", "Revenue", "Expenses", "Profit", "Cash Flow"],
    "sales": ["Executive Overview", "Pipeline", "Deals", "Sales Reps", "Win/Loss Analysis"],
    "marketing": ["Executive Overview", "Campaigns", "Channels", "Conversion Funnel", "Spend & ROI"],
    "hr": ["Workforce Overview", "Hiring", "Attrition", "Departments", "Employee Trends"],
    "education": ["Overview", "Enrollment", "Grades & Performance", "Courses", "Attendance"],
    "healthcare": ["Overview", "Patients", "Appointments", "Treatments", "Outcomes"],
    "operations": ["Overview", "Throughput", "Bottlenecks", "Workforce", "SLA Compliance"],
    "inventory": ["Overview", "Stock Levels", "Reorder Alerts", "Fast/Slow Movers", "Suppliers"],
    "logistics": ["Overview", "Delivery Performance", "Routes", "Carriers", "SLA Compliance"],
    "customer_support": ["Overview", "Ticket Volume", "Resolution Time", "Agent Performance", "CSAT"],
}

_DEFAULT_SECTIONS = ["Executive Overview", "Data Explorer", "Trends", "Segments"]


def recommend_dashboard(domain: str, available_metrics: List[str]) -> Dict[str, Any]:
    sections = _DOMAIN_SECTIONS.get(domain, _DEFAULT_SECTIONS)
    return dict(
        domain=domain,
        recommended_sections=sections,
        notes="Sections are a starting point based on the detected domain and available metrics — "
              "not every section will have data until the corresponding columns are present.",
        supporting_metrics=available_metrics,
    )
