import os
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin@db:5432/observability")

# Initialize the database connection
db = SQLDatabase.from_uri(DATABASE_URL)

# Initialize the Google Generative AI model
llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.1
)

# Create SQL toolkit
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Create the SQL agent
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type="zero-shot-react-description",
    max_iterations=5,
    early_stopping_method="generate"
)