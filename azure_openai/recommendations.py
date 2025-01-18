from openai import OpenAI
from openai import AzureOpenAI
from uitils.logger import custom_logger

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

    def _system_prompt(self,rating,conversation):
        prompt =f'''
Your are AI Assistant that helps students by recommending new quesstion based on the the given topics. These questions helps students to enhance the understanding of topic
Analyse the given student ratings and generate three questions based on student level
If the student is poor then generate easy questions, if he is average then generate modarate question else generate hard question only from the context given

Instructions to find student intellegence level:
- First analyse the student conversation with bot, type of queries, follow up queries student is asking to the bot. Does he taking the conversation on one topic with follow up queries or he asking queries on different topics.
- If the student is asking follow up questions(to understand previous query more) on same topic and taking conversation on same topic for long time or saying he is not understanding the bot response then the student is potentially not understanding the topic and is a weak student.
- If the student is asking follow up question not to understand his previous query but to gain more knowledge and ask different type of queries to bot to gain knowledge then student is potentially a good student.
- If the student conversation is normal without any follow up question or he never said he didn't understand the topic then the student has a normal understanding.

Conversation:
{conversation}

Student Rating:
{rating} out of 5

Based on the student intelligence level and student rating ask him different type of questions.

*NOTE :
*Include a good intro like sure, let me give me some questions to you for practice and after giving questions from the context, ask them to try to provide answer so that you can validate the answers and provide areas of gap.
*Don't include anything like poor, average or good student.'''
        return prompt
    
    def format_history(self,history):
        try:
            s = ''
            for i in history:
                s += f"Student: {i['rephrased_query']}\n"
                s += f"Bot: {i['answer']}\n"
                s += f"Interaction Rating: {i['interaction_rating']}\n"
            return s.strip()
        except KeyError as e:
            logger.error(f"Missing key in history format: {e}")
            raise ValueError("History format error: Missing key")

    def recommend_questions(self, learning_goals, rating, history):
        try:
            # Log input values
            logger.info(f"Received recommendation request for learning goals: {learning_goals}, rating: {rating}")
            
            topics = ",".join(learning_goals)
            if history:
                his = self.format_history(history)
            else:
                his = ''
            
            # Construct system prompt for OpenAI
            conversation_history = [
                {"role": "system", "content": self._system_prompt(rating, his)}
            ]

            user_prompt = f"""Your task is to generate ONLY 3 best questions based on these topics: {topics}. Your response should be as truthful as possible, and should include all the information covered about the topic: {topics}. Start generating with an engaging sentence.
*NOTE:
* Include a good intro like "Sure, let me give you some questions for practice," and after giving questions from the context, ask them to try to provide answers so that you can validate them.
* Do not include anything about poor, average, or good students."""

            # Log the user prompt for tracking
            logger.debug(f"User prompt: {user_prompt}")

            # Call OpenAI or Azure API
            ans = self.openai_client.chat.completions.create(
                model=self.gpt_engine_name,
                messages=conversation_history + [{"role": "user", "content": user_prompt}],
                max_tokens=300
            )

            ans = ans.choices[0].message.content
            logger.info("Successfully generated questions.")
            return ans
        except Exception as e:
            logger.error(f"Error while generating recommendations: {str(e)}")
            raise RuntimeError("Error generating recommendations from OpenAI")
