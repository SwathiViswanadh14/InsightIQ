from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
import pandas as pd
from io import BytesIO

app = FastAPI(title="InsightIQ")
app.mount("/static", StaticFiles(directory="static"), name="static")
BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "static" / "index.html"


@app.get("/", response_class=HTMLResponse)
def home():
    if not HTML_FILE.exists():
        return HTMLResponse(
            "<h2>InsightIQ</h2><p>Please create static/index.html</p>",
            status_code=404
        )
    return HTML_FILE.read_text(encoding="utf-8")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = (file.filename or "").lower()

    try:
        contents = await file.read()

        if filename.endswith(".csv"):
            df = pd.read_csv(BytesIO(contents))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(BytesIO(contents))
        else:
            raise HTTPException(
                status_code=400,
                detail="Please upload a CSV or Excel file."
            )

        missing = {
            str(column): int(count)
            for column, count in df.isnull().sum().items()
        }

        return {
            "filename": file.filename,
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "column_names": [str(c) for c in df.columns],
            "missing_values": missing
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read file: {str(error)}"
        )
    finally:
        await file.close()
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InsightIQ | Business Analytics</title>

    <style>
        :root {
            --bg: #0b0b14;
            --sidebar: #10101d;
            --card: #151526;
            --border: #292941;
            --text: #f4f1ff;
            --muted: #a4a1bd;
            --purple: #8b5cf6;
            --purple-light: #c4b5fd;
            --green: #4ade80;
            --red: #fb7185;
        }

        * {
            box-sizing: border-box;
        }

        html {
            scroll-behavior: smooth;
        }

        body {
            margin: 0;
            background: var(--bg);
            color: var(--text);
            font-family: Inter, "Segoe UI", Arial, sans-serif;
        }

        button, input {
            font: inherit;
        }

        .layout {
            display: flex;
            min-height: 100vh;
        }

        .sidebar {
            width: 245px;
            padding: 28px 18px;
            background: var(--sidebar);
            border-right: 1px solid var(--border);
            flex-shrink: 0;
        }

        .brand {
            font-size: 24px;
            font-weight: 800;
            margin: 0 0 42px 8px;
            letter-spacing: -0.8px;
        }

        .brand span {
            color: var(--purple-light);
        }

        .nav-label {
            color: #77748f;
            font-size: 11px;
            letter-spacing: 1.5px;
            margin: 26px 10px 12px;
        }

        .nav-link {
            display: block;
            color: var(--muted);
            text-decoration: none;
            padding: 13px 12px;
            border-radius: 10px;
            margin-bottom: 6px;
        }

        .nav-link:hover, .nav-link.active {
            background: #27203d;
            color: var(--purple-light);
        }

        main {
            min-width: 0;
            flex: 1;
            padding: 36px;
            max-width: 1600px;
        }

        .eyebrow {
            font-size: 11px;
            letter-spacing: 2px;
            color: var(--purple-light);
            font-weight: 700;
        }

        h1 {
            font-size: clamp(28px, 4vw, 38px);
            margin: 12px 0;
            letter-spacing: -1px;
        }

        h2 {
            font-size: 21px;
            margin: 8px 0;
        }

        p {
            color: var(--muted);
            line-height: 1.6;
        }

        .section {
            margin-top: 30px;
            scroll-margin-top: 24px;
        }

        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 17px;
            padding: 24px;
            margin-bottom: 22px;
            min-width: 0;
        }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 16px;
            margin-top: 25px;
        }

        .kpi {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 15px;
            padding: 22px;
        }

        .kpi-label {
            color: var(--muted);
            font-size: 13px;
        }

        .kpi-value {
            font-size: 30px;
            font-weight: 750;
            margin-top: 12px;
            overflow-wrap: anywhere;
        }

        .upload-area {
            margin-top: 20px;
            border: 1px dashed #514176;
            background: #11111f;
            padding: 28px;
            text-align: center;
            border-radius: 13px;
        }

        input[type="file"] {
            width: 100%;
            max-width: 420px;
            color: var(--muted);
            margin: 12px auto;
        }

        button {
            background: var(--purple);
            color: white;
            border: 0;
            padding: 12px 20px;
            border-radius: 9px;
            cursor: pointer;
            font-weight: 700;
        }

        button:hover {
            background: #7c3aed;
        }

        button:disabled {
            opacity: 0.6;
            cursor: wait;
        }

        .status {
            margin-top: 14px;
            overflow-wrap: anywhere;
        }

        .status.error {
            color: var(--red);
        }

        .status.success {
            color: var(--green);
        }

        .chart-description {
            font-size: 13px;
        }

        .chart-section {
            margin-top: 26px;
        }

        .chart-scroll {
            overflow-x: auto;
            border-bottom: 1px solid #34304f;
            padding: 12px 8px 0;
        }

        .bar-chart {
            display: flex;
            align-items: stretch;
            gap: 10px;
            min-width: max-content;
            height: 220px;
        }

        .bar-group {
            width: 30px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: center;
            height: 100%;
        }

        .bar-value {
            font-size: 10px;
            color: var(--muted);
            margin-bottom: 5px;
            white-space: nowrap;
        }

        .bar {
            width: 20px;
            min-height: 3px;
            background: linear-gradient(180deg, #c4b5fd, #7c3aed);
            border-radius: 5px 5px 0 0;
        }

        .bar-label {
            font-size: 10px;
            color: #94a3b8;
            margin-top: 7px;
        }

        .insight-list {
            list-style: none;
            padding: 0;
            margin: 18px 0 0;
        }

        .insight-list li {
            padding: 15px;
            margin-top: 10px;
            border: 1px solid var(--border);
            border-left: 3px solid var(--purple);
            background: #11111f;
            border-radius: 9px;
            line-height: 1.6;
            overflow-wrap: anywhere;
        }

        .muted {
            color: var(--muted);
        }

        footer {
            padding: 22px 0;
            color: #77748f;
            font-size: 12px;
        }

        @media (max-width: 850px) {
            .layout {
                display: block;
            }

            .sidebar {
                width: 100%;
                padding: 18px;
                border-right: 0;
                border-bottom: 1px solid var(--border);
            }

            .brand {
                margin-bottom: 18px;
            }

            .nav-label {
                margin-top: 14px;
            }

            main {
                padding: 22px 16px;
            }

            .kpi-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>

<body>
<div class="layout">
    <aside class="sidebar">
        <div class="brand">✦ Insight<span>IQ</span></div>

        <div class="nav-label">WORKSPACE</div>
        <a class="nav-link active" href="#overview">◈ Overview</a>
        <a class="nav-link" href="#upload">▧ Data Upload</a>
        <a class="nav-link" href="#insights">✧ AI Insights</a>
        <a class="nav-link" href="#reports">▤ Reports</a>
    </aside>

    <main>
        <section id="overview">
            <div class="eyebrow">POWERED BY DATA ANALYTICS</div>
            <h1>Turn your data into decisions.</h1>
            <p>Welcome to your intelligent business analytics workspace.</p>

            <div class="kpi-grid">
                <div class="kpi">
                    <div class="kpi-label">Total Records</div>
                    <div class="kpi-value" id="records">—</div>
                </div>
                <div class="kpi">
                    <div class="kpi-label">Total Columns</div>
                    <div class="kpi-value" id="columns">—</div>
                </div>
                <div class="kpi">
                    <div class="kpi-label">Data Quality</div>
                    <div class="kpi-value" id="quality">—</div>
                </div>
            </div>
        </section>

        <section class="section card" id="upload">
            <div class="eyebrow">DATA INPUT</div>
            <h2>Upload Your Dataset</h2>
            <p>Upload a CSV or Excel file to explore and analyse your data.</p>

            <form id="uploadForm">
                <div class="upload-area">
                    <div style="font-size:34px;">📁</div>
                    <p>Select your dataset (.csv, .xlsx, .xls)</p>
                    <input
                        type="file"
                        id="fileInput"
                        name="file"
                        accept=".csv,.xlsx,.xls"
                        required
                    >
                    <br>
                    <button id="uploadButton" type="submit">
                        Analyse Dataset ↗
                    </button>
                    <div id="status" class="status" role="status" aria-live="polite">
                        Ready to analyse your data.
                    </div>
                </div>
            </form>
        </section>

        <section class="section card" id="charts">
            <div class="eyebrow">DATA VISUALIZATION</div>
            <h2>Explore Your Data</h2>
            <p id="chartDescription" class="chart-description">
                Upload a dataset to generate charts.
            </p>
            <div id="chartContainer"></div>
        </section>

        <section class="section card" id="insights">
            <div class="eyebrow">INSIGHT CENTRE</div>
            <h2>Your Data Story</h2>
            <p>Analysis generated from your uploaded dataset.</p>
            <ul id="insightList" class="insight-list">
                <li class="muted">Upload a dataset to see its analysis.</li>
            </ul>
        </section>

        <section class="section card" id="reports">
            <div class="eyebrow">REPORTS</div>
            <h2>Analysis Summary</h2>
            <p id="reportMessage">
                Your report will appear here after analysis.
            </p>
            <p id="columnSummary" class="muted"></p>
        </section>

        <footer>InsightIQ · Business Analytics Workspace</footer>
    </main>
</div>

<script>
    const form = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const statusElement = document.getElementById("status");
    const uploadButton = document.getElementById("uploadButton");

    function setStatus(message, type = "") {
        statusElement.textContent = message;
        statusElement.className = "status" + (type ? " " + type : "");
    }

    function renderCharts(chartData) {
        const container = document.getElementById("chartContainer");
        const description = document.getElementById("chartDescription");

        container.replaceChildren();

        const columns = Object.keys(chartData || {});

        if (columns.length === 0) {
            description.textContent =
                "No numeric columns found. Upload a dataset with numeric values.";
            return;
        }

        description.textContent =
            "Showing the first 20 available values for each numeric column.";

        columns.forEach(column => {
            const entries = (chartData[column] || []).filter(
                item => Number.isFinite(Number(item.value))
            );

   
            if (entries.length === 0) return;

            const section = document.createElement("div");
            section.className = "chart-section";

            const heading = document.createElement("h3");
            heading.textContent = column;
            heading.style.color = "#c4b5fd";
            section.appendChild(heading);

            const scroll = document.createElement("div");
            scroll.className = "chart-scroll";

            const chart = document.createElement("div");
            chart.className = "bar-chart";

            const values = entries.map(item => Number(item.value));
            const minValue = Math.min(0, ...values);
            const maxValue = Math.max(0, ...values);
            const range = maxValue - minValue || 1;
            const zeroPosition = (maxValue / range) * 160;

            chart.style.height = "220px";
            chart.style.alignItems = "stretch";

            entries.forEach(item => {
                const value = Number(item.value);
                const group = document.createElement("div");
                group.className = "bar-group";
                group.title = `${column}: ${value}`;

                const valueLabel = document.createElement("span");
                valueLabel.className = "bar-value";
                valueLabel.textContent = value.toLocaleString(
                    undefined,
                    { maximumFractionDigits: 2 }
                );

                const plot = document.createElement("div");
                plot.style.cssText =
                    "height:160px;width:100%;display:flex;" +
                    "align-items:stretch;justify-content:center;";

                const bar = document.createElement("div");
                bar.className = "bar";

                const height = Math.max(3, Math.abs(value) / range * 150);
                bar.style.height = `${height}px`;
                bar.style.alignSelf = value >= 0 ? "flex-end" : "flex-start";

                if (value < 0) {
                    bar.style.background =
                        "linear-gradient(180deg,#fb7185,#be123c)";
                }

                plot.appendChild(bar);

                const label = document.createElement("span");
                label.className = "bar-label";
                label.textContent = Number(item.row) + 1;

                group.appendChild(valueLabel);
                group.appendChild(plot);
                group.appendChild(label);
                chart.appendChild(group);
            });

            scroll.appendChild(chart);
            section.appendChild(scroll);
            container.appendChild(section);
        });
    }

    function renderInsights(insights) {
        const list = document.getElementById("insightList");
        list.replaceChildren();

        if (!Array.isArray(insights) || insights.length === 0) {
            const item = document.createElement("li");
            item.textContent = "No insights were returned for this dataset.";
            list.appendChild(item);
            return;
        }

        insights.forEach(message => {
            const item = document.createElement("li");
            item.textContent = message;
            list.appendChild(item);
        });
    }

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        if (!fileInput.files || fileInput.files.length === 0) {
            setStatus("Please select a file first.", "error");
            return;
        }

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        uploadButton.disabled = true;
        setStatus("Analysing dataset...");

        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Upload failed.");
            }

            document.getElementById("records").textContent =
                Number(result.total_rows).toLocaleString();

            document.getElementById("columns").textContent =
                Number(result.total_columns).toLocaleString();

            const missingValues = Object.values(
                result.missing_values || {}
            ).reduce((sum, value) => sum + Number(value || 0), 0);

            const totalCells =
                Number(result.total_rows) * Number(result.total_columns);

            const quality = totalCells > 0
                ? Math.round((1 - missingValues / totalCells) * 100)
                : 100;

            document.getElementById("quality").textContent =
                `${quality}%`;

            renderCharts(result.chart_data || {});
            renderInsights(result.insights || []);

            document.getElementById("reportMessage").textContent =
                `${result.filename || "Dataset"} — ` +
                `${result.total_rows} rows and ` +
                `${result.total_columns} columns. ` +
                `${missingValues} missing values found.`;

            document.getElementById("columnSummary").textContent =
                "Columns: " + (result.column_names || []).join(", ");

            setStatus("Dataset analysed successfully!", "success");

            document.getElementById("insights").scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        } catch (error) {
            setStatus("Error: " + error.message, "error");
        } finally {
            uploadButton.disabled = false;
        }
    });
</script>
</body>
</html><p id="columnSummary" class="muted"></p>
<div style="display:flex; gap:12px; flex-wrap:wrap; margin-top:20px;">
    <button type="button" onclick="window.location.href='/download/excel'">
        📊 Download Excel Report
    </button>

    <button type="button" onclick="window.location.href='/download/pdf'">
        📄 Download PDF Report
    </button>
</div>

</html>



