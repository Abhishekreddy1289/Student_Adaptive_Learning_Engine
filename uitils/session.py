import json
import statistics
from uitils.logger import custom_logger

logger = custom_logger.get_logger()

class SessionManager:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        logger.info(f"SessionManager initialized with file path: {json_file_path}")
    
    def load_sessions(self):
        """Loads existing sessions from the JSON file."""
        try:
            with open(self.json_file_path, 'r') as f:
                content = f.read().strip()
                if not content:
                    logger.info("Session file is empty. Returning empty dictionary.")
                    return {}  # Return an empty dictionary if file is empty
                logger.info("Loaded session data successfully.")
                return json.loads(content)  # Load the valid JSON content
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading sessions from file: {str(e)}")
            return {}  # If file doesn't exist or has invalid JSON, return an empty dictionary

    def save_sessions(self, sessions):
        """Saves the updated session data back to the JSON file."""
        try:
            with open(self.json_file_path, 'w') as f:
                json.dump(sessions, f, indent=4)
                logger.info("Sessions data saved successfully.")
        except Exception as e:
            logger.error(f"Error saving sessions to file: {str(e)}")

    def insert_session(self, student_id, session_data):
        """Inserts a new session for a student."""
        try:
            sessions = self.load_sessions()

            # Ensure student entry exists
            if student_id not in sessions:
                sessions[student_id] = {}

            session_id = session_data["session_id"]

            # Insert the new session
            if session_id not in sessions[student_id]:
                sessions[student_id][session_id] = session_data
                logger.info(f"New session {session_id} inserted for student {student_id}.")
            else:
                logger.warning(f"Session {session_id} already exists for student {student_id}. No changes made.")

            # Save updated sessions
            self.save_sessions(sessions)
            return "Session Started Successfully.🙂"
        except Exception as e:
            logger.error(f"Error inserting session for student {student_id}: {str(e)}")
            return "Please Try After Sometime."
        
    def update_interaction(self, student_id, session_id, interaction_id, answer, updated_difficulty_level, student_response_time, confidence_level, result):
        """Updates an interaction for a student session."""
        try:
            sessions = self.load_sessions()

            if student_id in sessions and session_id in sessions[student_id]:

                
                interactions = sessions[student_id][session_id]["interactions"]
                interaction_found = False
                for interaction in interactions:
                    if interaction["interaction_id"] == interaction_id:
                        
                        interaction["answer"] = answer
                        interaction["answer_time"] = student_response_time 
                        interaction["confidence_level"] = confidence_level
                        interaction["correct_answer"] = result 

                        interaction_found = True
                        logger.info(f"Interaction {interaction_id} updated for session {session_id} of student {student_id}.")
                        break

                if not interaction_found:
                    logger.warning(f"Interaction with ID {interaction_id} not found for session {session_id} of student {student_id}.")
                    return "Interaction ID not found."

                # Recalculate session progress and state
                history = sessions[student_id][session_id]["interactions"]
                session_progress = (len(history) / 100) * 100 if len(history) < 100 else 100
                session_state = "completed" if len(history) >= 100 else "in-progress"

                # Update the session details
                sessions[student_id][session_id]["difficulty_level"] = updated_difficulty_level
                sessions[student_id][session_id]["session_progress"] = session_progress
                sessions[student_id][session_id]["session_state"] = session_state

                logger.info(f"Session {session_id} for student {student_id} updated with new progress and state.")
            
            else:
                logger.warning(f"Session {session_id} for student {student_id} does not exist.")
                return "Session or student does not exist."

            # Save the updated sessions data
            self.save_sessions(sessions)
            return "Updated successfully. 🙂"

        except Exception as e:
            logger.error(f"Error updating interaction for student {student_id}, session {session_id}: {str(e)}")
            return "Please try again later. 😞"


    def update_session(self, student_id, session_id, new_interaction):
        """Updates an existing session with a new interaction."""
        try:
            sessions = self.load_sessions()

            # Ensure student and session exist
            if student_id in sessions and session_id in sessions[student_id]:
                sessions[student_id][session_id]["interactions"].append(new_interaction)
                logger.info(f"New interaction added to session {session_id} for student {student_id}.")
            else:
                logger.warning(f"Session {session_id} for student {student_id} does not exist.")
            
            # Save updated sessions
            self.save_sessions(sessions)
        except Exception as e:
            logger.error(f"Error updating session for student {student_id}, session {session_id}: {str(e)}")

    def get_session(self, student_id, session_id):
        """Retrieve a specific session by session_id for a given student."""
        try:
            sessions = self.load_sessions()
            session = sessions.get(student_id, {}).get(session_id)
            logger.info(f"Retrieved session {session_id} for student {student_id}.")
            return session
        except Exception as e:
            logger.error(f"Error retrieving session {session_id} for student {student_id}: {str(e)}")
            return None

    def session_details(self, student_id, session_id):
        """Get detailed session information for a specific student."""
        try:
            sessions = self.load_sessions()
            if student_id not in sessions:
                sessions[student_id] = {}

            if session_id in sessions[student_id]:
                history = sessions[student_id][session_id]["interactions"]
                session_progress = sessions[student_id][session_id]["session_progress"]
                session_state = sessions[student_id][session_id]["session_state"]
                difficulty_level = sessions[student_id][session_id]["difficulty_level"]
                student_level = sessions[student_id][session_id]["student_level"]
                learning_goals = sessions[student_id][session_id]["learning_goals"]
                number_of_interactions = len(history)
                
                try:
                    avg_confidence_level = statistics.mean([rating["confidence_level"] for rating in history])
                except:
                    avg_confidence_level = 0
                
                try:
                    avg_answer_time = statistics.mean([res["answer_time"] for res in history])
                except:
                    avg_answer_time = 0
                
                response = {
                    "session_state": session_state,
                    "session_progress": session_progress,
                    "number_of_interactions": number_of_interactions,
                    "difficulty_level": difficulty_level,
                    "student_level": student_level,
                    "avg_confidence_level": avg_confidence_level,
                    "avg_answer_time": avg_answer_time,
                    "learning_goals": learning_goals,
                    "interactions":history
                }
                logger.info(f"Retrieved detailed session information for session {session_id} of student {student_id}.")
                return response
        except Exception as e:
            logger.error(f"Error retrieving session details for student {student_id}, session {session_id}: {str(e)}")
            return None
        
    def interaction_details(self, student_id, session_id, interaction_id):
        """Get detailed session information for a specific student."""
        try:
            sessions = self.load_sessions()
            if student_id not in sessions:
                print(f"Student {student_id} not found, adding to sessions.")  # Debug print
                sessions[student_id] = {}
            
            if session_id in sessions[student_id]:
                history = sessions[student_id][session_id]["interactions"]
                session_progress = sessions[student_id][session_id]["session_progress"]
                session_state = sessions[student_id][session_id]["session_state"]
                difficulty_level = sessions[student_id][session_id]["difficulty_level"]
                student_level = sessions[student_id][session_id]["student_level"]
                learning_goals = sessions[student_id][session_id]["learning_goals"]
                number_of_interactions = len(history)
                
                try:
                    avg_student_rating = statistics.mean([rating["interaction_rating"] for rating in history])
                except:
                    avg_student_rating = 0

                try:
                    avg_response_time = statistics.mean([res["response_time"] for res in history])
                except:
                    avg_response_time = 0
                
                interaction_details = next(
                    (interaction for interaction in history if interaction["interaction_id"] == interaction_id),
                    None
                )

                if interaction_details is None:
                    raise ValueError(f"Interaction with ID {interaction_id} not found.")

                response = {
                    "session_state": session_state,
                    "session_progress": session_progress,
                    "number_of_interactions": number_of_interactions,
                    "difficulty_level": difficulty_level,
                    "student_level": student_level,
                    "avg_student_rating": avg_student_rating,
                    "avg_response_time": avg_response_time,
                    "learning_goals": learning_goals,
                    "interactions": history,
                    "interaction_details":interaction_details
                }
                logger.info(f"Retrieved detailed session information for session {session_id} of student {student_id}.")
                return response

        except Exception as e:
            logger.error(f"Error retrieving session details for student {student_id}, session {session_id}: {str(e)}")
            return None
        
    def student_details(self, student_id):
        """Get detailed session information for all sessions of a specific student."""
        try:
            sessions = self.load_sessions()

            if student_id not in sessions:
                logger.warning(f"Student {student_id} not found in sessions data.")
                return None

            student_sessions = sessions[student_id]
            all_session_details = []

            for session_id, session_data in student_sessions.items():
                history = session_data["interactions"]
                session_progress = session_data["session_progress"]
                session_state = session_data["session_state"]
                difficulty_level = session_data["difficulty_level"]
                student_level = session_data["student_level"]
                learning_goals = session_data["learning_goals"]
                number_of_interactions = len(history)

                try:
                    avg_confidence_level = statistics.mean([rating["confidence_level"] for rating in history])
                except:
                    avg_confidence_level = 0

                try:
                    avg_answer_time = statistics.mean([res["answer_time"] for res in history])
                except:
                    avg_answer_time = 0

                session_detail = {
                    "session_id": session_id,
                    "session_state": session_state,
                    "session_progress": session_progress,
                    "number_of_interactions": number_of_interactions,
                    "difficulty_level": difficulty_level,
                    "student_level": student_level,
                    "avg_confidence_level": avg_confidence_level,
                    "avg_answer_time": avg_answer_time,
                    "learning_goals": learning_goals,
                    "interactions": history
                }
                all_session_details.append(session_detail)

            logger.info(f"Retrieved detailed session information for student {student_id}.")
            return all_session_details

        except Exception as e:
            logger.error(f"Error retrieving student details for student {student_id}: {str(e)}")
            return None
        
    def all_details(self):
        """Get detailed session information for all students and their sessions."""
        try:
            sessions = self.load_sessions()
            all_students_details = {}

            for student_id, student_sessions in sessions.items():
                all_session_details = []

                for session_id, session_data in student_sessions.items():
                    history = session_data["interactions"]
                    session_progress = session_data["session_progress"]
                    session_state = session_data["session_state"]
                    difficulty_level = session_data["difficulty_level"]
                    student_level = session_data["student_level"]
                    learning_goals = session_data["learning_goals"]
                    number_of_interactions = len(history)

                    try:
                        avg_confidence_level = statistics.mean([rating["confidence_level"] for rating in history])
                    except:
                        avg_confidence_level = 0

                    try:
                        avg_answer_time = statistics.mean([res["answer_time"] for res in history])
                    except:
                        avg_answer_time = 0

                    session_detail = {
                        "session_id": session_id,
                        "session_state": session_state,
                        "session_progress": session_progress,
                        "number_of_interactions": number_of_interactions,
                        "difficulty_level": difficulty_level,
                        "student_level": student_level,
                        "avg_confidence_level": avg_confidence_level,
                        "avg_answer_time": avg_answer_time,
                        "learning_goals": learning_goals,
                        "interactions": history
                    }
                    all_session_details.append(session_detail)

                all_students_details[student_id] = all_session_details

            logger.info("Retrieved detailed session information for all students.")
            return all_students_details

        except Exception as e:
            logger.error(f"Error retrieving all session details: {str(e)}")
            return None
            
    def get_all_session_ids(self, student_id):
        """Retrieve a list of all session IDs for a specific student."""
        try:
            sessions = self.load_sessions()

            # Check if the student exists
            if student_id in sessions:
                session_ids = list(sessions[student_id].keys())
                logger.info(f"Retrieved all session IDs for student {student_id}.")
                return session_ids
            else:
                logger.warning(f"Student {student_id} not found in sessions data.")
                return []  # Return an empty list if the student does not exist

        except Exception as e:
            logger.error(f"Error retrieving session IDs for student {student_id}: {str(e)}")
            return []