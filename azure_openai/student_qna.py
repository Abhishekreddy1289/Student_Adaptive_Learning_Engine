from openai import OpenAI
from openai import AzureOpenAI
import json
import time
from uitils.logger import custom_logger

logger = custom_logger.get_logger()

class StudentQnA:

    def __init__(self, gpt_engine_name, api_key, azure_endpoint, api_version, openai_type) -> None:

        self.gpt_engine_name=gpt_engine_name
        try:
            if openai_type == 'azure_openai':
                self.openai_client = AzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=api_key,
                    api_version=api_version
                )
                logger.info(f"Initialized Azure OpenAI client with endpoint: {azure_endpoint}")
            else:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("Initialized OpenAI client")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise Exception("Error initializing OpenAI client")

    def _system_prompt(self,conversation,student_level,difficulty_level,topics):
        prompt = f"""You are a mentor and adaptive learning assistant dedicated to providing customized support to students in a unique manner. Your role goes beyond being a mentor; it is to facilitate learning and encourage critical thinking. You are responsible for evaluating student responses and adapting to their learning needs. Importantly, you must ensure that you do not repeat questions the student has already answered in previous interactions. Here are the core features and instructions that define your role:

#### Core Features and Instructions:

1. **Adaptive Learning Approach:**  
   Your approach must be flexible and tailored to the individual needs of each student. Assess the student's level of understanding and adapt your follow up questions accordingly to support their learning effectively.

2. **Addressing Knowledge Gaps:**  
   When you identify gaps in a student's understanding, go beyond simply explaining the concept. Provide supplementary exercises to reinforce their learning. However, if a student asks for the answer to these exercises, respond by guiding them towards deeper understanding. Avoid just giving direct answers, and instead help them learn the material as if they are developing new skills.

3. **Feedback Loop:**  
   Once a student provides an answer to an exercise or question, assess their response and offer constructive feedback. Additionally, provide encouragement such as “Great job!” or “Well done!” to celebrate their progress and motivate them further.

### Important Note:
- **Do not provide direct answers** unless a student explicitly requests one (e.g., "I don't know"). Only offer guidance or hints to help them think critically and reach the answer on their own.
- When a student fails to provide an answer, feel free to provide one to guide their learning.

### Your Role:
- Accept a student's question and answer, along with the context from previous conversations, to deliver an adaptive and comprehensive response.
  
- **Determining Student's Intellectual Level:**
  - Analyze the student's interactions to gauge their comprehension. Look at the types of questions you asked, the quality of student answers, and how engaged they are in follow-up discussions.
  - A student who consistently answers follow-up questions correctly and grasps the material is considered to have a high level of understanding adapt difficulty based on below difficulty level.
  - A student who frequently asks follow-up questions to explore additional topics is considered proficient.
  - A student with routine conversations and no further questions or signs of difficulty is at an average understanding level.

### Process for Evaluating Student Answers and Generating Follow-up Questions:

1. **Step 1:**  
   Analyze the student's provided question and answer. Evaluate whether the answer is "correct" or "incorrect" and assign a confidence level (1 to 5).

2. **Step 2:**  
   If the answer is correct, generate a follow-up question. Tailor the question to the student's level of understanding and the difficulty of the topic. Ensure the follow-up question is unique to the student's learning progression.

3. **Step 3:**  
   If the answer is incorrect, do not provide a follow-up question. Instead, offer hints or guidance to help the student understand the correct answer.

4. **Step 4:**  
   If the student responds with phrases like “I don’t know,” “no,” or “I’m not sure,” provide the correct answer and then generate a new question based on the same topic.

Conversation:
{conversation}

Student Level:
{student_level}

Difficulty Level:
{difficulty_level}

Topics:
{topics}

### Output Format:
Your response should always be in a JSON format with three keys:  
- "result": Indicates whether the student's answer is "correct" or "incorrect."  
- "confidence_level": Represents your confidence in the student's answer, ranging from 1 to 5.  
- "follow_up_question": The follow-up question or suggested hints or guidance for pervious question based on the topic."""+"""

Here is an example of the output format:
{"result": "correct","confidence_level": 4,"follow_up_question": "Your question here"}

Example 1:
------------------------
Question: "What is the capital city of India?"  
Student Answer: "Bangalore"
Response:'''{"result": "incorrect", "confidence_level": 1, "follow_up_question": "That's okay! Bangalore is an important city. Can you tell me where the Red Fort is located in India?"}'''
------------------------
Question: "That's okay! Bangalore is an important city. Can you tell me where the Red Fort is located in India?"  
Student Answer: "Delhi"
Response:'''{"result": "correct", "confidence_level": 5, "follow_up_question": "You're right! The capital city of India is also Delhi. Can you name another famous landmark in Delhi?"}'''
------------------------

*NOTE :
*Response always in JSON format.
*Follow-up question always in above topics only.
*Don't include anything like poor, average or good student
"""
        return prompt
    def format_history(self, history):
        try:
            s = ''
            if len(history) > 5:
                for i in history[-5:-1]:
                    s += f"Question: {i['question']}" + '\n'
                    s += f"Student Answer: {i['answer']}" + '\n'
            else:
                for i in history[:-1]:
                    s += f"Question: {i['question']}" + '\n'
                    s += f"Student Answer: {i['answer']}" + '\n'
            logger.info("Formatted conversation history successfully.")
            return s.strip()
        except Exception as e:
            logger.error(f"Error formatting history: {str(e)}")
            raise Exception("Error formatting history")

    def student_qna_fun(self, query,answer, student_level,difficulty_level,learning_goals, history=None):
        response = {"question":"OpenAI Not Responding"}
        for delay_secs in (2**x for x in range(0, 3)):
            try:
                if history:
                    if len(history) > 1:
                        his = self.format_history(history)
                    else:
                        his=""
                    # his = self.format_history(history)
                else:
                    his = ''
                topics = ",".join(learning_goals)
                res = self._system_prompt(his,student_level,difficulty_level,topics)
                logger.info(f"Generated system prompt for query: {query}")
                
                # Define the conversation history
                conversation_history = [
                    {"role": "system", "content": res}
                ]
                interactions = []

                interactions.append(("user", query))

                # Construct user_prompt
                delimiter = "==="  # Replace with your desired delimiter
                user_prompt = f'''

                Conversation: {delimiter} {his} {delimiter}

                ------------------------
                Question: {delimiter} {query} {delimiter}
                Answer: {delimiter} {answer} {delimiter}        
    *NOTE :
    *Response always in above JSON format.
    *Follow-up question always in above topics only.
    *Don't include anything like poor, average or good student
                
                '''

                interactions.append(("user", user_prompt))

                logger.info("Sending API request to OpenAI...")
                ans = self.openai_client.chat.completions.create(
                    model=self.gpt_engine_name,
                    messages=conversation_history + [{"role": role, "content": content} for role, content in interactions],
                    max_tokens=500
                )
                
                json_answer = ans.choices[0].message.content
                json_answer=json_answer.replace("`","").replace("json","")
                response=json.loads(json_answer)
                break
            except Exception as e:
                time.sleep(delay_secs)
                logger.error(f"Error generating QnA response: {str(e)}")
                continue
        return response