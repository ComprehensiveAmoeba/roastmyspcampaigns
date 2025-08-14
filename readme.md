# SP Campaign Roaster 🔥

An advanced Streamlit application designed to analyze and "roast" Amazon Sponsored Products bulk sheets. This tool provides a high-level overview of an account's structural health and offers actionable insights to improve performance.

## 🚀 Overview

The SP Campaign Roaster ingests a standard bulk operations file from Amazon Advertising and performs a comprehensive analysis across four key pillars of account management:

1.  **Campaign Structure:** Classifies every campaign into specific archetypes (A-J) to identify well-organized campaigns versus inefficient or messy ones.
2.  **Automation vs. Control:** Analyzes the distribution of spend between automated (Auto) and manually controlled campaigns.
3.  **Funneling & Negatives:** Measures the usage of negative keywords to determine how effectively ad spend is being protected from irrelevant searches.
4.  **Bid Adjustments:** Checks the adoption of bid-by-placement strategies, a key indicator of advanced optimization.

The app then calculates an overall account score and presents the findings in a clear, metric-driven dashboard, complete with a detailed, downloadable breakdown of every campaign.

## 🛠️ How to Use

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2.  **Install Dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install streamlit pandas
    ```

3.  **Run the App:**
    ```bash
    streamlit run app.py
    ```

4.  **Download Your Bulk Sheet:**
    * Navigate to your Amazon Advertising Console -> Sponsored Products -> Bulk Operations.
    * Create & download a custom spreadsheet for the **Last 60 days**.
    * Ensure the data inclusion settings match the ones shown in the app's instruction manual.

5.  **Upload & Analyze:**
    * Open the app in your browser (usually at `http://localhost:8501`).
    * Upload the downloaded bulk sheet to the file uploader.
    * The app will automatically analyze the data and present the dashboard.

## ✨ Features

* **Overall Account Score:** A single, weighted metric to quickly gauge the health of your SP campaigns.
* **Four-Pillar Analysis:** Detailed cards for Structure, Automation, Funneling, and Bid Adjustments with color-coded feedback.
* **Campaign Structure Classification:** Every campaign is assigned a type (A-J) based on its structure, with clear definitions provided.
* **Detailed Campaign Breakdown:** A full, sortable table showing every campaign, its assigned type, and its key performance metrics (Spend, Sales, ACOS, ROAS).
* **Data Export:** Download the enriched campaign data as a CSV file for further analysis or reporting.
* **User-Friendly Interface:** Built with Streamlit for a clean, interactive, and easy-to-use experience.

## ✉️ Contact

For any questions, suggestions, or feedback, please feel free to reach out at **hola@soypat.es**.
