# feature_engineering.py
"""
Feature Engineering Pipeline (Final BigQuery-Safe Version)
-----------------------------------------------------------
Runs entirely in BigQuery. Produces book-, user-, and interaction-level
features for Goodreads Mystery/Thriller/Crime dataset.

Output: books.goodreads_features_mystery_thriller_crime
"""

import os
from google.cloud import bigquery

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_credentials.json"

PROJECT_ID = "recommendation-system-475301"
DATASET = "books"

BOOKS_TABLE = f"{PROJECT_ID}.{DATASET}.goodreads_books_mystery_thriller_crime_cleaned"
INTERACTIONS_TABLE = f"{PROJECT_ID}.{DATASET}.goodreads_interactions_mystery_thriller_crime_cleaned"
DESTINATION_TABLE = f"{PROJECT_ID}.{DATASET}.goodreads_features_mystery_thriller_crime"

client = bigquery.Client(project=PROJECT_ID)

# -----------------------------------------------------------------------------
# BigQuery SQL Query
# -----------------------------------------------------------------------------
query = f"""
-- ==============================================================
-- BOOK-LEVEL FEATURES
-- ==============================================================
WITH base_books AS (
  SELECT
    book_id,
    title_clean,
    average_rating,
    ratings_count,
    text_reviews_count,
    LOG(1 + ratings_count) AS log_ratings_count,
    (ratings_count + text_reviews_count) AS popularity_score,
    LENGTH(title_clean) AS title_length_in_characters,
    ARRAY_LENGTH(SPLIT(title_clean, ' ')) AS title_length_in_words,
    LENGTH(description_clean) AS description_length,
    ARRAY_LENGTH(popular_shelves_flat) AS num_genres,
    IF(ARRAY_LENGTH(series_flat) > 0, TRUE, FALSE) AS is_series,
    CASE
      WHEN ratings_count = 0 THEN 0
      ELSE (
        1 + 4 * (
          ((average_rating - 1)/4) + POW(1.96,2)/(2*ratings_count)
          - 1.96 * SQRT((( (average_rating - 1)/4)*(1 - (average_rating - 1)/4) + POW(1.96,2)/(4*ratings_count)) / ratings_count)
        ) / (1 + POW(1.96,2)/ratings_count)
      )
    END AS adjusted_average_rating
  FROM `{BOOKS_TABLE}`
),

-- Compute 80th percentile threshold using APPROX_QUANTILES
threshold AS (
  SELECT 
    APPROX_QUANTILES(adjusted_average_rating, 100)[OFFSET(80)] AS rating_threshold
  FROM base_books
),

book_final AS (
  SELECT
    b.*,
    b.adjusted_average_rating >= t.rating_threshold AS great,
    -- Normalized popularity (0–1 scale)
    SAFE_DIVIDE(
      b.popularity_score - MIN(b.popularity_score) OVER(),
      NULLIF(MAX(b.popularity_score) OVER() - MIN(b.popularity_score) OVER(), 0)
    ) AS book_popularity_normalized
  FROM base_books b CROSS JOIN threshold t
),

-- ==============================================================
-- USER-LEVEL FEATURES
-- ==============================================================
user_features AS (
  SELECT
    user_id_clean,
    COUNTIF(is_read) AS num_books_read,
    AVG(IF(rating > 0, rating, NULL)) AS avg_rating_given,
    COUNT(book_id) AS user_activity_count,
    MAX(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', date_updated_clean)) AS recent_activity,
    DATE_DIFF(
      CURRENT_DATE(),
      DATE(MAX(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', date_updated_clean))),
      DAY
    ) AS recent_activity_days,
    AVG(
      DATE_DIFF(
        DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', read_at_clean)),
        DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', started_at_clean)),
        DAY
      )
    ) AS avg_reading_time_days
  FROM `{INTERACTIONS_TABLE}`
  GROUP BY user_id_clean
),

-- ==============================================================
-- INTERACTION-LEVEL FEATURES
-- ==============================================================
interaction_features AS (
  SELECT
    user_id_clean,
    book_id,
    rating,
    is_read,
    DATE_DIFF(
      DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', read_at_clean)),
      DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', started_at_clean)),
      DAY
    ) AS days_to_read,
    DATE_DIFF(
      CURRENT_DATE(),
      DATE(SAFE.PARSE_TIMESTAMP('%a %b %d %H:%M:%S %z %Y', read_at_clean)),
      DAY
    ) AS user_book_recency
  FROM `{INTERACTIONS_TABLE}`
),

-- ==============================================================
-- FINAL MERGE
-- ==============================================================
merged AS (
  SELECT
    i.*,
    u.num_books_read,
    u.avg_rating_given,
    u.user_activity_count,
    u.recent_activity_days,
    u.avg_reading_time_days,
    b.average_rating,
    b.adjusted_average_rating,
    b.great,
    b.log_ratings_count,
    b.popularity_score,
    b.book_popularity_normalized,
    b.num_genres,
    b.is_series,
    b.title_length_in_characters,
    b.title_length_in_words,
    b.description_length,
    (u.avg_rating_given - b.adjusted_average_rating) AS user_avg_rating_vs_book
  FROM interaction_features i
  LEFT JOIN user_features u USING(user_id_clean)
  LEFT JOIN book_final b USING(book_id)
)

SELECT * FROM merged
"""

# -----------------------------------------------------------------------------
# Run Query
# -----------------------------------------------------------------------------
job_config = bigquery.QueryJobConfig(
    destination=DESTINATION_TABLE,
    write_disposition="WRITE_TRUNCATE"
)

print("Running BigQuery feature engineering query...")
query_job = client.query(query, job_config=job_config)
query_job.result()
print(f"Features table successfully created: {DESTINATION_TABLE}")

# -----------------------------------------------------------------------------
# Optional: Save local sample
# -----------------------------------------------------------------------------
os.makedirs("../data/processed", exist_ok=True)
SAMPLE_PATH = "../data/processed/features_sample.csv"

sample_df = client.query(f"SELECT * FROM `{DESTINATION_TABLE}` LIMIT 500").to_dataframe()
sample_df.to_csv(SAMPLE_PATH, index=False)
print(f"Local sample saved: {SAMPLE_PATH}")
