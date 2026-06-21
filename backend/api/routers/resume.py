from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.data import load_jobs, load_forecasts, get_nlp

router = APIRouter()


@router.get("/roles")
async def get_roles():
    from src.analyzer.gap import ROLE_KEYWORDS
    return {"roles": list(ROLE_KEYWORDS.keys())}


@router.post("/resume")
async def analyze_resume(file: UploadFile = File(...), role: str = Form(...)):
    try:
        from src.analyzer.gap import analyse_gap, ROLE_KEYWORDS
        from src.analyzer.resume import extract_resume_text
    except ImportError:
        raise HTTPException(status_code=503, detail="Analyzer dependencies not available.")

    nlp, matcher, skill_lookup = get_nlp()
    if nlp is None:
        raise HTTPException(status_code=503, detail="spaCy model not loaded. Run: python -m spacy download en_core_web_sm")

    if role not in ROLE_KEYWORDS:
        raise HTTPException(status_code=400, detail=f"Unknown role '{role}'. Valid roles: {list(ROLE_KEYWORDS.keys())}")

    content = await file.read()
    try:
        resume_text = extract_resume_text(content, file.filename or "upload.pdf")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not resume_text or len(resume_text) < 50:
        raise HTTPException(status_code=422, detail="Too little text extracted. If this is a scanned PDF, convert to DOCX first.")

    df = load_jobs()
    fc = load_forecasts()

    report = analyse_gap(resume_text, role, df, fc, nlp, matcher, skill_lookup)

    return {
        "readiness_score": report.readiness_score,
        "market_percentile": report.market_percentile,
        "jobs_analysed": report.jobs_analysed,
        "skills_present": report.skills_present,
        "skills_missing": report.skills_missing,
        "skill_demand": report.skill_demand,
        "role_top_skills": report.role_top_skills,
        "emerging_skills": report.emerging_skills,
    }
