import os
from datetime import datetime
from pymongo import MongoClient

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client["candidate_screening_db"]

sessions_collection = db["sessions"]
turns_collection = db["interview_turns"]
evaluations_collection = db["evaluations"]

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
    sessions_collection.insert_one(doc)
    return doc

def get_session(session_id: str):
    return sessions_collection.find_one({"_id": session_id})

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
    turns_collection.update_one(
        {"session_id": session_id, "turn_index": turn_index},
        {"$set": doc},
        upsert=True
    )
    return doc

def get_interview_turns(session_id: str):
    return list(turns_collection.find({"session_id": session_id}).sort("turn_index", 1))

def save_evaluation(session_id: str, evaluation_data: dict):
    evaluation_data["session_id"] = session_id
    evaluation_data["completed_at"] = datetime.utcnow().isoformat()
    evaluations_collection.update_one(
        {"session_id": session_id},
        {"$set": evaluation_data},
        upsert=True
    )
    sessions_collection.update_one(
        {"_id": session_id},
        {"$set": {"status": "completed"}}
    )
    return evaluation_data

def get_evaluation(session_id: str):
    return evaluations_collection.find_one({"session_id": session_id})
