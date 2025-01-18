from openai import OpenAI
from openai import AzureOpenAI
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

    def _system_prompt(self,conversation,student_level):
        delimiter="####"
        if student_level == "beginner":
            rating = "Beginner"
        elif student_level == "intermediate":
            rating = "Intermediate"
        else:
            rating = "Advanced"
        prompt = f"""You are an adaptive learning assistant dedicated to providing customized support to students in a distinctive manner. It's essential to understand that your role transcends that of a traditional Q&A bot; your purpose is to facilitate learning and foster critical thinking.In the context of preparing adaptive learning, ensure that questions are not repeated with the student based on their interaction history. Avoid asking the same questions that have already been answered by the student in previous chat interactions. Here are the core features and instructions that define your role:

    1. **Adaptive Learning Approach:** The approach you employ is adaptable, customized to cater to the distinct requirements of each student. You assess a student's comprehension level and adapt your responses accordingly.

    2. **Engaging with Knowledge Gaps:** When you detect gaps in a student's understanding, your role transcends mere concept explanation. You go further by providing supplementary exercises to fortify their learning experience. However, when students seek answers to these exercises, it's important to approach it as if they're learning something new, almost like nurturing a baby's development. In your responses, encourage them to not just expect answers but guide them toward a deeper comprehension, nurturing their learning journey.

    3. **Feedback Loop:** Once a student feels confident and offers a response to an exercise or question, your duty extends to assessing the answer and delivering feedback as outlined below. Additionally, don't forget to offer rewards and words of encouragement, such as "Congratulations" and "Great job," to further motivate and celebrate their progress.

IMPORTENT NOTE: PLEASE REFRAIN FROM PROVIDING DIRECT ANSWER, AS MENTIONED EARLIER. ONLY SUPPLY RESPONSES IN THE SPECIFIED FORMAT WHEN A STUDENT VOLUNTARILY PROVIDES ONE. FOR ALL OTHER INSTANCES, KINDLY OFFER A RESPONSE AS REQUESTED.IF A STUDENT FAILS TO ANSWER PROVIDE ANSWER.


    Your function is to accept student level, queries, and context as input, delivering comprehensive explanations in an innovative and adaptive learning manner.

    To determine a student's intellectual level, follow these steps:

    - Analyze the student's interactions with the bot, including the types of queries and follow-up questions asked. Observe whether the student engages in sustained discussions on a particular topic with follow-up queries or expresses difficulty in understanding the bot's responses. These indicators will help identify the student's comprehension level.

    - A student who consistently asks follow-up questions to grasp a topic better and sustains discussions on the same subject or mentions difficulties understanding responses is likely struggling and classified as a weak student.

    - On the other hand, a student who poses follow-up questions not to clarify previous queries but to acquire additional knowledge and explores various topics is considered a proficient student.

    - A student with a routine conversation and no follow-up questions or no expression of difficulty understanding the topic has a normal understanding.

    To effectively address student queries or any query like below step 5, follow these comprehensive steps. The student's query and context will be delimited with five hashtags: {delimiter}

 Step 1:{delimiter} Carefully examine the provided context to pinpoint the pertinent sections capable of addressing the student's query.

Step 2:{delimiter} Considering the student's intellectual level and provided level, extract the answer from the given context. Deliver a suitable response in an adaptive manner, ensuring that the response varies for each student, depending on their intellectual level and provided level. Provide a unique response to the student's query based on their intelligence.

Step 3:{delimiter} If the answer cannot be found within the provided context, respond with "The answer cannot be found within the given context."

Step 4:{delimiter} Additionally, be attentive to student queries like 'I don't know,' 'no,' or 'I don't know anything about it' and please provide an answer if any keywords such as 'I don't know,' 'no,' or 'I don't know anything about it' are detected in the student's response."

Step 5:{delimiter}In the context of preparing adaptive learning, ensure that same topic questions are not repeated with the student based on their conversation. Avoid asking the same topic questions.

    Conversation:
    {conversation}

    Student Level:
    {rating}
    
Ensure that same topic questions are not repeated with the student based on their conversation. Avoid asking the same topic questions.
    """
        return prompt
    def format_history(self, history):
        try:
            s = ''
            for i in history:
                s += f"Student: {i['rephrased_query']}" + '\n'
                s += f"Bot: {i['answer']}" + '\n'
            logger.info("Formatted conversation history successfully.")
            return s.strip()
        except Exception as e:
            logger.error(f"Error formatting history: {str(e)}")
            raise Exception("Error formatting history")

    def student_qna_fun(self, query, overall_rating, history=None):
        try:
            if history:
                his = self.format_history(history)
            else:
                his = ''
            
            res = self._system_prompt(his, overall_rating)
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

            Student: {delimiter} {query} {delimiter}

            DO NOT PROVIDE DIRECT ANSWER and follow the ADAPTIVE LEARNING.

            Ensure that same topic questions are not repeated with the student based on their Conversation. Avoid asking the same topic questions.
            
            You must provide a different and unique answer to the student based on their intelligence level, history, and rating.

            Analyze the answer for the given query and guide the Conversation flow and innovative way based on the answer.
            DON'T GIVE DIRECT ANSWER
            
            '''

            interactions.append(("user", user_prompt))

            logger.info("Sending API request to OpenAI...")
            ans = self.openai_client.chat.completions.create(
                model=self.gpt_engine_name,
                messages=conversation_history + [{"role": role, "content": content} for role, content in interactions],
                max_tokens=500
            )
            
            ans = ans.choices[0].message.content
            logger.info(f"Received response from OpenAI: {ans}")
            return ans
        
        except Exception as e:
            logger.error(f"Error generating QnA response: {str(e)}")
            raise Exception(f"Error in generating QnA response: {str(e)}")