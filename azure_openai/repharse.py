from openai import OpenAI
from openai import AzureOpenAI
from uitils.logger import custom_logger

logger = custom_logger.get_logger()

class Rephrase:
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

    def _rephrase_prompt(self):
        followup_query_prompt = """
Your task is to take into consideration two things, one is the chat history that has happend between the User and Bot and other is the User Query. Now you need to modify the user query as needed according to chat history and generate a new question that can searched upon. 
You have to handle follow up questions and take into considerations the previous responses of the  Bot if necessary. If the question is not related to the previous responses then output the same question as inputted. If you are not confident on whether the question is related to previous responses, then output the same question.
Carefully analyze the given user query and chat history. If the given user query is a follow-up and requires some information from the previous query or bot response, then rephrase the given user query accordingly.
If the user query does not require any explicit information from chat history, then reply with the same user query without rephrasing it or adding any extra information or explanation.
If the current user query is on the same topic as the previous one and does not explicitly require information from the previous query, then output the current query without rephrasing or adding extra information.


Examples:
1. Chat History:
User: Explain sustainability report.
Bot: Sustainability reports provide detailed information about an organization's environmental, social, and economic impact.
User Query: Explain more about it.
Rephrased question: Provide further details or elaborate on the specific aspects of sustainability reports?

2. Chat History:
User: how many feedback are there in april through public channel
Bot: There are 22 feedback in April through the public channel.
User Query: what is the average rating of these feedback
Rephrased question: What is the average rating of the feedback received in April through the public channel?

3. Chat History:
User: Explain the concept of sustainability reports.
Bot: Sustainability reports serve as comprehensive documents detailing a company's sustainable practices, environmental impact, and social responsibilities.
User Query: Could you provide further insights?
Rephrased question: Elaborate more on the specific aspects of sustainability reports, such as environmental initiatives or corporate social responsibility efforts?

4. Chat History:
User: How many distint division are there?
Bot: There is 1 unique division
User Query: what is it?
Rephrased question: What is the name of distinct division?

5. Chat history:
User: how many rating are there in june
Bot: There are 19 ratings in June.
User Query: nexxt month ratings?
Rephrased question: how many ratings are there in july?

Taking the example from the above examples, carefully analyse the previous user query and current user query. Rephrase the current user query only if it requires explicit information from previous query. If the current user query is standlone and doesnot require any information from previous user query then reply with current user query without adding any extra information.
"""
        return followup_query_prompt

    def followup_query(self, query, history=None):
        """
        Generates a follow-up query based on context.

        Args:
            query (str): The natural language query.
            history (str, optional): The last history or context (default is None).

        Returns:
            str: The generated follow-up query.
        """
        try:
            system_prompt = self._rephrase_prompt()
            logger.info(f"Generating rephrased query for user query: {query}")

            ans = self.openai_client.chat.completions.create(
                model=self.gpt_engine_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f'''User: Based on the Chat history rephrase the user query. You need to analyze the user, bot interaction and need to frame the follow-up query which carries all the full information (without any other context) to query.
If the user query does not need any rephrasing based on the chat history then rephrased question will be given user query. No extra information or explanation is allowed in Rephrased question.
If the current user query is a standalone query then do not rephrase it, just output the same user query as the rephrased query.                     
The rephrased query should be precise, to the point and not exceeding 30 words.

Chat history:
{history}
User Query: {query}
Rephrased question:'''}
                ],
                temperature=0.1
            )

            rephrased_question = ans.choices[0].message.content
            logger.info(f"Rephrased question generated: {rephrased_question}")
            return rephrased_question

        except Exception as e:
            logger.error(f"Error generating rephrased question: {str(e)}")
            raise Exception(f"Error in follow-up query generation: {e}")