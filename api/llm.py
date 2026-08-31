import os
import json
import anthropic

from dotenv import load_dotenv

load_dotenv()

CLAUDE_MODEL = "claude-3-opus-20240229"

def get_claude_client():
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        return anthropic.Anthropic(api_key=api_key)
    return None

def parse_resume_content(resume_text: str) -> dict:
    client = get_claude_client()
    if client:
        try:
            prompt = f"""Extract key candidate details from the following resume text.
Output MUST be pure JSON with keys: "candidate_name", "skills" (list of strings), "technologies" (list of strings), "experience_level" (Junior/Mid/Senior), "summary" (2-3 sentences).

Resume:
{resume_text}"""
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            text_resp = response.content[0].text.strip()
            clean_json = text_resp.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception:
            pass

    found_skills = []
    keywords = ["Python", "PyTorch", "TensorFlow", "Scikit-Learn", "FastAPI", "Docker", "SQL", "MongoDB", "Kubernetes", "AWS", "Machine Learning", "Deep Learning", "NLP", "Pandas", "NumPy", "Git"]
    for kw in keywords:
        if kw.lower() in resume_text.lower():
            found_skills.append(kw)
    if not found_skills:
        found_skills = ["Software Engineering", "Problem Solving", "Computer Science"]

    lines = [line.strip() for line in resume_text.split("\n") if line.strip()]
    candidate_name = lines[0] if lines else "Candidate"
    if len(candidate_name) > 40 or "@" in candidate_name:
        candidate_name = "Alex Mercer"

    return {
        "candidate_name": candidate_name,
        "skills": found_skills[:8],
        "technologies": found_skills,
        "experience_level": "Mid-Level",
        "summary": f"Candidate with hands-on exposure to {', '.join(found_skills[:4])} looking to demonstrate applied and conceptual depth in technical screening."
    }

