# InsightIQ – Business Analytics Dashboard

InsightIQ is a web-based business analytics dashboard built with Python and FastAPI. It helps users upload datasets, explore key metrics, visualize data, and generate useful business insights.

## Features

- Upload CSV and Excel datasets
- View key performance indicators (KPIs)
- Visualize data using charts
- Generate automated business insights
- Download reports in Excel and PDF formats
- ## Dashboard Preview

![InsightIQ Dashboard](<InsightIQ pic.png>)


## Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** HTML, CSS, JavaScript
- **Data Analysis:** Pandas
- **Visualization:** Charts

## How to Run Locally

1. Clone the repository:

   ```bash
   git clone https://github.com/SwathiViswanadh14/InsightIQ.git
   ```

2. Open the project folder:

   ```bash
   cd InsightIQ
   ```

3. Create and activate a virtual environment:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

4. Install the required dependencies:

   ```bash
   pip install fastapi uvicorn pandas openpyxl python-multipart
   ```

5. Start the application:

   ```bash
   python -m uvicorn main:app --reload
   ```

6. Open `http://127.0.0.1:8000` in your browser.

## Project Status

Developed as a beginner-friendly business analytics project to practice data analysis and web development.

## Author

Swathi Viswanadh
