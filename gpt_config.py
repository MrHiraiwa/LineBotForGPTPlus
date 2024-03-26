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
    },
    {
        # 関数の名称
        "name": "get_calendar",
        # 関数の機能説明
        "description": "You can retrieve upcoming schedules and the event ID of the schedule."
    },
    {
        # 関数の名称
        "name": "add_calendar",
        # 関数の機能説明
        "description": "You can add schedules.",
        "parameters": {
            "type": "object",
            # 各引数
            "properties": {
                "summary": {
                    "type": "string",
                    # 引数の説明
                    "description": "スケジュールのサマリー(必須)"
                },
                "start_time": {
                    "type": "string",
                    # 引数の説明
                    "description": "スケジュールの開始時間をRFC3339フォーマットの日本時間で指定(必須)"
                },
                "end_time": {
                    "type": "string",
                    # 引数の説明
                    "description": "スケジュールの終了時間をRFC3339フォーマットの日本時間で指定(必須)"
                },
                "description": {
                    "type": "string",
                    # 引数の説明
                    "description": "スケジュールした内容の詳細な説明(必須)"
                },
                "location": {
                    "type": "string",
                    # 引数の説明
                    "description": "スケジュールの内容を実施する場所(必須)"
                }
            }
        }
    },
    {
        # 関数の名称
        "name": "update_calendar",
        # 関数の機能説明
        "description": "You can update schedules by the event ID of the schedule.",
        "parameters": {
            "type": "object",
            # 各引数
            "properties": {
                "event_id": {
                    "type": "string",
                    # 引数の説明
                    "description": "スケジュールのイベントID(必須)"
                },
                "summary": {
                    "type": "string",
                    # 引数の説明
                    "description": "更新後のスケジュールのサマリー(必須)"
                },
                "start_time": {
                    "type": "string",
                    # 引数の説明
                    "description": "更新後のスケジュールの開始時間をRFC3339フォーマットの日本時間で指定(必須)"
                },
                "end_time": {
                    "type": "string",
                    # 引数の説明
                    "description": "更新後のスケジュールの終了時間をRFC3339フォーマットの日本時間で指定(必須)"
                },
                "description": {
                    "type": "string",
                    # 引数の説明
                    "description": "更新後のスケジュールした内容の詳細な説明(必須)"
                },
                "location": {
                    "type": "string",
                    # 引数の説明
                    "description": "更新後のスケジュールの内容を実施する場所(必須)"
                }
            }
        }
    },
    {
        # 関数の名称
        "name": "delete_calendar",
        # 関数の機能説明
        "description": "You can delete schedules by the event ID of the schedule.",
        "parameters": {
            "type": "object",
            # 各引数
            "properties": {
                "event_id": {
                    "type": "string",
                    # 引数の説明
                    "description": "削除対象のスケジュールのイベントID(必須)"
                }
            }
        }
    }   
]
