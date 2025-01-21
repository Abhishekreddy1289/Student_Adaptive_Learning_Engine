from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import List, Dict
import uuid
import time
import numpy as np
from collections import defaultdict
import datetime
from uitils.session import SessionManager
from azure_openai.student_qna import StudentQnA
from uitils.uitil import Uitils
from azure_openai.recommendations import RecommendationsQuestions
from uitils.logger import custom_logger
from config import gpt4_model,api_key,api_version,openai_type,azure_endpoint

app = FastAPI()

session_manager=SessionManager('student_sessions.json')
student_inter=StudentQnA(gpt4_model, api_key, azure_endpoint, api_version, openai_type)
recommend_question=RecommendationsQuestions(gpt4_model, api_key, azure_endpoint, api_version, openai_type)
adapt_difficult_obj=Uitils()
logger = custom_logger.get_logger()

class LearningSession(BaseModel):
    student_id:str
    student_level: str
    learning_goals: List[str]
    @validator('student_level')
    def validate_student_level(cls, value):
        allowed_levels = ["beginner", "intermediate", "advanced"]
        if value not in allowed_levels:
            raise ValueError(f"student_level must be one of {', '.join(allowed_levels)}")
        return value

class InteractionRequest(BaseModel):
    interaction_id:str
    answer: str

