from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.utilities.google_search import GoogleSearchAPIWrapper
from langchain import LLMMathChain

google_search = GoogleSearchAPIWrapper()
llm_math_chain = LLMMathChain(llm=llm, verbose=True)

llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0613")
search = SerpAPIWrapper()

tools = [
    Tool(
        name = "Google Search",
        func=google_search.run,
        description="最新の話題について答える場合に利用することができます。また、今日の日付や今日の気温、天気、為替レートなど現在の状況についても確認することができます。入力は検索内容です。"
    ),
    Tool(
        name="Calculator",
        func=llm_math_chain.run,
        description="計算をする場合に利用することができます。"
    )
]

mrkl = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)

def langchain_agent(question):
    result = mrkl.run(question)
    return result
  
