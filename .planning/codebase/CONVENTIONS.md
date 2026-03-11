### Coding Conventions (CONVENTIONS.md)
The project follows modern Python standards with a focus on FastAPI and Streamlit.
- **Formatting**: Uses `flake8` with a `max-line-length` of 88 (matching `black` standards).
- **Naming**: 
  - Functions and variables: `snake_case`.
  - Classes: `PascalCase`.
  - Constants: `UPPER_SNAKE_CASE`.
- **Architecture**:
  - **Backend**: Service-oriented architecture. Logic is encapsulated in `app/services/`, while `app/routes/` handle HTTP concerns using FastAPI. `SQLModel` (based on Pydantic and SQLAlchemy) is used for database models (`app/models/`) and request/response schemas (`app/schemas/`).
  - **Frontend**: Streamlit-based UI. Logic for API interaction is abstracted into `services/` (e.g., `dashboard_service.py`). UI components are modularized in `components/`.
- **Error Handling**: Uses FastAPI's `HTTPException` and custom middleware for request logging and exception catching. Sentry is integrated for production error tracking.
- **Dependency Injection**: Heavily utilizes FastAPI's `Depends` for database sessions and configuration.