@app.post("/sessions")
async def create_session(session: LearningSession):
    try:
        logger.info("Starting the process of creating a new learning session.")
        
        # Generate session_id using UUID
        random_uuid = uuid.uuid4()
        session_id = random_uuid.hex
        student_id = session.student_id
        learning_goals = session.learning_goals
        student_level = session.student_level
        
        logger.debug(f"Received data - Student ID: {student_id}, Learning Goals: {learning_goals}, Level: {student_level}")
        
        # Determine difficulty level based on student's level
        if student_level == "beginner":
            difficulty_level = "easy"
        elif student_level == "intermediate":
            difficulty_level = "medium"
        elif student_level == "advanced":
            difficulty_level = "hard"
        else:
            logger.error(f"Invalid student level received: {student_level}")
            raise HTTPException(status_code=400, detail="Invalid student level")
        random_uuid = uuid.uuid4()
        interaction_id = random_uuid.hex
        recom_question=recommend_question.recommend_question(learning_goals, student_level,difficulty_level,history=None)
        if recom_question["question"] != "OpenAI Not Responding":
            first_question=[{"interaction_id": interaction_id,
                    "question": recom_question["question"],
                    "answer": "",
                    "answer_time": 0,
                    "query_time": datetime.datetime.now().isoformat(),
                    "correct_answer":"not answered",
                    "confidence_level":0
                    }]
            session_data_1 = {
                "session_id": session_id,
                "student_id": student_id,
                "student_level": student_level,
                "difficulty_level": difficulty_level,
                "learning_goals": learning_goals,
                "session_state": "not started yet",
                "session_progress": 0,
                "session_start_time": datetime.datetime.now().isoformat(),
                "interactions": first_question
            }
            
            logger.info(f"Session data prepared for student {student_id} with session ID {session_id}")
            
            response = session_manager.insert_session(student_id, session_data_1)
            # Log the successful session creation
            logger.info(f"Session successfully created with session ID {session_id} for student {student_id}")
            
            return {"message": response, "session_id": session_id,"interaction_id": interaction_id,"question": recom_question["question"]}
        logger.error(f"Error occurred while calling OpenAI: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    except Exception as e:
        # Log the error if something goes wrong
        logger.error(f"Error occurred while creating session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/sessions/{student_id}/{session_id}/interactions")
async def track_interaction(student_id: str, session_id: str, request: InteractionRequest):
    try:
        session = session_manager.get_session(student_id, session_id)
        if not session:
            logger.warning(f"Session not found for student_id: {student_id}, session_id: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        answer_time=datetime.datetime.now().isoformat()
        logger.debug(f"Session found for student_id: {student_id}, session_id: {session_id}")
        try:
            interaction_q=session_manager.interaction_details(student_id, session_id,request.interaction_id)
            
            logger.debug(f"Session history read successfully for student_id: {student_id}, session_id: {session_id}")
        except Exception as e:
            logger.error(f"Error while reading history for student_id: {student_id}, session_id: {session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving session history")
        
        logger.debug(f"Current difficulty level: {interaction_q["difficulty_level"]}")
        try:
            response = student_inter.student_qna_fun(interaction_q["interaction_details"]["question"],request.answer, interaction_q["student_level"],interaction_q["difficulty_level"],interaction_q["learning_goals"], interaction_q["interactions"])
            logger.debug(f"Answer generated: {response}")
            if response["follow_up_question"] == "OpenAI Not Responding":
                logger.error(f"Error during Q&A processing for student_id: {student_id}, session_id: {session_id}: {str(e)}")
                raise HTTPException(status_code=500, detail="Error during Q&A processing")
        except Exception as e:
            logger.error(f"Error during Q&A processing for student_id: {student_id}, session_id: {session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error during Q&A processing")
        
        try:
            updated_difficulty_level=adapt_difficult_obj.adapt_difficulty(response["confidence_level"], interaction_q["difficulty_level"])
            student_response_time=adapt_difficult_obj.calculate_time_difference_in_minutes(answer_time,interaction_q["interaction_details"]["query_time"])
            session_manager.update_interaction(student_id, session_id,request.interaction_id,request.answer,updated_difficulty_level,student_response_time,response["confidence_level"],response["result"])

            random_uuid = uuid.uuid4()
            new_interaction_id = random_uuid.hex
            session_manager.update_session(student_id, session_id, {
                    "interaction_id": new_interaction_id,
                    "question": response["follow_up_question"],
                    "answer": "",
                    "answer_time":0,
                    "query_time": datetime.datetime.now().isoformat(),
                    "correct_answer": "not answered",
                    "confidence_level": 0
                })
        
        except Exception as e:
            logger.error(f"Error updating session for student_id: {student_id}, session_id: {session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error updating session")
        
        return {"message": {"interaction_id": new_interaction_id, "question": response["follow_up_question"]}}

    except HTTPException as http_error:
        logger.error(f"HTTP error occurred: {http_error.detail}")
        raise http_error
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/sessions/{student_id}/{session_id}")
async def get_session_state(student_id: str, session_id: str):
    try:
        logger.info(f"Received request to get session state for student_id: {student_id}, session_id: {session_id}")
        
        session = session_manager.get_session(student_id, session_id)
        if not session:
            logger.warning(f"Session not found for student_id: {student_id}, session_id: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.debug(f"Session found for student_id: {student_id}, session_id: {session_id}")

        try:
            response = session_manager.session_details(student_id, session_id)
            logger.debug(f"Session details retrieved successfully for student_id: {student_id}, session_id: {session_id}")
        except Exception as e:
            logger.error(f"Error retrieving session details for student_id: {student_id}, session_id: {session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving session details")

        return {
            "session state": response["session_state"],
            "session progress": response["session_progress"],
            "number of interactions": response["number_of_interactions"],
            "difficulty level": response["difficulty_level"],
            "student level": response["student_level"],
            "average confidence level": response["avg_confidence_level"],
            "student average answer time": response["avg_answer_time"],
            "learning goals": response["learning_goals"]
        }

    except HTTPException as http_error:
        logger.error(f"HTTP error occurred: {http_error.detail}")
        raise http_error
    except Exception as e:
        logger.error(f"Unexpected error occurred while retrieving session state: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/sessions/{student_id}/{session_id}/recommendations")
async def get_recommendations(student_id: str, session_id: str):
    try:
        logger.info(f"Received request to get recommendations for student_id: {student_id}, session_id: {session_id}")
        session = session_manager.get_session(student_id, session_id)
        if not session:
            logger.warning(f"Session not found for student_id: {student_id}, session_id: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.debug(f"Session found for student_id: {student_id}, session_id: {session_id}")
        try:
            response = session_manager.session_details(student_id, session_id)
            logger.debug(f"Session details retrieved successfully for student_id: {student_id}, session_id: {session_id}")
        except Exception as e:
            logger.error(f"Error retrieving session details for student_id: {student_id}, session_id: {session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving session details")
        
        try:
            
            ans = recommend_question.recommend_next(
                learning_goals=response["learning_goals"],
                student_level=response["student_level"],
                difficulty_level=response["difficulty_level"],
                avg_confidence_level=response["avg_confidence_level"],
                history=response["interactions"]
            )
            logger.debug(f"Recommendations generated for student_id: {student_id}, session_id: {session_id}")
        except Exception as e:
            logger.error(f"Error generating recommendations for student_id: {student_id}, session_id: {session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error generating recommendations")

        return {"recommended questions": ans}

    except HTTPException as http_error:
        logger.error(f"HTTP error occurred: {http_error.detail}")
        raise http_error
    except Exception as e:
        logger.error(f"Unexpected error occurred while getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@app.get("/analytics/student/{student_id}")
async def get_student_analytics(student_id: str):
    try:
        
        logger.info(f"Retrieving analytics for student {student_id}")
        
        student_sessions = session_manager.student_details(student_id)
        
        if not student_sessions:
            logger.warning(f"No sessions found for student {student_id}")
            raise HTTPException(status_code=404, detail="Student not found or no sessions available")
        
        total_sessions = len(student_sessions)
        total_interactions = sum(len(session["interactions"]) for session in student_sessions)
        
        total_correct_answers = sum(1 for session in student_sessions for interaction in session["interactions"] if interaction["correct_answer"] == "correct")
        total_incorrect_answers = sum(1 for session in student_sessions for interaction in session["interactions"] if interaction["correct_answer"] == "incorrect")
        total_partially_correct_answers = sum(1 for session in student_sessions for interaction in session["interactions"] if interaction["correct_answer"] == "partially correct")
        
        avg_confidence_level = np.mean([interaction["confidence_level"] for session in student_sessions for interaction in session["interactions"]])
        
        mastery = defaultdict(int)
        misconceptions = defaultdict(int)
        
        for session in student_sessions:
            for interaction in session["interactions"]:
                question = interaction["question"]
    
                if interaction["correct_answer"] != "correct":
                    misconceptions[question] += 1
                else:
                    mastery[question] += 1
        
        avg_interaction_duration = np.mean([interaction["answer_time"] for session in student_sessions for interaction in session["interactions"]])
    
        student_analytics = {
            "total_sessions": total_sessions,
            "total_interactions": total_interactions,
            "total_correct_answers": total_correct_answers,
            "total_incorrect_answers": total_incorrect_answers,
            "total_partially_correct_answers": total_partially_correct_answers,
            "avg_confidence_level": avg_confidence_level,
            "avg_interaction_duration": avg_interaction_duration,
            "concept_mastery": dict(mastery),
            "misconceptions": dict(misconceptions)
        }

        logger.info(f"Student analytics successfully retrieved for student {student_id}")
        return student_analytics

    except Exception as e:
        logger.error(f"Error retrieving analytics for student {student_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/analytics/aggregate")
async def get_aggregate_analytics():
    try:
       
        logger.info("Retrieving aggregate analytics for all students")
        
        all_sessions = session_manager.all_details()
        if not all_sessions:
            logger.warning("No sessions available for aggregate analytics")
            raise HTTPException(status_code=404, detail="No sessions found")
        
        
        logger.info(f"all_sessions type: {type(all_sessions)}")
        
        total_sessions = 0
        total_interactions = 0
        total_confidence_levels = 0
        total_answer_time = 0
        common_misconceptions = defaultdict(int)
        difficulty_progression = defaultdict(int)
        student_count = len(all_sessions)
        for student_id, student_sessions in all_sessions.items():
            logger.info(f"Processing sessions for student {student_id}")
            
            for session in student_sessions:
                total_sessions += 1
                total_interactions += len(session["interactions"])
                
                
                total_confidence_levels += sum(interaction["confidence_level"] for interaction in session["interactions"])
                total_answer_time += sum(interaction["answer_time"] for interaction in session["interactions"])

                
                for interaction in session["interactions"]:
                    if interaction["correct_answer"] != "correct":
                        common_misconceptions[interaction["question"]] += 1
                
                # Track difficulty progression
                difficulty_progression[session["difficulty_level"]] += 1
        
        
        avg_confidence_level = total_confidence_levels / total_interactions if total_interactions > 0 else 0
        avg_interaction_duration = total_answer_time / total_interactions if total_interactions > 0 else 0
        
        aggregate_analytics = {
            "number_of_students": student_count,
            "total_sessions": total_sessions,
            "total_interactions": total_interactions,
            "difficulty_progression": dict(difficulty_progression),
            "avg_interaction_duration": avg_interaction_duration,
            "avg_confidence_level": avg_confidence_level,
            "common_misconceptions": dict(common_misconceptions)
        }

        logger.info("Aggregate analytics successfully retrieved")
        return aggregate_analytics

    except Exception as e:
        logger.error(f"Error retrieving aggregate analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
