from llm_client import LLMClient
from prompts import *


class SQLAgents(LLMClient):
    def __init__(self, description):
        super().__init__(description)
        self.allow_tools = ["intent_steering", "generate_sql", "summarize"]

        self.remember("system", main_prompt)

    def parsing_resp(self, response):
        pass

