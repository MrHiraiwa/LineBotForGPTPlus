from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.schema import SystemMessage

llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0613")

search = GoogleSearchAPIWrapper()

tools = [
    Tool(
        name = "Search",
        func=search.run,
        description="useful for when you need to answer questions about current events."
    ),
]

system_message = SystemMessage(content="""You are a helpful AI assistant.""")
mrkl = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True, agent_kwargs={"system_message":system_message},)

def langchain_agent(question):
    result = mrkl.run(question)
    return result
  
