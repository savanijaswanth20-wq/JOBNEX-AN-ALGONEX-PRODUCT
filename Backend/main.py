#main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_connection
from analyzer import analyse_resume
import json 
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    resume_text: str
    jd_text: str


@app.get("/")
def home():
    return {
        "message": "Resume Analyzer Backend is Running"
    }


@app.post("/api/analyze")
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

        raise HTTPException(
            status_code=500,
            detail="Failed to save analysis"
        ) from error

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

