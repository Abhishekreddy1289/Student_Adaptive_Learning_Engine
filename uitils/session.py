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

    def update_session(self, student_id, session_id, new_interaction,difficulty_level):
        """Updates an existing session with a new interaction."""
        try:
            sessions = self.load_sessions()

            # Ensure student and session exist
            if student_id in sessions and session_id in sessions[student_id]:
                sessions[student_id][session_id]["interactions"].append(new_interaction)
                logger.info(f"New interaction added to session {session_id} for student {student_id}.")
            else:
                logger.warning(f"Session {session_id} for student {student_id} does not exist.")
            
            # Calculate session progress and state
            if session_id in sessions[student_id]:
                history = sessions[student_id][session_id]["interactions"]
                if len(history) > 0 and len(history) < 100:
                    session_progress = (len(history) / 100) * 100
                    session_state = "in-progress"
                else:
                    session_progress = 100
                    session_state = "completed"

                # Update the difficulty level
                sessions[student_id][session_id]["difficulty_level"] = difficulty_level
                sessions[student_id][session_id]["session_progress"] = session_progress
                sessions[student_id][session_id]["session_state"] = session_state
                logger.info(f"Difficulty level updated for session {session_id} for student {student_id}.")
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
            # Check if the student exists in the sessions data
            if student_id not in sessions:
                sessions[student_id] = {}
            # If the session exists, return session details
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
                
                response = {
                    "session_state": session_state,
                    "session_progress": session_progress,
                    "number_of_interactions": number_of_interactions,
                    "difficulty_level": difficulty_level,
                    "student_level": student_level,
                    "avg_student_rating": avg_student_rating,
                    "avg_response_time": avg_response_time,
                    "learning_goals": learning_goals,
                    "interactions":history
                }
                logger.info(f"Retrieved detailed session information for session {session_id} of student {student_id}.")
                return response
        except Exception as e:
            logger.error(f"Error retrieving session details for student {student_id}, session {session_id}: {str(e)}")
            return None
