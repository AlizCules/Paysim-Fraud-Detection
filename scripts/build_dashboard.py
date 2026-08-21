"""Build the interactive PaySim dashboard from verified Power BI CSV exports."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POWERBI_DIR = ROOT / "powerbi"
REPORTS_DIR = ROOT / "reports"
OUTPUT_PATH = REPORTS_DIR / "dashboard.html"

DATA_FILES = {
    "overall": ("overall_fraud_summary.csv", {"transactions", "fraud_transactions", "non_fraud_transactions", "fraud_rate"}),
    "by_type": ("fraud_rate_by_type.csv", {"type", "transactions", "fraud_transactions", "fraud_rate", "fraud_amount"}),
    "by_amount_band": ("fraud_rate_by_amount_band.csv", {"amount_band", "transactions", "fraud_transactions", "fraud_rate"}),
    "by_hour": ("fraud_rate_by_hour.csv", {"hour", "transactions", "fraud_transactions", "fraud_rate"}),
    "by_day": ("fraud_rate_by_day.csv", {"day", "transactions", "fraud_transactions", "fraud_rate"}),
    "by_segment": ("fraud_rate_by_segment.csv", {"type", "hour", "transactions", "fraud_transactions", "fraud_rate"}),
    "sql_alerts": ("alert_volume_selected_output.csv", {"scored_transactions", "alerts", "alert_rate", "mean_fraud_score"}),
    "model_alerts": ("alert_volume_by_model_threshold.csv", {"model", "feature_set", "split", "threshold", "alert_rate", "test_rows"}),
}

NUMERIC_FIELDS = {
    "transactions",
    "fraud_transactions",
    "non_fraud_transactions",
    "fraud_rate",
    "fraud_amount",
    "amount_band",
    "hour",
    "day",
    "scored_transactions",
    "alerts",
    "alert_rate",
    "mean_fraud_score",
    "threshold",
    "test_rows",
}


def _coerce(field: str, value: str) -> str | int | float:
    if field not in NUMERIC_FIELDS or field == "amount_band":
        return value
    if value == "":
        raise ValueError(f"Empty numeric value in field {field!r}")
    number = float(value)
    return int(number) if number.is_integer() else number


def read_export(key: str) -> list[dict[str, str | int | float]]:
    filename, required = DATA_FILES[key]
    path = POWERBI_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing Power BI export: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"{path.name} is missing columns: {sorted(missing)}")
        rows = [{field: _coerce(field, value) for field, value in row.items()} for row in reader]
    if not rows:
        raise ValueError(f"CSV has no data rows: {path}")
    return rows


def load_dashboard_data() -> dict[str, list[dict[str, str | int | float]]]:
    return {key: read_export(key) for key in DATA_FILES}


def build_html(data: dict[str, list[dict[str, str | int | float]]]) -> str:
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    template = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PaySim Fraud Analytics Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root { color-scheme: light; --ink: #17202a; --muted: #5d6d7e; --line: #d5d8dc; --panel: #fff; --bg: #f4f6f7; --accent: #1f618d; }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.45 Arial, sans-serif; }
    main { max-width: 1380px; margin: 0 auto; padding: 28px; }
    h1 { margin: 0 0 6px; font-size: 28px; }
    h2 { margin: 0 0 12px; font-size: 18px; }
    .subtitle, .note, .footer { color: var(--muted); }
    .note { margin: 0 0 20px; }
    .kpis, .grid { display: grid; gap: 14px; }
    .kpis { grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 22px 0; }
    .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .card, .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; box-shadow: 0 2px 8px rgba(23, 32, 42, .06); }
    .card { padding: 18px; }
    .panel { padding: 14px; min-width: 0; }
    .label { color: var(--muted); font-size: 13px; }
    .value { margin-top: 7px; font-size: 26px; font-weight: 700; }
    .chart { height: 330px; }
    .wide { grid-column: 1 / -1; }
    .control { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; color: var(--muted); }
    select { padding: 6px 8px; border: 1px solid var(--line); border-radius: 5px; background: #fff; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 8px 9px; border-bottom: 1px solid #eaedef; text-align: left; }
    th { background: #f8f9f9; }
    .footer { margin-top: 20px; font-size: 13px; }
    @media (max-width: 900px) { .kpis, .grid { grid-template-columns: 1fr; } .wide { grid-column: auto; } main { padding: 16px; } }
  </style>
</head>
<body>
<main>
  <h1>PaySim Transaction Fraud Analytics</h1>
  <p class="subtitle">Interactive analyst-facing preview generated from the aggregate files in <code>powerbi/</code>.</p>
  <p class="note"><strong>Scope:</strong> PaySim is simulated data, not real bank transaction data. Use these patterns for exploratory analysis and offline review prioritization only; this is not a production or real-time fraud-prevention application.</p>

  <section class="kpis" aria-label="Key performance indicators">
    <div class="card"><div class="label">Source transactions</div><div class="value" id="source-transactions">—</div></div>
    <div class="card"><div class="label">Source fraud rate</div><div class="value" id="source-fraud-rate">—</div></div>
    <div class="card"><div class="label">SQL scored alerts</div><div class="value" id="sql-alerts">—</div></div>
    <div class="card"><div class="label">SQL alert rate</div><div class="value" id="sql-alert-rate">—</div></div>
  </section>

  <section class="grid">
    <div class="panel"><h2>Fraud rate by transaction type</h2><div class="chart" id="by-type"></div></div>
    <div class="panel"><h2>Fraud rate by simulated hour</h2><div class="chart" id="by-hour"></div></div>
    <div class="panel"><h2>Fraud rate by amount band</h2><div class="chart" id="by-band"></div></div>
    <div class="panel"><h2>Fraud rate by simulated day</h2><div class="chart" id="by-day"></div></div>
    <div class="panel wide"><h2>High-risk type/hour segments</h2><div class="chart" id="by-segment"></div></div>
    <div class="panel wide">
      <h2>Alert-rate comparison by model and threshold</h2>
      <div class="control"><label for="model-filter">Candidate:</label><select id="model-filter"><option value="all">All candidates</option></select></div>
      <div class="chart" id="by-model"></div>
    </div>
    <div class="panel wide"><h2>High-risk segment detail</h2><div id="segment-table"></div></div>
  </section>

  <p class="footer">Source mapping: <code>powerbi/data_dictionary.md</code>. Model comparison rows are final-test reports with validation-selected thresholds; they are not operational alert-policy recommendations.</p>
</main>

<script>
const dashboardData = __DASHBOARD_DATA__;
const pct = value => `${(Number(value) * 100).toFixed(2)}%`;
const integer = value => new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Number(value));
const rateAxis = { tickformat: '.2%' };
const baseLayout = { margin: { t: 12, r: 20, b: 55, l: 62 }, paper_bgcolor: '#fff', plot_bgcolor: '#fff', font: { family: 'Arial, sans-serif', color: '#17202a' }, hovermode: 'closest' };
const config = { responsive: true, displaylogo: false };

const overall = dashboardData.overall[0];
const sqlAlerts = dashboardData.sql_alerts[0];
document.getElementById('source-transactions').textContent = integer(overall.transactions);
document.getElementById('source-fraud-rate').textContent = pct(overall.fraud_rate);
document.getElementById('sql-alerts').textContent = integer(sqlAlerts.alerts);
document.getElementById('sql-alert-rate').textContent = pct(sqlAlerts.alert_rate);

function draw(id, traces, extra = {}) {
  Plotly.newPlot(id, traces, { ...baseLayout, ...extra }, config);
}

draw('by-type', [{
  x: dashboardData.by_type.map(row => row.type),
  y: dashboardData.by_type.map(row => row.fraud_rate),
  customdata: dashboardData.by_type.map(row => [row.transactions, row.fraud_transactions, row.fraud_amount]),
  type: 'bar', marker: { color: '#1f618d' },
  hovertemplate: '%{x}<br>Fraud rate: %{y:.2%}<br>Transactions: %{customdata[0]:,}<br>Fraud transactions: %{customdata[1]:,}<br>Fraud amount: %{customdata[2]:,.2f}<extra></extra>'
}], { yaxis: { ...rateAxis, title: 'Fraud rate' }, xaxis: { title: 'Transaction type' } });

draw('by-hour', [{
  x: dashboardData.by_hour.map(row => row.hour),
  y: dashboardData.by_hour.map(row => row.fraud_rate),
  customdata: dashboardData.by_hour.map(row => [row.transactions, row.fraud_transactions]),
  mode: 'lines+markers', type: 'scatter', line: { color: '#1f618d' },
  hovertemplate: 'Hour %{x}<br>Fraud rate: %{y:.2%}<br>Transactions: %{customdata[0]:,}<br>Fraud transactions: %{customdata[1]:,}<extra></extra>'
}], { yaxis: { ...rateAxis, title: 'Fraud rate' }, xaxis: { title: 'Simulated hour', dtick: 2 } });

draw('by-band', [{
  x: dashboardData.by_amount_band.map(row => row.amount_band),
  y: dashboardData.by_amount_band.map(row => row.fraud_rate),
  customdata: dashboardData.by_amount_band.map(row => [row.transactions, row.fraud_transactions]),
  type: 'bar', marker: { color: '#2874a6' },
  hovertemplate: '%{x}<br>Fraud rate: %{y:.2%}<br>Transactions: %{customdata[0]:,}<br>Fraud transactions: %{customdata[1]:,}<extra></extra>'
}], { yaxis: { ...rateAxis, title: 'Fraud rate' }, xaxis: { title: 'Amount band' } });

draw('by-day', [{
  x: dashboardData.by_day.map(row => row.day),
  y: dashboardData.by_day.map(row => row.fraud_rate),
  customdata: dashboardData.by_day.map(row => [row.transactions, row.fraud_transactions]),
  mode: 'lines+markers', type: 'scatter', line: { color: '#5499c7' },
  hovertemplate: 'Day %{x}<br>Fraud rate: %{y:.2%}<br>Transactions: %{customdata[0]:,}<br>Fraud transactions: %{customdata[1]:,}<extra></extra>'
}], { yaxis: { ...rateAxis, title: 'Fraud rate' }, xaxis: { title: 'Simulated day' } });

draw('by-segment', [{
  x: dashboardData.by_segment.map(row => `${row.type} / h${row.hour}`),
  y: dashboardData.by_segment.map(row => row.fraud_rate),
  customdata: dashboardData.by_segment.map(row => [row.transactions, row.fraud_transactions]),
  type: 'bar', marker: { color: '#7b241c' },
  hovertemplate: '%{x}<br>Fraud rate: %{y:.2%}<br>Transactions: %{customdata[0]:,}<br>Fraud transactions: %{customdata[1]:,}<extra></extra>'
}], { yaxis: { ...rateAxis, title: 'Fraud rate' }, xaxis: { title: 'Retained type/hour segment', tickangle: -35 } });

const modelFilter = document.getElementById('model-filter');
const candidates = [...new Set(dashboardData.model_alerts.map(row => `${row.model} / ${row.feature_set}`))];
candidates.forEach(candidate => { const option = document.createElement('option'); option.value = candidate; option.textContent = candidate; modelFilter.appendChild(option); });
function drawModelComparison() {
  const selected = modelFilter.value;
  const rows = selected === 'all' ? dashboardData.model_alerts : dashboardData.model_alerts.filter(row => `${row.model} / ${row.feature_set}` === selected);
  draw('by-model', [{
    x: rows.map(row => `${row.model} / ${row.feature_set}`),
    y: rows.map(row => row.alert_rate),
    customdata: rows.map(row => [row.threshold, row.test_rows, row.split]),
    type: 'bar', marker: { color: '#239b56' },
    hovertemplate: '%{x}<br>Alert rate: %{y:.2%}<br>Threshold: %{customdata[0]}<br>Test rows: %{customdata[1]:,}<br>Split: %{customdata[2]}<extra></extra>'
  }], { yaxis: { ...rateAxis, title: 'Alert rate' }, xaxis: { title: 'Model / feature scope', tickangle: -25 } });
}
modelFilter.addEventListener('change', drawModelComparison);
drawModelComparison();

const segmentRows = dashboardData.by_segment.map(row => `<tr><td>${row.type}</td><td>${row.hour}</td><td>${integer(row.transactions)}</td><td>${integer(row.fraud_transactions)}</td><td>${pct(row.fraud_rate)}</td></tr>`).join('');
document.getElementById('segment-table').innerHTML = `<table><thead><tr><th>Type</th><th>Hour</th><th>Transactions</th><th>Fraud transactions</th><th>Fraud rate</th></tr></thead><tbody>${segmentRows}</tbody></table>`;
</script>
</body>
</html>
"""
    return template.replace("__DASHBOARD_DATA__", serialized)


def main() -> None:
    data = load_dashboard_data()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_html(data), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
