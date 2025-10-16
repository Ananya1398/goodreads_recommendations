# 📚 Book Recommendation System (Goodreads + MLOps)

This project builds a machine learning-based book recommendation system using Goodreads data, with an end-to-end MLOps-ready architecture. It includes data processing, model training, recommendation logic, an API for serving, and Docker for containerization.

## 🙋‍♂️ Team Members

- Purva Agarwal  
- Ananya Asthana  
- Karan Goyal  
- Shivam Sah  
- Shivani Sharma  
- Arpita Wagulde

## 🏗️ Project Architecture Overview


## 📄 Data Sources

- **Goodreads Dataset:** Books, ratings, and metadata from the [Goodbooks dataset](https://cseweb.ucsd.edu/~jmcauley/datasets/goodreads.html)
- Additional sources (if any) can be added under `data/external/`

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/purva-agarwal/goodreads_recommendations.git
cd goodreads_recommendations
```
### 2. Set up Python Environment

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate     # macOS/Linux
# OR
.venv\Scripts\activate        # Windows

# Install dependencies

```

### 3. Run Training Pipeline

```bash

```

This will load the data, clean it, engineer features, train a model, and save it to the `models/` directory.

### 4. Start the Recommendation API

#### Locally (for development):

```bash

```

Visit: [http://localhost:8000/docs](http://localhost:8000/docs) to test the API using Swagger UI.

#### Or via Docker:

```bash

```

## 🐳 Using Docker

### Build the Docker Image

```bash

```

### Run the Docker Container

```bash

```

### Access the API

Open in browser:

## ✅ Features

- ✅ Clean and structured Goodreads data pipeline
- ✅ Feature engineering using TF-IDF, embeddings, and more
- ✅ Book recommendation logic (collaborative & content-based filtering)
- ✅ Model training and evaluation
- ✅ Model serving via FastAPI
- ✅ Containerized with Docker for portability and deployment

## 🧪 Testing

Run unit tests using:

```bash

```

Make sure you activate your virtual environment first.

## 📁 Folder Structure

| Folder/File         | Description                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| `notebooks/`        | Jupyter notebooks for exploration and prototyping                           |
| `src/`              | Source code (data processing, feature engineering, modeling, recommendation)|
| `pipeline/`         | ML pipeline orchestration (e.g., Prefect, MLflow)                           |
| `serving/`          | Model API implementation (e.g., FastAPI or Flask)                           |
| `models/`           | Trained models and serialized objects                                       |
| `tests/`            | Unit tests for core components                                              |
| `dockerfiles/`      | Docker images and related files for reproducibility and deployment          |
| `requirements.txt`  | Project dependencies (alternative: Poetry `pyproject.toml`)                 |
| `.dockerignore`     | Files/folders to exclude from Docker build context                          |
| `.gitignore`        | Files/folders to exclude from version control                               |
| `README.md`         | Project overview and usage instructions                                     |

## 📄 License

This project is for educational purpose.

## 🙋‍♀️ Contact

For questions, issues, or contributions, feel free to open a GitHub Issue or Pull Request.

