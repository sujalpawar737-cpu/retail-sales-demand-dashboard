# Retail Sales & Demand Dashboard

**VIT Pune · DS2004 Fundamentals of Data Science — course-project extension**  
Base topic: **Retail Sales Trends and Product Demand Analysis**

An interactive, student-level dashboard built with Streamlit, Pandas and Plotly. It analyzes **real historical transaction records**, highlights data-preparation decisions, explores repeat product demand and demonstrates a basic Linear Regression backtest.

## What is included

- **Overview:** sales-line value (GBP), unique invoices, units, products, monthly trends, country breakdown, weekday activity.
- **Product & demand:** product selection, monthly demand, product comparison and K-means grouping (an optional FODS extension).
- **Prediction lab:** *independent dashboard baseline*, not the group's original Colab model; weekly Linear Regression with lag features, chronological backtesting, MAE/RMSE/R² and comparison with a four-week-average baseline.
- **Data & methods:** line counts, exclusions, reproducible preprocessing decisions, clear limits and dataset attribution.

This is **not** a live retailer dashboard, a net-profit calculator, an inventory optimizer or a current-year demand forecast.

## Run locally (Windows, PowerShell)

```powershell
# Extract Retail_Sales_Dashboard.zip, then open a terminal in that folder
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If you don't have Python 3.12, use `py -m venv .venv` and a compatible Python version, preferably Python 3.12 or 3.13. After the server starts, open the address displayed in the terminal (commonly `http://localhost:8501`).

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

**No database, API key or credentials are needed.** The app includes its prepared compressed CSV data.

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository with the extracted files (including `data/sales_clean.csv.gz`, `data/quality_report.json` and `.streamlit/config.toml`). Keep the original `Online Retail.xlsx` out of GitHub.
2. Check that the repository root contains `app.py` and `requirements.txt`.
3. Open [share.streamlit.io](https://share.streamlit.io/), sign in and choose **Create app → deploy an existing app**.
4. Select your repository, `main` branch, and entrypoint **app.py**.
5. Deploy and inspect all four sections using the public address.

Streamlit documentation: [deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

For evaluation, run the local version as a backup to the hosted version.

## Data provenance and reproducible cleaning

Source: **UCI Machine Learning Repository, Online Retail, dataset 352** — [official dataset page](https://archive.ics.uci.edu/dataset/352/online+retail). The original data are historical UK retail invoice line items collected from **1 Dec 2010 to 9 Dec 2011**. **Currency is GBP**. The source dataset is distributed under **CC BY 4.0**; attribution is maintained here and in the app.

Included `data/sales_clean.csv.gz` and `data/quality_report.json` are generated from the supplied `Online Retail.xlsx` using `scripts/prepare_data.py`:

```bash
python scripts/prepare_data.py --input "online+retail.zip"
```

The above command expects a copy of the original ZIP in the project directory; the processed files are already included, so rerunning preparation is optional. You can alternatively pass `--input "Online Retail.xlsx"`.

**Original:** 541,909 invoice line items. **Retained:** 530,104 valid positive-sales line items. Exclusions are allocated sequentially: 9,288 cancellation-coded; 1,336 nonpositive quantity; 1,181 nonpositive unit price. 135,080 rows have missing CustomerID; these **are not automatically removed** because customer identity is unnecessary for this product-focused analysis. Valid duplicate-looking rows are not indiscriminately removed. The public app's prepared file does **not contain CustomerID**.

**Sales metric:** `Quantity * UnitPrice` for retained positive invoice lines. This is **not** net revenue including refunds, gross margin, profit, or cash received. Revenue widgets include any valid positive service/fee lines; product ranking excludes identified non-merchandise stock codes.

**Exceptional orders:** Some products appear in a very large single order. To avoid presenting that as recurring consumer demand, overview's top-product chart ranks by distinct invoices and requires at least 10 distinct invoices for a product. No statistically uncertain outlier is silently deleted from the dataset.

## Prediction lab: what it really does

This lab uses a **separate model** since the existing team's Google Colab notebook was not available. It can be replaced/integrated later, rather than being misrepresented as the previously completed model.

For selected frequently ordered products, it constructs a **complete weekly series**, fills unrecorded product-weeks with zero recorded units, and omits the initial and final partial calendar weeks. It uses only the preceding 1, 2 and 4 weeks, the preceding four-week average and the week index to predict the *next* week's units. The last ten complete weeks are a chronological holdout evaluated with rolling one-week-ahead inputs. A simple 4-week average acts as the comparison baseline. The final one-week estimate refers to **December 2011**; it is not a 2026 forecast.

A negative R² or a baseline performing better is possible and is intentionally shown. The dashboard's main product-sales analysis remains useful even when a simple prediction model underperforms.

## Before treating this as your group's final CP dashboard

Compare the supplied data-cleaning decisions, charts, formulas and model features with your existing Colab notebook. Your original notebook was **not supplied**, so these may not match the team's course-project methodology or results. Reconcile them and use the same model or disclose the dashboard model as a supplemental experiment. Do not claim the dashboard is a literal export of your notebook until verified.

## Key files

```text
app.py                    Streamlit interface (4 views)
analytics.py              Data Science computations and model
scripts/prepare_data.py   Reproducible source Excel → compressed CSV conversion
data/sales_clean.csv.gz    Prepared data, no CustomerID
data/quality_report.json Cleaning audit
requirements.txt          Runtime dependencies
.streamlit/config.toml    Theme configuration
tests/test_analytics.py   Basic checks
```

## Project limitations

- A **single historical retailer**, not all UK businesses or an Indian store.
- No stock-on-hand, supplier lead times or purchase costs, so no claim of exact inventory optimization or profit.
- Partial starting/ending months and extreme wholesale orders can distort patterns.
- No real-time system, sales database, user auth, or external API integration is represented.
- Any demand forecast is limited by one year of data and basic regression; evaluate results rather than assuming accuracy.