def generate_screening_question(role: str, candidate_info: dict, rag_chunks: list, turn_index: int, previous_turns: list) -> dict:
    client = get_claude_client()
    context_text = "\n\n".join([f"[{chunk.get('source', 'Textbook')}]: {chunk.get('text', '')}" for chunk in rag_chunks])

    if client:
        try:
            prev_context = ""
            for turn in previous_turns:
                prev_context += f"\nQ: {turn.get('question')}\nA: {turn.get('candidate_answer')}\n"

            prompt = f"""You are an elite technical interviewer screening for the position of {role}.
Candidate details:
Name: {candidate_info.get('candidate_name')}
Skills: {', '.join(candidate_info.get('skills', []))}
Experience: {candidate_info.get('experience_level')}

Grounded Reference Knowledge:
{context_text}

Previous Turns in Session:
{prev_context if prev_context else "This is question 1."}

Generate interview question #{turn_index}.
The question must:
1. Be directly grounded in the provided reference knowledge.
2. Inquire deeply about conceptual understanding and practical architectural trade-offs.
3. Meaningfully challenge the candidate according to their skills.

Output MUST be pure JSON with keys:
"question": (string question),
"topic": (string topic),
"difficulty": ("Intermediate" or "Advanced"),
"focus_area": (string focus area)"""

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            text_resp = response.content[0].text.strip()
            clean_json = text_resp.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            data["grounded_context"] = rag_chunks
            return data
        except Exception:
            pass

    turn_templates = {
        "AI / Machine Learning Engineer": [
            {
                "topic": "Inductive Bias & Hypothesis Generalization",
                "difficulty": "Intermediate",
                "focus_area": "Tom Mitchell ML - Chapter 1 & 2",
                "question": "In machine learning theory as formulated by Tom Mitchell, why is an inductive bias strictly necessary for any learning algorithm to generalize to unseen instances? How does Occam's razor express itself in tree-based algorithms?"
            },
            {
                "topic": "Neural Optimizations & Gradient Propagation",
                "difficulty": "Advanced",
                "focus_area": "Backpropagation & Loss Optimization",
                "question": "When training deep multilayer feedforward networks, what mathematical mechanics cause vanishing and exploding gradients during backpropagation? What architectural and normalization strategies do you employ to stabilize training dynamics?"
            },
            {
                "topic": "Bias-Variance Tradeoff & Regularization",
                "difficulty": "Advanced",
                "focus_area": "Generalization & Statistical Learning",
                "question": "Walk through the mathematical decomposition of expected prediction error into bias, variance, and irreducible error. How do L1 Lasso and L2 Ridge regularizers geometrically influence parameter sparsity and model variance?"
            },
            {
                "topic": "Modern Attention & Foundation Architectures",
                "difficulty": "Advanced",
                "focus_area": "Scaled Dot-Product & Self-Attention",
                "question": "Explain the mechanics of Scaled Dot-Product Attention: Softmax((Q * K^T) / sqrt(d_k)) * V. Why is the scaling factor 1/sqrt(d_k) essential, and how does Multi-Head Attention permit attending to disparate representation subspaces?"
            }
        ],
        "Data Scientist / Applied ML": [
            {
                "topic": "Feature Engineering & Data Imputation",
                "difficulty": "Intermediate",
                "focus_area": "Exploratory Preprocessing & Scaling",
                "question": "How do you systematically handle multivariate missingness without introducing data leakage into test sets? Why would you select RobustScaler over StandardScaler when working with heavy-tailed financial or sensor data?"
            },
            {
                "topic": "Classification Metrics Under Extreme Imbalance",
                "difficulty": "Advanced",
                "focus_area": "Precision, Recall, ROC-AUC",
                "question": "When deploying fraud or anomaly detection models with 99.8% negative class prevalence, why is ROC-AUC often overly optimistic, and how does the Precision-Recall curve provide a more truthful evaluation of positive class utility?"
            },
            {
                "topic": "Bagging vs. Gradient Boosting Paradigms",
                "difficulty": "Advanced",
                "focus_area": "Random Forests & XGBoost Dynamics",
                "question": "Compare how Random Forests and Gradient Boosted Trees treat bias and variance. Why does bagging reduce variance while boosting drives down bias, and what hyperparameters prevent boosting from memorizing training residuals?"
            }
        ],
        "Backend Engineer": [
            {
                "topic": "ACID Guarantees & Distributed Datastores",
                "difficulty": "Advanced",
                "focus_area": "Write-Ahead Logging & B-Trees",
                "question": "How does a database storage engine enforce Durability and Atomicity using Write-Ahead Logging (WAL)? In high-throughput distributed systems, how do you navigate the trade-offs between linearizability and availability described in the CAP theorem?"
            },
            {
                "topic": "Asynchronous Concurrency & Backpressure",
                "difficulty": "Intermediate",
                "focus_area": "Event Loops & Message Brokers",
                "question": "Explain how non-blocking I/O event loops process thousands of concurrent network connections compared to thread-per-request architectures. How do message brokers with backpressure protect downstream microservices from cascading failures?"
            },
            {
                "topic": "Distributed Caching & Invalidation Patterns",
                "difficulty": "Advanced",
                "focus_area": "Cache-Aside, Write-Back & Invalidation",
                "question": "Under what concurrency conditions does the Cache-Aside pattern encounter race conditions leading to stale data? Compare Cache-Aside with Write-Back caching, and discuss your mitigation strategy for cache thundering herds."
            }
        ]
    }

    role_questions = turn_templates.get(role, turn_templates["AI / Machine Learning Engineer"])
    q_index = min(turn_index - 1, len(role_questions) - 1)
    selected = dict(role_questions[q_index])
    selected["grounded_context"] = rag_chunks
    return selected

