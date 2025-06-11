from services.hackernews_service import fetch_hackernews_top_stories
from services.google_api_service import fetch_google_api_top_stories
from langchain.prompts import ChatPromptTemplate
from models.report_model import ReportResponse, ReportItem
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
import os
import asyncio

# Initialize the LLM
llm = ChatOpenAI(model_name="gpt-4.1-nano", openai_api_key=os.getenv("OPENAI_API_KEY"))

# Prompt to categorize content
category_prompt_template = ChatPromptTemplate.from_template(
    "From the following tech article content, output only a single category name "
    "(e.g., AI, Cybersecurity, Cloud, Mobile, Infrastructure, Software, Startups). "
    "No explanation. Just the category.\n\n{content}"
)
category_chain: Runnable = category_prompt_template | llm

# Prompt to summarize content
summary_prompt_template = ChatPromptTemplate.from_template(
    "Summarize the following tech article content in 2-3 sentences: {content}"
)
summary_chain: Runnable = summary_prompt_template | llm

async def generate_tech_trends_report():
    articles = []
    articles.extend(await fetch_hackernews_top_stories())
    articles.extend(await fetch_google_api_top_stories())
    summaries = []

    for article in articles:
        try:
            # Handle coroutine content
            content = await article['content'] if asyncio.iscoroutine(article['content']) else article['content']

            # Skip poorly fetched content
            if not content or len(content.strip()) < 100:
                category = "Insufficient Content"
                summary = "Content too short to summarize."
            else:
                # Parallel calls
                category_result, summary_result = await asyncio.gather(
                    category_chain.ainvoke({"content": content}),
                    summary_chain.ainvoke({"content": content})
                )

                # Extract only text from the result object
                category = category_result.content.strip().replace("Category:", "").strip()
                summary = summary_result.content.strip()

            # Build and store result
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
