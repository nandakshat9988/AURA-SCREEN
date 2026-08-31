import uuid
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database
import rag
import llm

app = FastAPI(title="Role-Based Candidate Screening System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_INTERVIEW_TURNS = 3

class AnswerSubmission(BaseModel):
    answer: str

@app.get("/api/roles")
def list_roles():
    return {
        "roles": [
            {
                "id": "ai_ml",
                "name": "AI / Machine Learning Engineer",
                "source": "Tom Mitchell / Burkov Machine Learning",
                "description": "Evaluates inductive bias, neural networks, backpropagation, and foundational attention mechanisms."
            },
            {
                "id": "data_science",
                "name": "Data Scientist / Applied ML",
                "source": "Applied ML, Jason Brownlee & Scikit-Learn",
                "description": "Evaluates feature engineering, imputation, class imbalance metrics, bagging, and boosting."
            },
            {
                "id": "backend",
                "name": "Backend Engineer",
                "source": "System Design, Distributed Architectures & Storage",
                "description": "Evaluates ACID internals, asynchronous event loops, caching strategies, and API resilience."
            }
        ]
    }

@app.post("/api/sessions/start")
async def start_session(
    role: str = Form(...),
    resume_text: Optional[str] = Form(None),
    resume_file: Optional[UploadFile] = File(None)
):
    extracted_text = ""
    if resume_file and resume_file.filename:
        file_bytes = await resume_file.read()
        if resume_file.filename.lower().endswith(".pdf"):
            extracted_text = rag.extract_text_from_pdf(file_bytes)
        else:
            extracted_text = file_bytes.decode("utf-8", errors="ignore")
    elif resume_text and resume_text.strip():
        extracted_text = resume_text.strip()
    else:
        extracted_text = "Candidate Profile: Experience in Python, Software Engineering, and Computer Science."

    candidate_info = llm.parse_resume_content(extracted_text)
    session_id = str(uuid.uuid4())[:8]

    database.create_session(
        session_id=session_id,
        candidate_name=candidate_info.get("candidate_name", "Candidate"),
        role=role,
        resume_text=extracted_text,
        skills=candidate_info.get("skills", []),
        summary=candidate_info.get("summary", "")
    )

    query = f"{role} {' '.join(candidate_info.get('skills', []))}"
    rag_chunks = rag.retrieve_relevant_context(role, query, top_k=2)

    question_data = llm.generate_screening_question(
        role=role,
        candidate_info=candidate_info,
        rag_chunks=rag_chunks,
        turn_index=1,
        previous_turns=[]
    )

    database.save_interview_turn(
        session_id=session_id,
        turn_index=1,
        question=question_data.get("question"),
        rag_chunks=rag_chunks
    )

    return {
        "session_id": session_id,
        "candidate": candidate_info,
        "role": role,
        "turn_index": 1,
        "total_turns": MAX_INTERVIEW_TURNS,
        "question": question_data.get("question"),
        "topic": question_data.get("topic"),
        "difficulty": question_data.get("difficulty"),
        "rag_sources": rag_chunks
    }

@app.post("/api/sessions/{session_id}/answer")
def submit_answer(session_id: str, submission: AnswerSubmission):
    session = database.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    turns = database.get_interview_turns(session_id)
    current_turn = turns[-1]
    turn_index = current_turn["turn_index"]

    feedback = llm.evaluate_response(
        role=session["role"],
        question=current_turn["question"],
        rag_chunks=current_turn.get("rag_chunks", []),
        candidate_answer=submission.answer
    )

    database.save_interview_turn(
        session_id=session_id,
        turn_index=turn_index,
        question=current_turn["question"],
        rag_chunks=current_turn.get("rag_chunks", []),
        candidate_answer=submission.answer,
        feedback=feedback
    )

    if turn_index >= MAX_INTERVIEW_TURNS:
        all_turns = database.get_interview_turns(session_id)
        candidate_info = {
            "candidate_name": session["candidate_name"],
            "skills": session.get("skills", [])
        }
        report = llm.generate_final_report(candidate_info, session["role"], all_turns)
        database.save_evaluation(session_id, report)
        return {
            "is_completed": True,
            "turn_index": turn_index,
            "feedback": feedback,
            "summary": report
        }

    next_turn_index = turn_index + 1
    query = f"{session['role']} {current_turn.get('question')} {submission.answer}"
    next_rag_chunks = rag.retrieve_relevant_context(session["role"], query, top_k=2)

    updated_turns = database.get_interview_turns(session_id)
    candidate_info = {
        "candidate_name": session["candidate_name"],
        "skills": session.get("skills", []),
        "experience_level": "Mid-Level"
    }

    next_question_data = llm.generate_screening_question(
        role=session["role"],
        candidate_info=candidate_info,
        rag_chunks=next_rag_chunks,
        turn_index=next_turn_index,
        previous_turns=updated_turns
    )

    database.save_interview_turn(
        session_id=session_id,
        turn_index=next_turn_index,
        question=next_question_data.get("question"),
        rag_chunks=next_rag_chunks
    )

    return {
        "is_completed": False,
        "turn_index": next_turn_index,
        "total_turns": MAX_INTERVIEW_TURNS,
        "feedback_on_previous": feedback,
        "question": next_question_data.get("question"),
        "topic": next_question_data.get("topic"),
        "difficulty": next_question_data.get("difficulty"),
        "rag_sources": next_rag_chunks
    }

@app.get("/api/sessions/{session_id}/summary")
def get_summary(session_id: str):
    session = database.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    evaluation = database.get_evaluation(session_id)
    turns = database.get_interview_turns(session_id)
    for turn in turns:
        turn.pop("_id", None)
    session.pop("_id", None)
    if evaluation:
        evaluation.pop("_id", None)
    return {
        "session": session,
        "turns": turns,
        "evaluation": evaluation
    }
