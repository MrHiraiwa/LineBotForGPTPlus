from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.utilities import GoogleSearchAPIWrapper

llm = ChatOpenAI(model="gpt-3.5-turbo-0613")

search = GoogleSearchAPIWrapper()

tools = [
    Tool(
        name = "Search",
        func=search.run,
        description="useful for when you need to answer questions about current events. it is single-input tool Search."
    ),
]

mrkl = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)

def langchain_agent(question):
    try:
        result = mrkl.run(question)
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        # 何らかのデフォルト値やエラーメッセージを返す
        return "An error occurred while processing the question"

