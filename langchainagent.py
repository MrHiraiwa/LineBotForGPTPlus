from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.utilities.google_search import GoogleSearchAPIWrapper

llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0613")

google_search = GoogleSearchAPIWrapper()

tools = [
    Tool(
        name = "Search",
        func=google_search.run,
        description="useful for when you need to answer questions about current events."
    ),
]

mrkl = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)

def langchain_agent(question):
    result = mrkl.run(question)
    return result
  
