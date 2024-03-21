functions = [
    {
        # 関数の名称
        "name": "get_customsearch1",
        # 関数の機能説明
        "description": "",
        # 関数のパラメータ
        "parameters": {
            "type": "object",
            # 各引数
            "properties": {
                "words": {
                    "type": "string",
                    # 引数の説明
                    "description": "検索ワード"
                }
            }
        }
    },
    {
        # 関数の名称
        "name": "clock",
        # 関数の機能説明
        "description": "useful for when you need to know what time it is."
    },
    {
        # 関数の名称
        "name": "generate_image",
        # 関数の機能説明
        "description": "If you specify a long sentence, you can generate an image that matches the sentence.",
        # 関数のパラメータ
        "parameters": {
            "type": "object",
            # 各引数
            "properties": {
                "prompt": {
                    "type": "string",
                    # 引数の説明
                    "description": "画像生成の文章"
                }
            }
        }
    },
    {
        # 関数の名称
        "name": "search_wikipedia",
        # 関数の機能説明
        "description": "useful for when you need to Read dictionary page by specifying the word. ",
        # 関数のパラメータ
        "parameters": {
            "type": "object",
            # 各引数
            "properties": {
                "prompt": {
                    "type": "string",
                    # 引数の説明
                    "description": "検索ワード"
                }
            }
        }
    },
    {
        # 関数の名称
        "name": "scraping",
        # 関数の機能説明
        "description": "useful for when you need to read a web page by specifying the URL.",
        # 関数のパラメータ
        "parameters": {
            "type": "object",
            # 各引数
            "properties": {
                "link": {
                    "type": "string",
                    # 引数の説明
                    "description": "読みたいページのURL"
                }
            }
        }
    },
    {
        # 関数の名称
        "name": "get_googlesearch",
        # 関数の機能説明
        "description": "",
        # 関数のパラメータ
        "parameters": {
            "type": "object",
            # 各引数
            "properties": {
                "words": {
                    "type": "string",
                    # 引数の説明
                    "description": "検索ワード"
                }
            }
        }
    }
]
