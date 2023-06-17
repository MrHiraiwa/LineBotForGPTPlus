from langchain import SerpAPIWrapper
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI


llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0613")
search = SerpAPIWrapper()
wolfram = WolframAlphaAPIWrapper()
tools = [
    Tool(
        name = "Search",
        func = search.run,
        description = "useful for when you need to answer questions about current events. You should ask targeted questions"
    )
]

mrkl = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)

def langchain_agent(question):
    result = mrkl.run(question)
    return result
  
