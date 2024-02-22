# icognition-backend
The backend application for icognition


# Installation - Databases
1. `cd docker-database`
2. `docker-compose up -d`

# Running with Docker
1. From project root
2. Run the docker compose: `docker-compose up --build` 

# Local Development
1. Create conda environment `conda create -n {NAME} python=3.12`
2. Install dependencies `pip install -r requirements.txt`


# Run
* Add env variables to session export $(cat .env | xargs) && env
* Terminal: `uvicorn main:app --reload --port 8889`
* VS Code press F5 on Windows 

# GCP Proxy Connection (not needed if using docker-databases)
* Command ./cloud-sql-proxy --port 3306 {connection_name}
* path '/home/eboraks/Projects/gcp-sql-proxy'
* Connect to DB: psql -h 127.0.0.1 -p 3306 -d test-db-eliran -U icog-db-user 