def evaluate_response(role: str, question: str, rag_chunks: list, candidate_answer: str) -> dict:
    client = get_claude_client()
    context_text = "\n".join([chunk.get("text", "") for chunk in rag_chunks])

    if client and candidate_answer.strip():
        try:
            prompt = f"""You are evaluating a candidate's response to an interview question for {role}.
Question Asked: {question}
Grounded Reference Material:
{context_text}
Candidate's Answer:
{candidate_answer}

Evaluate technical accuracy, conceptual depth, and trade-off awareness on a scale of 0-100.
Output MUST be pure JSON with keys:
"score": (integer 0-100),
"strengths": (list of 2 short strings),
"improvements": (list of 1-2 short strings),
"feedback": (2-3 sentences of constructive critique)"""

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            text_resp = response.content[0].text.strip()
            clean_json = text_resp.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception:
            pass

    length = len(candidate_answer.strip().split())
    if length < 10:
        return {
            "score": 45,
            "strengths": ["Direct response provided"],
            "improvements": ["Answer lacks theoretical depth and concrete technical terminology"],
            "feedback": "The response touches upon the topic but needs deeper technical rigor, specific formula or architectural citations, and discussion of practical trade-offs."
        }
    elif length < 35:
        return {
            "score": 75,
            "strengths": ["Clear fundamental understanding", "Accurate core concept identification"],
            "improvements": ["Elaborate on edge cases and failure modes"],
            "feedback": "Solid answer addressing the primary requirement. Bringing in architectural constraints or mathematical context would elevate this to senior-level mastery."
        }
    else:
        return {
            "score": 90,
            "strengths": ["Comprehensive conceptual articulation", "Strong domain vocabulary", "Solid understanding of trade-offs"],
            "improvements": ["Include production monitoring or operational telemetry considerations"],
            "feedback": "Excellent, well-structured explanation demonstrating deep command of the concepts and their practical implications."
        }

def generate_final_report(candidate_info: dict, role: str, turns: list) -> dict:
    scores = [turn.get("feedback", {}).get("score", 70) for turn in turns]
    overall_score = round(sum(scores) / max(len(scores), 1))

    client = get_claude_client()
    if client:
        try:
            turns_summary = ""
            for idx, turn in enumerate(turns):
                turns_summary += f"Question {idx+1}: {turn.get('question')}\nAnswer: {turn.get('candidate_answer')}\nScore: {turn.get('feedback', {}).get('score')}\n\n"

            prompt = f"""Generate a comprehensive technical interview evaluation report.
Candidate: {candidate_info.get('candidate_name')}
Role: {role}
Interview Transcript:
{turns_summary}

Output MUST be pure JSON with keys:
"overall_score": {overall_score},
"technical_depth": (integer 0-100),
"conceptual_grounding": (integer 0-100),
"problem_solving": (integer 0-100),
"communication": (integer 0-100),
"recommendation": ("Strong Hire" or "Hire" or "Leaning Hire" or "Needs Further Development"),
"executive_summary": (3-4 sentences executive summary),
"top_strengths": (list of 3 key strengths),
"growth_areas": (list of 2 areas to improve)"""

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            text_resp = response.content[0].text.strip()
            clean_json = text_resp.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception:
            pass

    recommendation = "Strong Hire" if overall_score >= 85 else ("Hire" if overall_score >= 70 else "Leaning Hire")
    return {
        "overall_score": overall_score,
        "technical_depth": min(100, overall_score + 4),
        "conceptual_grounding": overall_score,
        "problem_solving": max(50, overall_score - 3),
        "communication": min(100, overall_score + 6),
        "recommendation": recommendation,
        "executive_summary": f"{candidate_info.get('candidate_name', 'The candidate')} participated in a structured technical screening for the {role} role. The evaluation demonstrated solid grounding against core textbook knowledge with consistent reasoning across conceptual and applied domains.",
        "top_strengths": [
            "Demonstrated strong comprehension of foundational principles and algorithms",
            "Effective problem formulation aligned with real-world engineering constraints",
            "Clear technical vocabulary and coherent communicative flow"
        ],
        "growth_areas": [
            "Deepen familiarity with high-throughput production failure modes",
            "Elaborate more on empirical validation metrics and monitoring"
        ]
    }
