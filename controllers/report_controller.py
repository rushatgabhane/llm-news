from services.hackernews_service import fetch_hackernews_top_stories
from services.google_api_service import fetch_google_api_top_stories
from langchain.prompts import ChatPromptTemplate
from models.report_model import ReportResponse, ReportItem
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
from langchain.callbacks.base import BaseCallbackHandler
import os
import asyncio
import logging

# Setup logging to file
logging.basicConfig(filename='prompt_logs.log', level=logging.INFO)

# Define callback handler to log prompts and responses
class PromptAndResponseLogger(BaseCallbackHandler):
    def on_llm_start(self, prompts):
        for prompt in prompts:
            logging.info(f"LLM Prompt: {prompt}")

    def on_llm_end(self, response):
        for generation in response.generations:
            for gen in generation:
                logging.info(f"LLM Response: {gen.text}")

# Initialize the LLM with callback
llm = ChatOpenAI(
    model_name="gpt-4.1-nano",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    callbacks=[PromptAndResponseLogger()]
)

# Prompt to categorize content
category_prompt_template = ChatPromptTemplate.from_template(
    "From the following tech article content, output categories as terms separated by commas:\n\n"
    "No explanation. Just the category.\n\n{content}"
)
category_chain: Runnable = category_prompt_template | llm

# Prompt to summarize content
summary_prompt_template = ChatPromptTemplate.from_template(
    "Summarize the following tech article content in 2-3 sentences: {content}"
)
summary_chain: Runnable = summary_prompt_template | llm

# Prompt to remove duplicates
duplicates = ChatPromptTemplate.from_template(
    "Return the titles of the articles that seem to be duplicates based on the summary of the article: {content}"
)
duplicates_chain: Runnable = duplicates | llm

async def generate_tech_trends_report():
    articles = []
    articles.extend(await fetch_hackernews_top_stories())
    articles.extend(await fetch_google_api_top_stories())
    summaries = []

    for article in articles:
        try:
            content = await article['content'] if asyncio.iscoroutine(article['content']) else article['content']

            if not content or len(content.strip()) < 100:
                category = "Insufficient Content"
                summary = "Content too short to summarize."
            else:
                category_result, summary_result = await asyncio.gather(
                    category_chain.ainvoke({"content": content}),
                    summary_chain.ainvoke({"content": content})
                )

                category = category_result.content.strip().replace("Category:", "").strip()
                summary = summary_result.content.strip()

            report_item = ReportItem(
                category=category,
                title=article['title'],
                source=article['url'],
                summary=summary
            )
            summaries.append(report_item)

        except Exception as e:
            summaries.append(ReportItem(
                category=f"Error categorizing: {e}",
                title=article['title'],
                source=article['url'],
                summary=f"Error summarizing: {e}"
            ))

    return ReportResponse(summaries=summaries)
