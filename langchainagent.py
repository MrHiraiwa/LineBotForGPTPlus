from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.utilities.google_search import GoogleSearchAPIWrapper
import openai
from datetime import datetime, time, timedelta
import pytz

def clock(dummy):
    jst = pytz.timezone('Asia/Tokyo')
    nowDate = datetime.now(jst) 
    nowDateStr = nowDate.strftime('%Y/%m/%d %H:%M:%S %Z')
    return nowDateStr


llm = ChatOpenAI(model="gpt-3.5-turbo")

google_search = GoogleSearchAPIWrapper()

tools = [
    Tool(
        name = "Search",
        func=google_search.run,
        description="useful for when you need to answer questions about current events. it is single-input tool Search."
    ),
    Tool(
        name = "Clock",
        func=clock,
        description="useful for when you need to know what time it is. it is single-input tool."
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

