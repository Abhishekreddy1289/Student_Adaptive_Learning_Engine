from openai import OpenAI
from openai import AzureOpenAI
import time
from uitils.logger import custom_logger
import json

logger = custom_logger.get_logger()

class RecommendationsQuestions:
    def __init__(self, gpt_engine_name, api_key, azure_endpoint, api_version, openai_type) -> None:
        self.answer=''
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

    def _system_prompt(self,student_level,difficulty_level,conversation,topics):
        prompt =f"""
Your are AI Assistant that helps students by recommending new question based on the given topics. These questions helps students to enhance the understanding of the topic
Analyse the given conversation and generate one question based on student level
If the student is poor then generate easy questions, if he is average then generate modarate question else generate hard question only from the context given

Instructions to find student intellegence level:
- First analyse the student's conversation with bot, type of queries, follow up queries that student is asking to the bot. Does he taking the conversation on one topic with follow up queries or he asking queries on different topics.
- If the student is asking follow up questions(to understand previous query more) on same topic and taking conversation on same topic for long time or saying he is not understanding the bot's responses then the student is potentially not understanding the topic and is a weak student.
- If the student is asking follow up question not to understand his previous query but to gain more knowledge and ask different type of queries to bot to gain knowledge then the student is potentially a good student.
- If the student conversation is normal without any follow up question or he never said that he didn't understand the topic then the student has a normal understanding.
- Recommend new question based on below difficulty level.

Conversation:
{conversation}

Student Level:
{student_level}

Difficulty Level:
{difficulty_level}

Topics:
{topics}

Based on the student intelligence level and student level ask him different type of questions.

*** Output Format ***
The response should always be in a JSON format with ONE key: 'question'. The 'question' key has the recommended new quesstion based on the the given topics. Just follow the below example for output compliance:"""+"""
 
Output Format Example:
'''{"question": "Your question here"}'''

*NOTE :
*Response always in JSON format.
*Don't include anything like poor, average or good student."""
        return prompt
    
    def format_history_recommend(self,history):
        try:
            s = ''
            for i in history[:-1]:
                s += f"Bot: {i['question']}\n"
                s += f"Student: {i['answer']}\n"
            return s.strip()
        except KeyError as e:
            logger.error(f"Missing key in history format: {e}")
            raise ValueError("History format error: Missing key")

    def recommend_question(self, learning_goals, student_level,difficulty_level, history=None):
        response = {"question":"OpenAI Not Responding"}
        for delay_secs in (2**x for x in range(0, 3)):
            try:
                # Log input values
                logger.info(f"Received recommendation request for learning goals: {learning_goals}, rating: {student_level}")
                
                topics = ",".join(learning_goals)
                if history:
                    if len(history) > 1:
                        his = self.format_history_recommend(history)
                    else:
                        his=""
                else:
                    his = ''
                
                # Construct system prompt for OpenAI
                conversation_history = [
                    {"role": "system", "content": self._system_prompt(student_level,difficulty_level,his,topics)}
                ]

                user_prompt = f"""Your task is to generate ONLY ONE best question based on these topics: {topics}. Your response should be as truthful as possible, and should include all the information covered about the topic: {topics}. Start generating with an engaging sentence.
    *NOTE:
    * Do not include anything about poor, average, or good students.
    *Response always in above JSON format."""

                # Log the user prompt for tracking
                logger.debug(f"User prompt: {user_prompt}")

                # Call OpenAI or Azure API
                ans = self.openai_client.chat.completions.create(
                    model=self.gpt_engine_name,
                    messages=conversation_history + [{"role": "user", "content": user_prompt}],
                    max_tokens=300
                )

                json_answer = ans.choices[0].message.content
                logger.info("Successfully generated questions.")
                json_answer=json_answer.replace("`","").replace("json","")
                response=json.loads(json_answer)
                break
            except Exception as e:
                time.sleep(delay_secs)
                logger.error(f"Error while generating new question recommendations: {str(e)}")
                continue
        return response
    
    def _system_prompt_next(self,avg_confidence_level,student_level,difficulty_level,conversation,topics):
        prompt =f"""
You are an adaptive learning assistant designed to offer personalized recommendations and identify knowledge gaps based on student input. Use the following details to guide your responses:

- **Learning Goals**: {topics}
- **Student Level**: {student_level}
- **Difficulty Level**: {difficulty_level}
- **Average Confidence Level**: {avg_confidence_level}
- **Interaction History**: {conversation}

### Instructions:

1. **Suggest Personalized Next Steps**: Tailor your recommendations to the student’s learning goals, current level, and progress. If the student is confident and has mastered the basics, suggest more advanced exercises or new topics. If they are uncertain or struggling, advise revisiting foundational concepts and practicing earlier material. Consider the difficulty level to ensure the next steps are appropriately challenging but not overwhelming.

2. **Identify Knowledge Gaps**: Review the student’s past interactions and highlight areas where understanding may be lacking. This could be indicated by repeated mistakes, low confidence in certain topics, or stagnation in progress. Propose targeted exercises or explanations to address these gaps and help the student build confidence.

Your response should be clear, concise, and foster critical thinking, with actionable steps and guidance to help the student move forward.

*** Output Format ***
The response should always be in a JSON format with TWO key: The "next_steps" key has the recommended Suggest Personalized Next Steps based on the the given topics. "knowledge_gaps" key has the Identify Knowledge Gaps based on the the given topics. Just follow the below example for output compliance:"""+"""
 
Output Format Example:
'''{"next_steps":"Your response here","knowledge_gaps": "Your response here"}'''

*NOTE :
*Response always in JSON format.
*Don't include anything like poor, average or good student."""
        return prompt
    
    def format_history(self,history):
        try:
            s = ''
            for i in history:
                s += f"Bot: {i['question']}\n"
                s += f"Student: {i['answer']}\n"
            return s.strip()
        except KeyError as e:
            logger.error(f"Missing key in history format: {e}")
            raise ValueError("History format error: Missing key")

    def recommend_next(self, avg_confidence_level,learning_goals, student_level,difficulty_level, history=None):
        response = {"question":"OpenAI Not Responding"}
        for delay_secs in (2**x for x in range(0, 3)):
            try:
                # Log input values
                logger.info(f"Received recommendation request for learning goals: {learning_goals}, rating: {student_level}")
                
                topics = ",".join(learning_goals)
                if history:
                    his = self.format_history(history)
                else:
                    his = ''
                
                # Construct system prompt for OpenAI
                conversation_history = [
                    {"role": "system", "content": self._system_prompt_next(avg_confidence_level,student_level,difficulty_level,his,topics)}
                ]

                user_prompt = f"""Your task is to generate Suggest Personalized Next Steps and Identify Knowledge Gaps based on these topics: {topics}. Your response should be as truthful as possible, and should include all the information covered about the topic: {topics}. Start generating with an engaging sentence.
    *NOTE:
    * Do not include anything about poor, average, or good students.
    *Response always in above JSON format."""

                # Log the user prompt for tracking
                logger.debug(f"User prompt: {user_prompt}")

                # Call OpenAI or Azure API
                ans = self.openai_client.chat.completions.create(
                    model=self.gpt_engine_name,
                    messages=conversation_history + [{"role": "user", "content": user_prompt}],
                    max_tokens=300
                )

                json_answer = ans.choices[0].message.content
                logger.info("Successfully generated recommendations.")
                json_answer=json_answer.replace("`","").replace("json","")
                response=json.loads(json_answer)
                break
            except Exception as e:
                time.sleep(delay_secs)
                logger.error(f"Error while generating recommendations: {str(e)}")
                continue
        return response