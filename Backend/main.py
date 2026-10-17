import os
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from database import get_connection
from analyzer import analyse_resume

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="JobNex - Resume Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def find_frontend_file(filename: str):
    base_dir = os.path.dirname(__file__)
    # Only look in static/ — ../Frontend/ is not accessible in Vercel serverless
    candidates = [
        os.path.join(base_dir, "static", filename),
        os.path.join(base_dir, filename),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


@app.get("/", response_class=HTMLResponse)
def home():
    html_path = find_frontend_file("Index.html") or find_frontend_file("index.html")
    if html_path and os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content="<h2>JobNex Backend is Running</h2><p>Frontend file not found.</p>", status_code=200)


@app.get("/style.css")
def get_css():
    css_path = find_frontend_file("style.css")
    if css_path and os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="text/css")
    return Response(content="", media_type="text/css")


@app.get("/script.js")
def get_js():
    js_path = find_frontend_file("script.js")
    if js_path and os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="application/javascript")
    return Response(content="", media_type="application/javascript")


@app.get("/api")
@app.get("/api/health")
def api_status():
    return {
        "message": "Resume analyser Backend is Running"
    }


class AnalyzeRequest(BaseModel):
    resume_text: str = Field(min_length=50, description="Resume content (at least 50 characters)")
    jd_text: str = Field(min_length=50, description="Job description content (at least 50 characters)")

    @field_validator('resume_text', 'jd_text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Input cannot be empty or contain only whitespace.")
        return v


@app.get("/api/history")
def get_history():
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, matched_score, matched_skills, missing_skills, created_at FROM resume_analyzer ORDER BY id DESC LIMIT 15")
        rows = cursor.fetchall()
        for r in rows:
            if isinstance(r.get("created_at"), object) and hasattr(r.get("created_at"), "isoformat"):
                r["created_at"] = r["created_at"].isoformat()
        return {"total": len(rows), "records": rows}
    except Exception as error:
        logger.warning(f"DB unavailable for /api/history: {error}")
        return {"total": 0, "records": []}  # graceful fallback for serverless
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.post("/api/analyze")
@app.post("/api/analyse")
def analyse(request: AnalyzeRequest):
    result = analyse_resume(request.resume_text, request.jd_text)
    connection = None
    cursor = None
    analysis_id = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        query = """
            INSERT INTO resume_analyzer (resume_text, jd_text, matched_skills, missing_skills, matched_score, suggestions)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            query, (
                request.resume_text,
                request.jd_text,
                json.dumps(result["matched_skills"]),
                json.dumps(result["missing_skills"]),
                result["matched_score"],
                json.dumps(result.get("suggestions", result.get("suggestion", [])))
            )
        )

        connection.commit()
        analysis_id = cursor.lastrowid

    except Exception as error:
        if connection is not None and connection.is_connected():
            connection.rollback()
        logger.warning(f"Database save skipped or unavailable: {error}")

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return {
        "Analysis_Id": analysis_id,
        **result
    }


# Backend API: Retrieve analysis history
@app.get("/api/analyses")
def get_analyses():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """SELECT
                id AS Analysis_id,
                matched_score,
                matched_skills,
                missing_skills,
                created_at AS created_At
            FROM resume_analyzer
            ORDER BY id DESC
            LIMIT 3"""

        cursor.execute(query)
        analyses = cursor.fetchall()

        for i in analyses:
            for field in ("matched_skills", "missing_skills"):
                value = i[field]
                if isinstance(value, str):
                    i[field] = json.loads(value)

        return {"analyses": analyses}

    except Exception as error:
        logger.warning(f"Database query skipped or unavailable: {error}")
        return {"analyses": []}

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()
