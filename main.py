      
from pathlib import Path
from io import BytesIO

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

app = FastAPI(title="InsightIQ")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
HTML_FILE = STATIC_DIR / "index.html"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Temporary storage for the most recently uploaded dataset
latest_df = None
latest_filename = "dataset"
latest_insights = []


@app.get("/", response_class=HTMLResponse)
def home():
    if not HTML_FILE.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return HTML_FILE.read_text(encoding="utf-8")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global latest_df, latest_filename, latest_insights

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

        missing_values = df.isnull().sum().to_dict()
        numeric_columns = df.select_dtypes(
            include="number"
        ).columns.tolist()

        chart_data = {}
        for column in numeric_columns:
            chart_data[column] = [
                {"row": int(index), "value": float(value)}
                for index, value in df[column].dropna().head(20).items()
            ]

        insights = []

        if df.empty:
            insights.append("The uploaded dataset is empty.")
        else:
            insights.append(
                f"Dataset overview: {len(df)} rows and "
                f"{len(df.columns)} columns."
            )

        total_missing = int(df.isnull().sum().sum())
        total_cells = int(df.shape[0] * df.shape[1])

        if total_missing > 0:
            missing_percentage = (
                total_missing / total_cells * 100 if total_cells else 0
            )
            insights.append(
                f"Data quality alert: {total_missing} missing values "
                f"({missing_percentage:.1f}% of all cells). "
                "Review incomplete data before making decisions."
            )
        else:
            insights.append("Data quality: No missing values were found.")

        for column in numeric_columns:
            values = pd.to_numeric(
                df[column], errors="coerce"
            ).dropna()

            if not values.empty:
                insights.append(
                    f"{column}: Average {values.mean():.2f}, "
                    f"highest {values.max():.2f}, "
                    f"lowest {values.min():.2f}."
                )

                if values.max() != values.min():
                    insights.append(
                        f"{column} shows variation across the dataset. "
                        "Review high and low records to identify "
                        "potential performance differences."
                    )
                else:
                    insights.append(
                        f"{column} has the same value across all "
                        "available numeric records."
                    )

        if not numeric_columns:
            insights.append(
                "No numeric columns found. Add numeric data to enable "
                "performance analysis."
            )
        # Smart insights: detect unusual numeric values
        for column in numeric_columns:
            values = pd.to_numeric(
                df[column], errors="coerce"
            ).dropna()

            if len(values) >= 4:
                mean_value = values.mean()
                std_value = values.std()

                if std_value > 0:
                    unusual_values = values[
                        (values - mean_value).abs() > 2 * std_value
                    ]

                    if not unusual_values.empty:
                        insights.append(
                            f"Unusual values detected in '{column}': "
                            f"{len(unusual_values)} record(s) differ "
                            "significantly from the dataset average. "
                            "Review these records."
                        )

        # Check for duplicate rows
        duplicate_count = int(df.duplicated().sum())

        if duplicate_count > 0:
            insights.append(
                f"Data quality alert: {duplicate_count} duplicate row(s) "
                "found. Review them before analysis."
            )
        else:
            insights.append("Data quality: No duplicate rows found.")
        # Save the latest successful upload for report downloads
        latest_df = df.copy()
        latest_filename = Path(file.filename or "dataset").stem
        latest_insights = insights.copy()

        return {
            "filename": file.filename,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "missing_values": {
                str(key): int(value)
                for key, value in missing_values.items()
            },
            "chart_data": chart_data,
            "insights": insights
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


def check_report_data():
    if latest_df is None:
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV or Excel file before downloading a report."
        )


@app.get("/download/excel")
def download_excel_report():
    check_report_data()

    output = BytesIO()
    df = latest_df
    total_missing = int(df.isnull().sum().sum())
    total_cells = int(df.shape[0] * df.shape[1])
    quality = (
        (total_cells - total_missing) / total_cells * 100
        if total_cells else 100
    )

    summary = pd.DataFrame({
        "Metric": [
            "Source file",
            "Total records",
            "Total columns",
            "Missing values",
            "Data quality (%)",
        ],
        "Value": [
            latest_filename,
            len(df),
            len(df.columns),
            total_missing,
            round(quality, 2),
        ],
    })

    missing = pd.DataFrame({
        "Column": [str(c) for c in df.columns],
        "Missing Values": [int(df[c].isnull().sum()) for c in df.columns],
    })

    insights = pd.DataFrame({"Business Insights": latest_insights})

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        missing.to_excel(writer, sheet_name="Missing Values", index=False)
        insights.to_excel(writer, sheet_name="Insights", index=False)
        df.to_excel(writer, sheet_name="Uploaded Data", index=False)

    output.seek(0)

    return Response(
        content=output.getvalue(),
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                f'attachment; filename="{latest_filename}_InsightIQ_Report.xlsx"'
        },
    )


@app.get("/download/pdf")
def download_pdf_report():
    check_report_data()

    output = BytesIO()
    df = latest_df
    total_missing = int(df.isnull().sum().sum())
    total_cells = int(df.shape[0] * df.shape[1])
    quality = (
        (total_cells - total_missing) / total_cells * 100
        if total_cells else 100
    )

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()
    story = [
        Paragraph("InsightIQ Analysis Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Source file: {latest_filename}", styles["Normal"]),
        Paragraph(f"Total records: {len(df)}", styles["Normal"]),
        Paragraph(f"Total columns: {len(df.columns)}", styles["Normal"]),
        Paragraph(f"Missing values: {total_missing}", styles["Normal"]),
        Paragraph(f"Data quality: {quality:.2f}%", styles["Normal"]),
        Spacer(1, 18),
        Paragraph("Missing Values by Column", styles["Heading2"]),
    ]

    table_data = [["Column", "Missing Values"]]
    for column in df.columns:
        table_data.append([
            Paragraph(str(column), styles["BodyText"]),
            str(int(df[column].isnull().sum())),
        ])

    table = Table(table_data, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4338CA")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([table, Spacer(1, 18)])

    story.append(Paragraph("Business Insights", styles["Heading2"]))
    for insight in latest_insights:
        story.append(Paragraph(str(insight), styles["BodyText"]))
        story.append(Spacer(1, 8))

    document.build(story)
    output.seek(0)

    return Response(
        content=output.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{latest_filename}_InsightIQ_Report.pdf"'
        },
    )
