from loguru import logger
import os
from datetime import datetime

class CustomLogger:
    def __init__(self, log_directory: str = "logs", log_filename: str = "app", rotation: str = "1 day"):
        """
        Initialize the logger with custom settings.
        :param log_directory: Directory where log files will be stored.
        :param log_filename: The base filename for logs (without date).
        :param rotation: The rotation pattern (e.g., '1 day', '500 MB').
        """
        # Create log directory if it does not exist
        os.makedirs(log_directory, exist_ok=True)
        
        # Use current date to create a date-based filename
        current_date = datetime.now().strftime("%Y-%m-%d")  # Get current date in YYYY-MM-DD format
        log_filename_with_date = f"{log_filename}_{current_date}.log"
        log_path = os.path.join(log_directory, log_filename_with_date)
        
        # Configure the logger
        self.logger = logger
        self.logger.add(log_path, rotation=rotation)  # Log rotation every day
        
    def get_logger(self):
        """
        Return the configured logger instance.
        """
        return self.logger

# Initialize the logger
custom_logger = CustomLogger(log_directory="logs", log_filename="app")
logger = custom_logger.get_logger()
logger.info("Logger has been successfully initialized")