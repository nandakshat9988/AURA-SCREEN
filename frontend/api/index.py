import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from http.server import BaseHTTPRequestHandler
import json
import uuid
import database
import rag
import llm

MAX_INTERVIEW_TURNS = 3

class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        try:
            path = self.path.split("?")[0]
            if path == "/api/roles":
                roles = [
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
                self._send_json(200, {"roles": roles})
                return

            if "/api/sessions/" in path and path.endswith("/summary"):
                parts = path.strip("/").split("/")
                session_id = parts[2]
                session = database.get_session(session_id)
                if not session:
                    self._send_json(404, {"error": "Session not found"})
                    return
                eval_data = database.get_evaluation(session_id)
                turns = database.get_interview_turns(session_id)
                for t in turns:
                    t.pop("_id", None)
                session.pop("_id", None)
                if eval_data:
                    eval_data.pop("_id", None)
                self._send_json(200, {"session": session, "turns": turns, "evaluation": eval_data})
                return

            self._send_json(404, {"error": "Not Found"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def do_POST(self):
        try:
            path = self.path.split("?")[0]
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)

            if path == "/api/sessions/start":
                content_type = self.headers.get("Content-Type", "")
                role = "AI / Machine Learning Engineer"
                extracted_text = "Candidate profile with Python and Machine Learning experience."

                if "multipart/form-data" in content_type:
                    from urllib.parse import parse_qs
                    boundary = content_type.split("boundary=")[-1].strip()
                    parts = raw_body.split(b"--" + boundary.encode())
                    for part in parts:
                        if b'name="role"' in part:
                            headers_and_body = part.split(b"\r\n\r\n", 1)
                            if len(headers_and_body) > 1:
                                role = headers_and_body[1].rstrip(b"\r\n--").decode("utf-8", errors="ignore").strip()
                        elif b'name="resume_text"' in part:
                            headers_and_body = part.split(b"\r\n\r\n", 1)
                            if len(headers_and_body) > 1:
                                txt = headers_and_body[1].rstrip(b"\r\n--").decode("utf-8", errors="ignore").strip()
                                if txt:
                                    extracted_text = txt
                        elif b'name="resume_file"' in part:
                            headers_and_body = part.split(b"\r\n\r\n", 1)
                            if len(headers_and_body) > 1:
                                file_bytes = headers_and_body[1].rstrip(b"\r\n--")
                                if b"filename=" in part and len(file_bytes) > 20:
                                    try:
                                        pdf_txt = rag.extract_text_from_pdf(file_bytes)
                                        if pdf_txt:
                                            extracted_text = pdf_txt
                                    except Exception:
                                        extracted_text = file_bytes.decode("utf-8", errors="ignore")
                elif "application/json" in content_type:
                    try:
                        payload = json.loads(raw_body.decode("utf-8"))
                        role = payload.get("role", role)
                        extracted_text = payload.get("resume_text", extracted_text)
                    except Exception:
                        pass

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

                q_data = llm.generate_screening_question(
                    role=role,
                    candidate_info=candidate_info,
                    rag_chunks=rag_chunks,
                    turn_index=1,
                    previous_turns=[]
                )

                database.save_interview_turn(
                    session_id=session_id,
                    turn_index=1,
                    question=q_data.get("question"),
                    rag_chunks=rag_chunks
                )

                self._send_json(200, {
                    "session_id": session_id,
                    "candidate": candidate_info,
                    "role": role,
                    "turn_index": 1,
                    "total_turns": MAX_INTERVIEW_TURNS,
                    "question": q_data.get("question"),
                    "topic": q_data.get("topic"),
                    "difficulty": q_data.get("difficulty"),
                    "rag_sources": rag_chunks
                })
                return

            if "/api/sessions/" in path and path.endswith("/answer"):
                parts = path.strip("/").split("/")
                session_id = parts[2]
                session = database.get_session(session_id)
                if not session:
                    self._send_json(404, {"error": "Session not found"})
                    return

                payload = json.loads(raw_body.decode("utf-8"))
                candidate_answer = payload.get("answer", "")

                turns = database.get_interview_turns(session_id)
                current_turn = turns[-1] if turns else {"turn_index": 1, "question": "", "rag_chunks": []}
                turn_index = current_turn["turn_index"]

                feedback = llm.evaluate_response(
                    role=session.get("role", "AI / Machine Learning Engineer"),
                    question=current_turn.get("question", ""),
                    rag_chunks=current_turn.get("rag_chunks", []),
                    candidate_answer=candidate_answer
                )

                database.save_interview_turn(
                    session_id=session_id,
                    turn_index=turn_index,
                    question=current_turn.get("question", ""),
                    rag_chunks=current_turn.get("rag_chunks", []),
                    candidate_answer=candidate_answer,
                    feedback=feedback
                )

                if turn_index >= MAX_INTERVIEW_TURNS:
                    all_turns = database.get_interview_turns(session_id)
                    cand_info = {
                        "candidate_name": session.get("candidate_name", "Candidate"),
                        "skills": session.get("skills", [])
                    }
                    rep = llm.generate_final_report(cand_info, session.get("role", ""), all_turns)
                    database.save_evaluation(session_id, rep)
                    self._send_json(200, {
                        "is_completed": True,
                        "turn_index": turn_index,
                        "feedback": feedback,
                        "summary": rep
                    })
                    return

                next_turn_idx = turn_index + 1
                query = f"{session.get('role')} {current_turn.get('question')} {candidate_answer}"
                next_chunks = rag.retrieve_relevant_context(session.get("role", ""), query, top_k=2)
                upd_turns = database.get_interview_turns(session_id)
                cand_info = {
                    "candidate_name": session.get("candidate_name", "Candidate"),
                    "skills": session.get("skills", []),
                    "experience_level": "Mid-Level"
                }

                next_q = llm.generate_screening_question(
                    role=session.get("role", ""),
                    candidate_info=cand_info,
                    rag_chunks=next_chunks,
                    turn_index=next_turn_idx,
                    previous_turns=upd_turns
                )

                database.save_interview_turn(
                    session_id=session_id,
                    turn_index=next_turn_idx,
                    question=next_q.get("question"),
                    rag_chunks=next_chunks
                )

                self._send_json(200, {
                    "is_completed": False,
                    "turn_index": next_turn_idx,
                    "total_turns": MAX_INTERVIEW_TURNS,
                    "feedback_on_previous": feedback,
                    "question": next_q.get("question"),
                    "topic": next_q.get("topic"),
                    "difficulty": next_q.get("difficulty"),
                    "rag_sources": next_chunks
                })
                return

            self._send_json(404, {"error": "Not Found"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})
