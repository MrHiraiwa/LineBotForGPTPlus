clock = FunctionDeclaration(
    name="clock",
    description="useful for when you need to know what time it is.",
)

googlesearch = FunctionDeclaration(
    name="get_googlesearch",
    description="useful for when you need to know what time it is.",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "検索ワード"
            }
        }
    },
)

customsearch = FunctionDeclaration(
    name="get_customsearch1",
    description="",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "検索ワード"
            }
        }
    },
)

generateimage = FunctionDeclaration(
    name="generate_image",
    description="If you specify a long sentence, you can generate an image that matches the sentence.",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "画像生成の文章"
            }
        }
    },
)

wikipedia = FunctionDeclaration(
    name="search_wikipedia",
    description="useful for when you need to Read dictionary page by specifying the word.",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "検索ワード"
            }
        }
    },
)

scraping = FunctionDeclaration(
    name="scraping",
    description="useful for when you need to read a web page by specifying the URL.",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "読みたいページのURL"
            }
        }
    },
)
