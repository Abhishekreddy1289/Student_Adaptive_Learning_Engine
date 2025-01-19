from uitils.logger import custom_logger
from datetime import datetime

logger = custom_logger.get_logger()

class Uitils:
    def adapt_difficulty(self, confidence_level, current_difficulty_level):
        try:
            if confidence_level > 3:
                if current_difficulty_level == "easy":
                    return "medium"
                elif current_difficulty_level == "medium":
                    return "hard"
                else:
                    return "hard"
            
            elif confidence_level < 2:
                if current_difficulty_level == "hard":
                    return "medium"
                elif current_difficulty_level == "medium":
                    return "easy"
                else:
                    return "easy"
            else:
                # Keep the same level
                return current_difficulty_level
        except Exception as e:
            logger.error(f"Error adapting difficulty level: {str(e)}")
            raise Exception(f"Error adapting difficulty level: {str(e)}")
        
    def calculate_time_difference_in_minutes(self,answer_time, query_time):
        format = "%Y-%m-%dT%H:%M:%S.%f"
        
        dt1 = datetime.strptime(answer_time, format)
        dt2 = datetime.strptime(query_time, format)
        
        time_diff = (dt1 - dt2).total_seconds()
        return time_diff / 60  # Convert seconds to minute s