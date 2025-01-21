import os

os.environ["OPENAI_TYPE"] = "azure_openai"
os.environ["AZURE_OPENAI_API_KEY"] = "Azure OpenAI key" #Replace Azure API KEY
os.environ["AZURE_OPENAI_API_BASE"] = "Azure Endpoint" #Replace Azure ENDPOINT/BASE
os.environ["AZURE_OPENAI_API_VERSION"] = "2023-07-01-preview"
os.environ["GPT4_MODEL"] = "gpt-4o" #Recommend GPT 4o model for best results

openai_type = os.getenv("OPENAI_TYPE")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_API_BASE")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
gpt4_model = os.getenv("GPT4_MODEL")