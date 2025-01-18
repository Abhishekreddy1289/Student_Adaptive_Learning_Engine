from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import List, Dict
import uuid
import time
import datetime
from uitils.session import SessionManager
from azure_openai.validate import Validate
from azure_openai.repharse import Rephrase
from azure_openai.student_qna import StudentQnA
from azure_openai.validate import Validate
from azure_openai.recommendations import RecommendationsQuestions
from uitils.logger import custom_logger
from config import gpt4_model,api_key,api_version,openai_type,azure_endpoint

app = FastAPI()

session_manager=SessionManager('student_sessions.json')
validate_response=Validate(gpt4_model, api_key, azure_endpoint, api_version, openai_type)
rephrase_query=Rephrase(gpt4_model, api_key, azure_endpoint, api_version, openai_type)
student_inter=StudentQnA(gpt4_model, api_key, azure_endpoint, api_version, openai_type)
validate_score=Validate(gpt4_model, api_key, azure_endpoint, api_version, openai_type)
recommend_question=RecommendationsQuestions(gpt4_model, api_key, azure_endpoint, api_version, openai_type)
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
    query: str

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
        
        session_data_1 = {
            "session_id": session_id,
            "student_id": student_id,
            "student_level": student_level,
            "difficulty_level": difficulty_level,
            "learning_goals": learning_goals,
            "session_state": "not started yet",
            "session_progress": 0,
            "session_start_time": datetime.datetime.now().isoformat(),
            "interactions": []
        }
        
        logger.info(f"Session data prepared for student {student_id} with session ID {session_id}")
        
        response = session_manager.insert_session(student_id, session_data_1)
        # Log the successful session creation
        logger.info(f"Session successfully created with session ID {session_id} for student {student_id}")
        
        return {"message": response, "session_id": session_id}

    except Exception as e:
        # Log the error if something goes wrong
        logger.error(f"Error occurred while creating session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/sessions/{student_id}/{session_id}/interactions")
async def track_interaction(student_id: str, session_id: str, request: InteractionRequest):
    try:
        logger.info(f"Received request to track interaction for student_id: {student_id}, session_id: {session_id}")
        
        session = session_manager.get_session(student_id, session_id)
        if not session:
            logger.warning(f"Session not found for student_id: {student_id}, session_id: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.debug(f"Session found for student_id: {student_id}, session_id: {session_id}")
        s_time = time.time()
        try:
            rephrase_q = rephrase_query.followup_query(request.query)
            logger.debug(f"Rephrased query: {rephrase_q}")
        except Exception as e:
            logger.error(f"Error while rephrasing query: {str(e)}")
            raise HTTPException(status_code=500, detail="Error processing the query")

        try:
            session_res=session_manager.session_details(student_id, session_id)
            # history, student_level, difficulty_level = session_manager.read_history(student_id, session_id)
            logger.debug(f"Session history read successfully for student_id: {student_id}, session_id: {session_id}")
        except Exception as e:
            logger.error(f"Error while reading history for student_id: {student_id}, session_id: {session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving session history")
        
        logger.debug(f"Current difficulty level: {session_res["difficulty_level"]}")
        try:
            answer = student_inter.student_qna_fun(rephrase_q, session_res["student_level"], session_res["interactions"])
            logger.debug(f"Answer generated: {answer}")
        except Exception as e:
            logger.error(f"Error during Q&A processing for student_id: {student_id}, session_id: {session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error during Q&A processing")

        end_time = time.time() - s_time
        logger.debug(f"Interaction processed in {end_time:.2f} seconds")
        
        try:
            interaction_score = validate_score.student_score(rephrase_q, answer, session_res["interactions"])
            logger.debug(f"Interaction score calculated: {interaction_score}")
        except Exception as e:
            logger.error(f"Error during interaction scoring for student_id: {student_id}, session_id: {session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error during interaction scoring")
        
        try:
            difficulty_level = validate_score.adapt_difficulty(interaction_score, {session_res["difficulty_level"]})
            logger.debug(f"Updated difficulty level: {difficulty_level}")
        except Exception as e:
            logger.error(f"Error during difficulty level adaptation for student_id: {student_id}, session_id: {session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error adjusting difficulty level")
        
        random_uuid = uuid.uuid4()
        interaction_id = random_uuid.hex
        logger.debug(f"Generated interaction ID: {interaction_id}")
        
        try:
            session_manager.update_session(student_id, session_id, {
                "interaction_id": interaction_id,
                "query": request.query,
                "rephrased_query": rephrase_q,
                "answer": answer,
                "interaction_time": datetime.datetime.now().isoformat(),
                "response_time": end_time,
                "interaction_rating": interaction_score
            },difficulty_level)
            logger.info(f"Session updated with interaction_id {interaction_id} for student {student_id}")
        except Exception as e:
            logger.error(f"Error updating session for student_id: {student_id}, session_id: {session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error updating session")
        
        return {"message": {"interaction_id": interaction_id, "answer": answer}}

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
            "avg student rating": response["avg_student_rating"],
            "avg response time": response["avg_response_time"],
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
            ans = recommend_question.recommend_questions(
                learning_goals=response["learning_goals"],
                rating=response["avg_student_rating"],
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