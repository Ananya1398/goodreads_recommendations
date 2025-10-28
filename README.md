# Book Recommendation System (Goodreads + MLOps)

This project builds a machine learning-based book recommendation system using Goodreads data, with an end-to-end MLOps-ready architecture. It includes data processing, model training, recommendation logic, an API for serving, and Docker for containerization.

## Team Members

- Ananya Asthana
- Arpita Wagulde  
- Karan Goyal  
- Purva Agarwal  
- Shivam Sah  
- Shivani Sharma

## Project Architecture Overview

(Include a diagram or description of the architecture here)

## Data Sources

- **Goodreads Dataset:** Books, ratings, and metadata from the [Goodbooks dataset](https://cseweb.ucsd.edu/~jmcauley/datasets/goodreads.html)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/purva-agarwal/goodreads_recommendations.git
cd goodreads_recommendations
```

### 2. Set up Python Environment

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate     # macOS/Linux
# OR
venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

> **Note:** Make sure to activate your virtual environment before running any subsequent commands.

### 3. Run Training Pipeline

- Set the following environment variables from terminal.
  The variable set is only for this instance of terminal and will not affect others.
  
  ```bash
  export AIRFLOW_HOME=/path/to/your/config/folder
  ```
  
  Replace `/path/to/your/config/folder` with the absolute path to the config folder of the cloned repository.

- Request access to GCP credentials (access credentials will be shared per user basis)

- Place the access credentials in the config folder as `gcp_credentials.json`

```bash
airflow standalone
```

**Access the Airflow UI:**

A login password for the admin user will be shown in the terminal or in `config/simple_auth_manager_passwords.json.generated`

Open your browser and go to: <http://localhost:8080>

Login using the admin credentials

**Add Connection on Airflow UI:**

1. Go to Admin → Connections
2. Click "Add Connection"
3. Set Connection ID: `goodreads_conn`
4. Set Connection Type: `Google Cloud`
5. Paste the shared GCP access credentials JSON in the "Extra Fields JSON" field

**Run the DAG:**

1. In the Airflow UI, search for `goodreads_recommendation_pipeline` DAG
2. Click "Trigger DAG" to start execution

### 4. Start the Recommendation API

#### Locally (for development)

```bash
# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit: [http://localhost:8000/docs](http://localhost:8000/docs) to test the API using Swagger UI.

## Data Pipeline Architecture & Components

This section provides a detailed breakdown of the data pipeline components and their functionality within the Apache Airflow DAG.

### Pipeline Overview

The `goodreads_recommendation_pipeline` DAG orchestrates a comprehensive data processing workflow that transforms raw Goodreads data into a machine learning-ready dataset. The pipeline follows MLOps best practices with data validation, cleaning, feature engineering, and normalization stages.

### Pipeline Components (DAG Tasks)

#### 1. **Data Reading & Validation**
- **Task ID:** `read_data_from_bigquery`
- **Type:** `BigQueryInsertJobOperator`

- **Purpose:** Extracts data from Google BigQuery source tables and performs initial record count validation

- **Functionality:**
  - Queries both books and interactions tables from the mystery/thriller/crime genre subset
  - Validates data availability and record counts
  - Establishes connection to GCP BigQuery using configured credentials
  - Provides baseline metrics for data quality assessment

#### 2. **Results Logging**
- **Task ID:** `log_bq_results`
- **Type:** `PythonOperator`

- **Purpose:** Processes and logs the results from the BigQuery data reading task

- **Functionality:**
  - Retrieves job results from the previous BigQuery operation
  - Logs detailed information about data availability
  - Provides visibility into data extraction success metrics
  - Enables monitoring of data pipeline health

#### 3. **Pre-Cleaning Data Validation**
- **Task ID:** `validate_data_quality`
- **Type:** `PythonOperator`

- **Purpose:** Performs comprehensive data quality checks on raw source data

- **Functionality:**
  - Validates table structure and schema compliance
  - Checks for required columns and data types
  - Identifies missing values and data range violations
  - Detects anomalies in rating distributions and user behavior patterns
  - Stops pipeline execution if critical data quality issues are found
  - Sends failure notifications via email for immediate alerting

#### 4. **Data Cleaning**
- **Task ID:** `clean_data`
- **Type:** `PythonOperator`

- **Purpose:** Cleans and standardizes the raw Goodreads dataset

- **Functionality:**
  - Removes duplicate records and invalid entries
  - Standardizes text fields (titles, authors, descriptions)
  - Handles missing values using appropriate imputation strategies
  - Cleans and validates timestamp fields for reading dates
  - Removes outliers and invalid ratings
  - Creates cleaned tables in BigQuery for downstream processing

#### 5. **Post-Cleaning Validation**
- **Task ID:** `validate_cleaned_data`
- **Type:** `PythonOperator`

- **Purpose:** Validates data quality after cleaning operations

- **Functionality:**
  - Ensures cleaning process completed successfully
  - Verifies data integrity and consistency
  - Validates that cleaned data meets quality standards
  - Checks for any new issues introduced during cleaning
  - Provides confidence in data quality for feature engineering

#### 6. **Feature Engineering**
- **Task ID:** `feature_engg_data`
- **Type:** `PythonOperator`

- **Purpose:** Creates machine learning features from cleaned data

- **Functionality:**
  - **Book-level Features:**
    - Average reading time per book across all readers
    - Book popularity metrics (total ratings, average rating)
    - Genre and publication year features
    - Text-based features from book descriptions
  - **User-level Features:**
    - User reading patterns and preferences
    - Reading speed and completion rates
    - Genre preferences and rating patterns
  - **Interaction Features:**
    - User-book interaction history
    - Temporal features (reading dates, seasonal patterns)
    - Rating patterns and review sentiment

#### 7. **Data Normalization**
- **Task ID:** `normalize_data`
- **Type:** `PythonOperator`

- **Purpose:** Normalizes features for machine learning model consumption

- **Functionality:**
  - Applies appropriate scaling techniques (Min-Max, Z-score normalization)
  - Handles categorical variable encoding
  - Ensures feature distributions are suitable for ML algorithms
  - Creates final normalized dataset ready for model training
  - Maintains data consistency across different feature types

### Pipeline Flow & Dependencies

```text
start → read_data_from_bigquery → log_bq_results → validate_data_quality 
    → clean_data → validate_cleaned_data → feature_engg_data → normalize_data → end
```

### Error Handling & Monitoring

- **Email Notifications:** Automatic failure and success notifications sent to configured email addresses
- **Retry Logic:** Configurable retry attempts with exponential backoff
- **Logging:** Comprehensive logging at each stage for debugging and monitoring
- **Data Quality Gates:** Pipeline stops if critical data quality issues are detected
- **BigQuery Integration:** Seamless integration with Google Cloud Platform for scalable data processing

### Configuration & Environment

- **Airflow Configuration:** Managed through `config/airflow.cfg`
- **GCP Credentials:** Requires `gcp_credentials.json` in the config directory
- **Connection Management:** Uses `goodreads_conn` for BigQuery connectivity
- **Environment Variables:** `AIRFLOW_HOME` and `GOOGLE_APPLICATION_CREDENTIALS` configuration

## Folder Structure

| Folder/File                    | Description                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| `config/`                     | Airflow configuration files, DAG definitions, and database files for pipeline orchestration |
| `config/dags/`                | Apache Airflow DAG files defining the data pipeline workflow and task dependencies |
| `datapipeline/`               | Core data processing modules including data cleaning, feature engineering, and validation scripts |
| `datapipeline/data/`          | Data storage directories for raw, processed datasets and analysis notebooks |
| `datapipeline/data/raw/`      | Raw Goodreads dataset storage before any processing or cleaning operations |
| `datapipeline/data/processed/`| Cleaned and processed datasets with schema definitions for ML pipeline consumption |
| `datapipeline/data/notebooks/`| Jupyter notebooks for exploratory data analysis, bias analysis, and model prototyping |
| `datapipeline/scripts/`       | Main data processing scripts including cleaning, feature engineering, normalization, and anomaly detection |
| `datapipeline/scripts/logs/`  | Log files generated during data processing operations for debugging and monitoring |
| `datapipeline/tests/`         | Unit tests for data processing components to ensure code quality and reliability |
| `docs/`                       | Project documentation including scope definitions and technical specifications |
| `features.md`                 | Feature documentation describing implemented functionality and capabilities |
| `requirements.txt`            | Python package dependencies and version specifications for environment setup |
| `setup.py`                    | Python package configuration for installation and distribution management |
| `README.md`                   | Project documentation with setup instructions, architecture overview, and usage guidelines |

## Data Analysis & Insights

This section highlights key findings from our exploratory data analysis and bias detection notebooks that inform our recommendation system design.

### Raw Data Analysis (`raw_analysis.ipynb`)

**Purpose:** BigQuery data exploration to inspect raw data schema, null patterns, and data distributions.

**Analysis Performed:**

- **BigQuery Connection:** Connected to `recommendation-system-475301` project and queried `goodreads_books_mystery_thriller_crime` table
- **Data Sampling:** Retrieved 10,000 rows with 7 columns (book_id, title, authors, average_rating, ratings_count, popular_shelves, description)
- **Data Quality Assessment:** 
  - Zero missing values across all columns
  - 9,599 unique titles out of 10,000 books
  - 235 unique average rating values
  - 1,353 unique ratings count values
  - 7,367 unique descriptions
- **JSON Field Analysis:** Examined structured data in authors and popular_shelves columns
- **Statistical Summary:** Generated descriptive statistics and data type analysis

**Visualizations Generated:**

- Average rating distribution histogram with KDE curve
- Ratings count distribution (log scale)
- Description length distribution (word count)
- Missing values percentage per column
- Sample data saved to `../raw/goodreads_sample.csv`

### Bias Analysis & Fairness Assessment (`bias_analysis.ipynb`)

**Purpose:** Comprehensive bias detection and mitigation analysis using group-level shrinkage to ensure fair recommendations across multiple dimensions.

**Analysis Dimensions:**

1. **Popularity Bias** - High/Medium/Low popularity groups (based on book_popularity_normalized)
2. **Book Length Bias** - Categories based on book_length_category
3. **Book Era Bias** - Publication era groups (book_era)
4. **User Activity Bias** - High/Medium/Low activity user groups (based on user_activity_count)
5. **Reading Pace Bias** - Fast/Medium/Slow reader categories (reading_pace_category)
6. **Author Gender Bias** - Male/Female author groups (using gender_guesser library)

**Technical Implementation:**

- **Data Source:** BigQuery table `goodreads_features_cleaned` with 10,000+ records
- **Mitigation Method:** Group-level shrinkage with λ = 0.5 to pull extreme group means toward global mean
- **Metrics Analyzed:** 
  - Average rating per group (before/after mitigation)
  - Percentage read per group (behavioral metric, unchanged)
- **Fairness Calculation:** Equity index based on variance reduction and mean change penalties

**Analysis Process:**

- **Before Analysis:** Calculated group means for each dimension
- **Mitigation Applied:** Adjusted ratings using formula: `rating_debiased = original_rating - λ * (group_mean - global_mean)`
- **After Analysis:** Recalculated group means post-mitigation
- **Fairness Metrics:** Computed variance ratios, relative mean changes, and equity indices

**Key Findings:**

- **Bias Detection:** Systematic rating disparities identified across all analyzed dimensions
- **Mitigation Effectiveness:** Group mean shrinkage successfully reduced extreme group differences
- **Behavioral Preservation:** Reading behavior (% read) remained unchanged to preserve genuine user engagement
- **Fairness Improvement:** Equity index improvements achieved across all dimensions

**Visualizations Generated:**

- Side-by-side bar charts comparing before/after ratings for each dimension
- Side-by-side bar charts showing % read behavior (unchanged)
- Equity index summary bar chart across all dimensions
- Detailed explanations for each dimension's bias patterns and mitigation effects

**Output Files:**

- `fairness_summary_lambda_0_5.csv` - Comprehensive fairness metrics across all dimensions
- Multiple visualization charts showing bias reduction effectiveness