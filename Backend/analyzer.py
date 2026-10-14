#Analyzer.py
def analyse_resume(resume_text,jd_text):
    resume_text=resume_text.lower()
    jd_text=jd_text.lower()
    skills = [
            "python",
            "sql",
            "react",
            "fastapi",
            "docker"
        ]

    matched_skills = []
    missing_skills=[]
    suggestion=[]
    match_score = 0.0
    for i in skills:
        if i in resume_text and i in jd_text:
            matched_skills.append(i)
            if skills:
                match_score=round(len(matched_skills)/len(skills)*100,2)
        else:
            missing_skills.append(i)
            suggestion.append(f"Try learning {i} for this profile add {i} to your resume")
            

    return {
        "matched_skills": matched_skills,
        "missing_skills":missing_skills,
        "suggestion":suggestion,
        "suggestions":suggestion,
        "matched_score":match_score
    }
   