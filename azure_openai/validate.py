from openai import OpenAI
from openai import AzureOpenAI
from uitils.logger import custom_logger

logger = custom_logger.get_logger()

class Validate:
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

    def _system_prompt(self):
        score_system = """
**Rating Criteria**:

- If it is the student's **first query** with the bot, assign a starting rating of **3** regardless of the query quality.
- If the student answers correctly on the **first attempt**, assign a rating of **5**.
- If the student answers correctly after receiving **one hint** or further clarification, assign a rating of **4**.
- If the student answers correctly after receiving **two hints**, assign a rating of **3**.
- If the student answers correctly after receiving **three hints**, assign a rating of **2**.
- If the student requests **more than three hints** or responds with answers like "I don't know" or similar, assign a rating of **1**.

**Performance-based Adjustments**:

- In subsequent interactions (after the first query), analyze both the student's current performance and their previous interactions. Adjust the rating based on improvements, consistency, or decline in performance.
    - **Improvement**: If the student's performance improves from the last interaction (e.g., fewer hints needed or more correct answers), increase their rating accordingly.
    - **Decline**: If the student's performance declines (e.g., requiring more hints or giving incorrect answers), decrease their rating accordingly.

**Response Type**:

- The rating must be among these options: **'1', '2', '3', '4', and '5'**.
- If this is the **first interaction**, start the rating at **3**.

To determine the student's rating:

- Analyze the student's current query and response from the bot, considering the entire conversation history if relevant.
- For the very first interaction, assign a starting rating of **3** regardless of the query's quality. Adjust ratings based on the student's performance in subsequent interactions.

"""
        return score_system
    
    def format_history(self,history):
        try:
            s = ''
            for i in history:
                s += f"Student: {i['rephrased_query']}" + '\n'
                s += f"Bot: {i['answer']}" + '\n'
                s += f"Interaction Rating: {i['interaction_rating']}" + "\n"
            logger.info("Formatted conversation history successfully.")
            return s.strip()
        except Exception as e:
            logger.error(f"Error formatting history: {str(e)}")
            raise Exception("Error formatting history")

    def student_score(self, query, response, history):
        try:
            if history:
                his = self.format_history(history)
            else:
                his = ''
            
            conversation_history = [
                {"role": "system", "content": self._system_prompt()}
            ]
            interactions = []
            delimiter = "==="  # Replace with your desired delimiter
            user_prompt = f'''
Conversation: {delimiter} {his} {delimiter}

Student: {delimiter} {query} {delimiter}
Bot: {delimiter} {response} {delimiter}

Response should have only single rating number 5, 4, 3, 2, or 1, without providing any additional information.

Response:'''
            
            interactions.append(("user", user_prompt))
            
            logger.info("Sending API request to OpenAI for rating...")
            ans = self.openai_client.chat.completions.create(
                model=self.gpt_engine_name,
                messages=conversation_history + [{"role": role, "content": content} for role, content in interactions],
                max_tokens=1
            )
            
            ans = ans.choices[0].message.content
            logger.info(f"Received response from OpenAI: {ans}")
            return int(ans)
        except Exception as e:
            logger.error(f"Error generating student score: {str(e)}")
            raise Exception(f"Error in generating student score: {str(e)}")

    def adapt_difficulty(self, comprehension_score, current_difficulty_level):
        try:
            if comprehension_score > 3:
                if current_difficulty_level == "easy":
                    return "medium"
                elif current_difficulty_level == "medium":
                    return "hard"
                else:
                    return "hard"
            
            elif comprehension_score < 2:
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