# CarbonIQ

carbonIQ is a school-mandated, paperless environmental management platform that combines waste-collection reporting, geospatial mapping, and climate-data overlays to reduce pollution, improve waste collection, and inform resiliency planning. Students and staff identify waste hotspots via an intuitive map UI; reported items (waste type, photo, timestamps) are stored in a central DB and routed to waste management operations by schools or licensed parties.
The platform also replaces paper workflows (enrolment, finance, and exams) and brings AI-powered marking and analytics so the institution both reduces paper waste and uses students as distributed data collectors.

## Features

- **FastAPI**: Modern, high-performance Python web framework for building APIs.
- **MongoDB**: Flexible, scalable NoSQL database for persistent storage.
- **Async Support**: Asynchronous request handling for improved performance.
- **Dockerized**: Easily deployable using Docker and Docker Compose.

## Project Structure

```
/project-root
├── app/
│   ├── main.py         # FastAPI application entry point
│   ├── models.py       # Pydantic models and MongoDB schemas
│   ├── routes/         # API route definitions
│   └── db.py           # MongoDB connection logic
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image definition for FastAPI app
├── docker-compose.yml  # Multi-container setup for app and MongoDB
└── README.md           # Project documentation
```

## Setup (Without Docker)

1. **Clone the repository**
    ```bash
    git clone https://github.com/njange/CarbonIQ
    cd CarbonIQ
    ```

2. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure MongoDB**
    - Ensure MongoDB is running locally or update the connection string in `db.py`.

4. **Run the application**
    ```bash
    uvicorn app.main:app --reload
    ```

## Setup (With Docker)

1. **Build and start the containers**
    ```bash
    docker-compose up --build
    ```
    This will start both the FastAPI app and a MongoDB instance.

2. **Environment Variables**
    - You can configure MongoDB connection details in the `docker-compose.yml` or via environment variables.

3. **Stopping the containers**
    ```bash
    docker-compose down
    ```

## Example Usage

- Access the API documentation at: [http://localhost:8000/docs](http://localhost:8000/docs)
- Example endpoints:
    ```
    GET /items/
    POST /items/
    ```

## Contributing

1. Fork the repository.
2. Create a new branch.
3. Submit a pull request.

## License

MIT License.

---

**Note:**  
- Ensure Docker and Docker Compose are installed on your system for containerized deployment.
- For production deployments, update environment variables and security settings as needed.
- See the source code for detailed API route implementations and data models.
