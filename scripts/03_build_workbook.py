"""Telecom Customer Churn — build the Excel workbook from the outputs.
Run:  python3 scripts/03_build_workbook.py   (from the project folder)
Reads output/*.csv + output/kpis.txt (written by 01_clean_analyse.py and
02_train_models.py), writes excel/telecom-churn_dashboard.xlsx.
Layout follows the sibling analytics repos: Cover, KPIs, one sheet per
aggregate CSV, Dashboard with charts linked to the data sheets.
The workbook is a reconciled workbook with charts — it has no slicers and no
.pbix. That is stated in the README; do not call it interactive.
"""
import csv
import os
import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, Alignment

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
EXCEL = os.path.join(BASE, "excel")
os.makedirs(EXCEL, exist_ok=True)

wb = openpyxl.Workbook()


def add_sheet(name, rows, widths=None):
    ws = wb.create_sheet(name)
    for r in rows:
        ws.append(r)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    if widths:
        for col, w in widths.items():
            ws.column_dimensions[col].width = w
    return ws


def read_csv(name):
    with open(os.path.join(OUT, name), newline="") as f:
        return list(csv.reader(f))


# ---- Cover -----------------------------------------------------------------
cover = wb.active
cover.title = "Cover"
cover["A1"] = "Telecom Customer Churn Prediction"
cover["A1"].font = Font(bold=True, size=16)
cover["A2"] = ("Business question: which customers are about to leave, why, "
               "and what is a targeted retention offer worth?")
cover["A3"] = "Dataset: IBM Telco Customer Churn (public sample data), 7,043 customers, 21 features"
cover["A4"] = "Churn rate: 26.54% (1,869 of 7,043 customers left)"
cover["A5"] = "Best model (measured): XGBoost — 75.4% accuracy, 77.0% recall, 0.84 ROC-AUC on the held-out test set (n=1,409)"
cover["A6"] = "Licence: portfolio / learning use ONLY, never sellable — dataset © Original Authors (IBM Sample Data Sets)"
cover["A7"] = "How to reproduce: download the dataset with the links in README.md, then run scripts/01_clean_analyse.py, scripts/02_train_models.py, scripts/03_build_workbook.py"
cover["A8"] = "Built by Bhavya Patel. No .pbix in this repo; build it from powerbi/model.md."
for r in range(1, 9):
    cover.cell(row=r, column=1).alignment = Alignment(wrap_text=True)
cover.column_dimensions["A"].width = 130

# ---- KPIs ------------------------------------------------------------------
kpi_rows = [["Metric", "Value"]]
with open(os.path.join(OUT, "kpis.txt")) as f:
    for line in f:
        line = line.strip()
        if ": " in line:
            k, v = line.split(": ", 1)
            kpi_rows.append([k, v])
add_sheet("KPIs", kpi_rows, {"A": 42, "B": 22})

# ---- Data sheets -----------------------------------------------------------
sheets = {}
for name, title in [
    ("churn_by_contract.csv", "churn_by_contract"),
    ("churn_by_internet.csv", "churn_by_internet"),
    ("churn_by_payment.csv", "churn_by_payment"),
    ("churn_by_tenure.csv", "churn_by_tenure"),
    ("charges_by_segment.csv", "charges_by_segment"),
    ("model_results.csv", "model_results"),
    ("threshold_analysis.csv", "threshold_analysis"),
]:
    rows = read_csv(name)
    sheets[title] = add_sheet(title, rows, {"A": 32, "B": 14, "C": 14,
                                             "D": 16, "E": 18, "F": 16,
                                             "G": 16, "H": 16, "I": 16,
                                             "J": 16, "K": 16})
fi_rows = read_csv("feature_importance.csv")[:16]
sheets["feature_importance"] = add_sheet("feature_importance", fi_rows,
                                         {"A": 42, "B": 16, "C": 22})

# ---- Dashboard -------------------------------------------------------------
dash = wb.create_sheet("Dashboard")
dash["A1"] = "Telecom Customer Churn — Dashboard"
dash["A1"].font = Font(bold=True, size=14)
dash["A2"] = "Charts are linked to the data sheets in this workbook. Change the data, refresh the chart."
dash.column_dimensions["A"].width = 130


def bar_chart(ws, title, x_title, y_title, data_col, cats_col, nrows,
              height=7.5, width=14):
    ch = BarChart()
    ch.type = "col"
    ch.title = title
    ch.y_axis.title = y_title
    ch.x_axis.title = x_title
    ch.height = height
    ch.width = width
    ch.legend = None
    data = Reference(ws, min_col=data_col, min_row=1, max_row=nrows)
    cats = Reference(ws, min_col=cats_col, min_row=2, max_row=nrows)
    ch.add_data(data, titles_from_data=True)
    ch.set_categories(cats)
    ch.shape = 4
    return ch


# churn rate by contract: churn_rate_pct is column C (3), categories column A (1)
ws = sheets["churn_by_contract"]
dash.add_chart(bar_chart(ws, "Churn rate by contract (%)", "Contract",
                         "Churn rate %", 3, 1, 4), "A4")
# churn rate by internet service
ws = sheets["churn_by_internet"]
dash.add_chart(bar_chart(ws, "Churn rate by internet service (%)",
                         "Internet service", "Churn rate %", 3, 1, 4), "A20")
# churn rate by tenure band
ws = sheets["churn_by_tenure"]
dash.add_chart(bar_chart(ws, "Churn rate by tenure band (%)", "Tenure band",
                         "Churn rate %", 3, 1, 5), "A36")
# model accuracy vs recall: accuracy col B (2), recall col D (4), categories col A (1)
ws = sheets["model_results"]
ch = BarChart()
ch.type = "col"
ch.title = "Model accuracy vs recall (%) — class-weighted, test set"
ch.y_axis.title = "%"
ch.height = 7.5
ch.width = 14
ch.add_data(Reference(ws, min_col=2, min_row=1, max_row=5), titles_from_data=True)
ch.add_data(Reference(ws, min_col=4, min_row=1, max_row=5), titles_from_data=True)
ch.set_categories(Reference(ws, min_col=1, min_row=2, max_row=5))
ch.shape = 4
dash.add_chart(ch, "A52")

path = os.path.join(EXCEL, "telecom-churn_dashboard.xlsx")
wb.save(path)
print("WROTE", path)
