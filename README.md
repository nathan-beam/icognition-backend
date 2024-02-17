# icognition-backend
The backend application for icognition

# Installation
1. Run the docker compose AI: Add commend
2. Create conda environment `conda create -n {NAME} python=3.12`
3. Install dependencies `pip install -r requirements.txt`

# Run
* Add env variables to session export $(cat .env | xargs) && env
* Terminal: `uvicorn main:app --reload --port 8889`
* VS Code press F5 on Windows 


## CI/CD Pipeline
* Set Github secrets key
** PRODUCTION_DATABASE_URL postgres://eliran:googleCloud1@34.23.234.126:5432/mydatabase, postgres+pg8000://icog-db-user:Case2214#34.23.234.126:5432/test-db-eliran
** GCP_SA_KEY: Create a base64 from the GCP service accout JSON key

