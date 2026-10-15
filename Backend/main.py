#main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from database import get_connection
from analyzer import analyse_resume
import json 
app = FastAPI()

from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    resume_text: str = Field(min_length=50, description="Resume content (at least 50 characters)")
    jd_text: str = Field(min_length=50, description="Job description content (at least 50 characters)")

    @field_validator('resume_text', 'jd_text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Input cannot be empty or contain only whitespace.")
        return v


@app.get("/")
def home():
    return {
        "message": "Resume Analyzer Backend is Running"
    }


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
        raise HTTPException(status_code=500, detail="Failed to fetch records from database") from error
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()



@app.post("/api/analyze")
@app.post("/api/analyse")
def analyze(request: AnalyzeRequest):
    connection = None
    cursor = None

    try:
        result = analyse_resume(request.resume_text, request.jd_text)
        connection = get_connection()

        cursor = connection.cursor()

        query = """
                    INSERT INTO resume_analyzer (resume_text, jd_text, matched_score, matched_skills, missing_skills, suggestions)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
        cursor.execute(
            query,
            (
                request.resume_text,
                request.jd_text,
                result["matched_score"],
                json.dumps(result["matched_skills"]),
                json.dumps(result["missing_skills"]),
                json.dumps(result.get("suggestions", result.get("suggestion", [])))
            )
        )
        connection.commit()

        return {
            "message": "Analysis request saved successfully",
            "Analysis_Id": cursor.lastrowid,
            "result": result
        }

    except Exception as error:
        if connection is not None and connection.is_connected():
            connection.rollback()
        logger.exception("Error during analysis")     
        raise HTTPException(
            status_code=500,
            detail="Failed to save analysis"
        ) from error

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

