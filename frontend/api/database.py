import os
from datetime import datetime
from pymongo import MongoClient

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "Aura-Screen")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "aura-screen-resumes")

memory_store = {}

def get_collection():
    if MONGO_URI and MONGO_URI.strip():
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000)
            db = client[DB_NAME]
            return db[COLLECTION_NAME]
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
        "turns": [],
        "evaluation": None,
        "created_at": datetime.utcnow().isoformat()
    }
    col = get_collection()
    if col is not None:
        try:
            col.insert_one(doc)
            return doc
        except Exception:
            pass
    memory_store[session_id] = doc
    return doc

def get_session(session_id: str):
    col = get_collection()
    if col is not None:
        try:
            res = col.find_one({"_id": session_id})
            if res:
                return res
        except Exception:
            pass
    return memory_store.get(session_id)

def save_interview_turn(session_id: str, turn_index: int, question: str, rag_chunks: list, candidate_answer: str = "", feedback: dict = None):
    turn_data = {
        "turn_index": turn_index,
        "question": question,
        "rag_chunks": rag_chunks,
        "candidate_answer": candidate_answer,
        "feedback": feedback or {},
        "updated_at": datetime.utcnow().isoformat()
    }
    col = get_collection()
    if col is not None:
        try:
            col.update_one(
                {"_id": session_id},
                {"$pull": {"turns": {"turn_index": turn_index}}}
            )
            col.update_one(
                {"_id": session_id},
                {"$push": {"turns": turn_data}}
            )
            return turn_data
        except Exception:
            pass
    session = memory_store.get(session_id)
    if session:
        session["turns"] = [t for t in session.get("turns", []) if t.get("turn_index") != turn_index]
        session["turns"].append(turn_data)
    return turn_data

def get_interview_turns(session_id: str):
    session = get_session(session_id)
    if session and "turns" in session:
        return sorted(session["turns"], key=lambda t: t.get("turn_index", 0))
    return []

def save_evaluation(session_id: str, evaluation_data: dict):
    evaluation_data["completed_at"] = datetime.utcnow().isoformat()
    col = get_collection()
    if col is not None:
        try:
            col.update_one(
                {"_id": session_id},
                {"$set": {"evaluation": evaluation_data, "status": "completed"}}
            )
            return evaluation_data
        except Exception:
            pass
    session = memory_store.get(session_id)
    if session:
        session["evaluation"] = evaluation_data
        session["status"] = "completed"
    return evaluation_data

def get_evaluation(session_id: str):
    session = get_session(session_id)
    if session:
        return session.get("evaluation")
    return None
