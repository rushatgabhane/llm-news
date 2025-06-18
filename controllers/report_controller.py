from services.google_api_service import fetch_google_api_top_stories
from services.hackernews_service import fetch_hackernews_top_stories
from logger_service import logger
from langchain.prompts import ChatPromptTemplate
from models.report_model import ReportResponse, ReportItem
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
from langchain.callbacks.base import AsyncCallbackHandler
import os
import asyncio
import json

class PromptAndResponseLogger(AsyncCallbackHandler):
    def __init__(self, logger):
        self.logger = logger

    async def on_chat_model_start(self, serialized, messages, **kwargs):
        for message_group in messages:
            for message in message_group:
                self.logger.info(f"LLM Chat Prompt: {message.content}")

    async def on_llm_end(self, response, **kwargs):
        for generation in response.generations:
            for gen in generation:
                self.logger.info(f"LLM Response: {gen.text}")

    async def on_llm_error(self, error, **kwargs):
        self.logger.error(f"LLM Error: {error}")

llm = ChatOpenAI(
    model_name="gpt-4.1-nano",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    callbacks=[PromptAndResponseLogger(logger)]
)

combined_prompt_template = ChatPromptTemplate.from_template(
    """
    You are a tech news analyzer. Given the following article content, do two tasks:

    1. Categorize the content into topics (do not use abbreviations). Separate them by making use of the standard JSON list format.
    2. Summarize the content in 2-5 sentences.
    3. Provide actionable insights based on the article content. Separate them by making use of the standard JSON list format.

    Output strictly in this JSON format:

    {{
        "categories": [
        ],
        "summary": "<summary>",
        "insights": [
        ]
    }}

    You must follow these rules:
    - Always return a valid JSON object.
    - Always categorize the content into one or more topics.
    - Always provide a summary in 2-5 sentences.
    - Always provide actionable insights based on the content.
    - If the content is too short or insufficient, categorize it as "Insufficient content" and leave summary and insights empty.
    - If you encounter an error or cannot process the content, categorize it as "Error", provide the error message as the summary and leave insights empty.

    Article Content:
    {content}
    """
)

pipeline: Runnable = combined_prompt_template | llm

async def generate_tech_trends_report(logger):
    articles = []
    articles.extend(await fetch_hackernews_top_stories(logger))
    articles.extend(await fetch_google_api_top_stories(logger))
    summaries = []

    for article in articles:
        try:
            content = await article['content'] if asyncio.iscoroutine(article['content']) else article['content']

            if not content or len(content.strip()) < 100:
                logger.warning(f"[Controller] Insufficient content for article: {article['url']}")
            else:
                response = await pipeline.ainvoke({"content": content})
                response_text = response.content.strip()
                logger.info(f"Raw LLM response: {response_text}")
                
                parsed = json.loads(response_text)
                categories = parsed.get("categories", [])
                summary = parsed.get("summary", "No summary provided.")
                insights = parsed.get("insights", [])
                if not isinstance(insights, list):
                    insights = [str(insights)]

            if "Error" in categories:
                logger.error(f"[Controller] LLM returned error for article: {article['url']}")
                continue
            elif "Insufficient Content" in categories:
                logger.warning(f"[Controller] Insufficient content for article: {article['url']}")
                continue
            else:
                logger.info(f"[Controller] Processed article: {article['url']}")

            report_item = ReportItem(
                categories=categories,
                title=article['title'],
                source=article['url'],
                summary=summary,
                insights=insights
            )
            summaries.append(report_item)

        except Exception as e:
            logger.error(f"[Controller] Error processing article: {article['title']} - {e}")

    return ReportResponse(summaries=summaries)