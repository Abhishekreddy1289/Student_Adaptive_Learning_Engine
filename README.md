# Student Adaptive Learning Engine

This project provides an adaptive learning system where student interactions are tracked, and the system dynamically adjusts to the student’s learning progress. The engine uses FastAPI to create and manage student sessions, while Azure OpenAI services generate personalized queries, evaluate student responses, and provide follow-up queries and recommendations. The system is designed to help students progress by identifying knowledge gaps and offering next steps based on their interaction history.

## Requirements

To set up the environment and install the required dependencies, follow these steps:

### 1. Set Up a Virtual Environment

It’s recommended to use a virtual environment to manage dependencies for the project.

For Windows:
```bash
# Set-up environment
python -m venv student_env
.\student_env\Scripts\activate
```
### 2. Install Dependencies

After activating the virtual environment, install the required dependencies from the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 3. Set Up Configuration

Ensure you configure the required API keys and model settings. These configurations should be placed in a `config.py` file:

```python
# config.py
gpt4_model = "your-gpt4-model"
api_key = "your-azure-api-key"
api_version = "your-azure-api-version"
openai_type = "your-openai-type"
azure_endpoint = "your-azure-endpoint"
```

### 4. Run the Application

Once you have installed the dependencies and configured the environment, you can start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```

This will start the FastAPI server, and you can access the API documentation at:

```
http://localhost:8000/docs
```

## API Overview

### 1. **POST /sessions**

#### **Purpose**:
Creates a new learning session for a student, including their learning goals, level, and difficulty settings. The engine will generate an initial question based on the student’s selected topics.

#### **Request Body**:
```json
{
  "student_id": "123",
  "student_level": "beginner",
  "learning_goals": ["Improve English", "Practice Grammar"]
}
```

- **student_id**: A unique identifier for the student.
- **student_level**: The level of the student, which can be `"beginner"`, `"intermediate"`, or `"advanced"`.
- **learning_goals**: A list of goals the student aims to achieve during the session.

#### **Response**:
```json
{
  "message": "Session created successfully.",
  "session_id": "abcdef123456",
  "interaction_id": "interaction123456",
  "question": "What is the past tense of 'run'?"
}
```

- **message**: A confirmation message indicating whether the session creation was successful.
- **session_id**: A unique session identifier for tracking the student's progress.
- **interaction_id**: A unique identifier for the first interaction.
- **question**: The first question generated by the engine based on the student’s goals and level.

#### **Usage**:
This endpoint starts a learning session for a student by creating a session with the specified learning goals, student level, and difficulty level. The system generates an initial question for the student to answer based on their goals and level.

---

### 2. **POST /sessions/{student_id}/{session_id}/interactions**

#### **Purpose**:
Tracks an interaction between the student and the system, where the student answers a query generated by the system. The system evaluates the student's response, adjusts the difficulty, and provides a follow-up question.

#### **Request Body**:
```json
{
  "interaction_id": "interaction123456",
  "answer": "The past tense of 'run' is 'ran'."
}
```

- **interaction_id**: The unique identifier for the current interaction.
- **answer**: The student’s answer to the query provided by the system.

#### **Response**:
```json
{
  "interaction_id": "interaction789012",
  "follow_up_question": "What is the past tense of 'go'?"
}
```

- **interaction_id**: A new unique identifier for the next interaction.
- **follow_up_question**: A new question generated based on the student’s response and learning goals.

#### **Usage**:
This endpoint tracks a student’s response to the query, evaluates their answer, adjusts the difficulty level based on the confidence in the answer, and provides a follow-up question tailored to the student's progress and learning goals.

---

### 3. **GET /sessions/{student_id}/{session_id}**

#### **Purpose**:
Fetches the current state of a specific learning session, including progress, difficulty level, and session details.

#### **Response**:
```json
{
  "session_state": "in progress",
  "session_progress": 50,
  "number_of_interactions": 5,
  "difficulty_level": "medium",
  "student_level": "beginner",
  "avg_student_rating": 4.2,
  "avg_response_time": 2.3,
  "learning_goals": ["Improve English"]
}
```

- **session_state**: The current state of the session (e.g., "in progress").
- **session_progress**: The progress made in the session (e.g., 50%).
- **number_of_interactions**: The number of interactions that have occurred.
- **difficulty_level**: The current difficulty level for the session.
- **student_level**: The student’s level (e.g., "beginner").
- **avg_student_rating**: The average rating of the student’s performance.
- **avg_response_time**: The average time it took to respond to the student’s queries.
- **learning_goals**: The list of goals the student is working toward.

#### **Usage**:
This endpoint is used to get an overview of the student's learning session, allowing the student or an administrator to view how the session is progressing. It provides a snapshot of the session's state, interaction history, and performance metrics.

---

### 4. **GET /sessions/{student_id}/{session_id}/recommendations**

#### **Purpose**:
Generates personalized next steps and identifies knowledge gaps for the student based on their progress, session history, and learning goals. This helps guide the student to their next steps in the learning journey.

#### **Response**:
```json
{
  "recommended_next_steps": [
    "Review past tenses of irregular verbs.",
    "Practice more grammar exercises related to tenses."
  ],
  "knowledge_gaps": [
    "Past tenses of irregular verbs."
  ]
}
```

- **recommended_next_steps**: A list of personalized next steps for the student based on their learning history.
- **knowledge_gaps**: A list of identified knowledge gaps that the student should focus on to improve.

#### **Usage**:
This endpoint provides personalized next steps and identifies knowledge gaps based on the student's learning progress, interaction history, and goals. The system helps guide the student to areas where they need improvement, ensuring that their learning journey is optimized for their needs.

---

## Workflow

1. **Create a Session**:
   - When a student logs in or starts their learning journey, a session is created using the `/sessions` endpoint. The session includes basic information such as the student's learning goals and their current level. The system generates an initial query for the student to answer.

2. **Track Interactions**:
   - During the session, the student answers questions generated by the system. These interactions are tracked using the `/sessions/{student_id}/{session_id}/interactions` endpoint. The system evaluates the student’s response, adapts the difficulty level, and provides a follow-up question to keep the student progressing.

3. **Monitor Progress**:
   - At any time, the session state, progress, and performance metrics can be retrieved using the `/sessions/{student_id}/{session_id}` endpoint. This helps monitor how well the student is progressing in their learning journey.

4. **Receive Recommendations**:
   - The system can suggest additional resources, questions, or steps for the student to explore based on their learning history and progress using the `/sessions/{student_id}/{session_id}/recommendations` endpoint. This helps the student continue their learning by addressing knowledge gaps and focusing on the most important areas.

---

## Conclusion

The **Student Adaptive Learning Engine** is a powerful tool designed to enhance the learning experience through dynamic, personalized sessions. By leveraging Azure OpenAI services, it provides the ability to generate personalized queries, evaluate student responses, adapt difficulty levels, and offer relevant next steps for continued learning. This system is ideal for creating an interactive, adaptive, and personalized learning environment for students at various skill levels.