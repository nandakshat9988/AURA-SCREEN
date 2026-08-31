import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "")
memory_store = {
    "sessions": {},
    "turns": {},
    "evaluations": {}
}

def get_db():
    if MONGO_URI and MONGO_URI.strip():
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            return client["candidate_screening_db"]
        except Exception:
            pass
    return None

def create_session(session_id: str, candidate_name: str, role: str, resume_text: str, skills: list, summary: str):
    doc = {
        "_id": session_id,
        "candidate_name": candidate_name,
        "role": role,
        "resume_text": resume_text,
        "skills": skills,
        "summary": summary,
        "status": "in_progress",
        "created_at": datetime.utcnow().isoformat()
    }
    db = get_db()
    if db is not None:
        try:
            db["sessions"].insert_one(doc)
            return doc
        except Exception:
            pass
    memory_store["sessions"][session_id] = doc
    return doc

def get_session(session_id: str):
    db = get_db()
    if db is not None:
        try:
            res = db["sessions"].find_one({"_id": session_id})
            if res:
                return res
        except Exception:
            pass
    return memory_store["sessions"].get(session_id)

def save_interview_turn(session_id: str, turn_index: int, question: str, rag_chunks: list, candidate_answer: str = "", feedback: dict = None):
    doc = {
        "session_id": session_id,
        "turn_index": turn_index,
        "question": question,
        "rag_chunks": rag_chunks,
        "candidate_answer": candidate_answer,
        "feedback": feedback or {},
        "updated_at": datetime.utcnow().isoformat()
    }
    db = get_db()
    if db is not None:
        try:
            db["interview_turns"].update_one(
                {"session_id": session_id, "turn_index": turn_index},
                {"$set": doc},
                upsert=True
            )
            return doc
        except Exception:
            pass
    if session_id not in memory_store["turns"]:
        memory_store["turns"][session_id] = {}
    memory_store["turns"][session_id][turn_index] = doc
    return doc

def get_interview_turns(session_id: str):
    db = get_db()
    if db is not None:
        try:
            turns = list(db["interview_turns"].find({"session_id": session_id}).sort("turn_index", 1))
            if turns:
                return turns
        except Exception:
            pass
    session_turns = memory_store["turns"].get(session_id, {})
    sorted_keys = sorted(session_turns.keys())
    return [session_turns[k] for k in sorted_keys]

def save_evaluation(session_id: str, evaluation_data: dict):
    evaluation_data["session_id"] = session_id
    evaluation_data["completed_at"] = datetime.utcnow().isoformat()
    db = get_db()
    if db is not None:
        try:
            db["evaluations"].update_one(
                {"session_id": session_id},
                {"$set": evaluation_data},
                upsert=True
            )
            db["sessions"].update_one(
                {"_id": session_id},
                {"$set": {"status": "completed"}}
            )
            return evaluation_data
        except Exception:
            pass
    memory_store["evaluations"][session_id] = evaluation_data
    if session_id in memory_store["sessions"]:
        memory_store["sessions"][session_id]["status"] = "completed"
    return evaluation_data

def get_evaluation(session_id: str):
    db = get_db()
    if db is not None:
        try:
            res = db["evaluations"].find_one({"session_id": session_id})
            if res:
                return res
        except Exception:
            pass
    return memory_store["evaluations"].get(session_id)
