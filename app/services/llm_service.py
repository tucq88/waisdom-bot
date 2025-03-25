from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from app.config.settings import OPENAI_API_KEY, DEFAULT_AGENT_MODEL, MAX_TOKENS_SUMMARY

logger = logging.getLogger(__name__)

class ContentSummary(BaseModel):
    """Model for content summary output."""
    summary: str = Field(description="A concise summary of the content")
    key_points: List[str] = Field(description="Key points from the content")
    actionable_insights: List[str] = Field(description="Actionable insights extracted from the content")
    priority_score: float = Field(description="Priority score from 1-10, with 10 being highest importance")
    tags: List[str] = Field(description="Relevant tags/topics for this content")

class LLMService:
    """Service for LLM-based content processing."""

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=DEFAULT_AGENT_MODEL,
            temperature=0.1,
            verbose=True
        )

    def summarize_content(self, content: str, metadata: Dict[str, Any]) -> ContentSummary:
        """
        Generate a summary and extract insights from content.

        Args:
            content: The content to summarize
            metadata: Additional metadata about the content

        Returns:
            ContentSummary object with summary and insights
        """
        parser = PydanticOutputParser(pydantic_object=ContentSummary)

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert research assistant. You are analyzing content to extract valuable
            information. For the content provided, create a concise summary, extract key points, and identify
            actionable insights that could be useful for the researcher.

            Also provide a priority score from 1-10, where:
            - 10: Groundbreaking/essential content that represents unique, highly actionable insights
            - 7-9: Very important content with novel information and clear applications
            - 4-6: Moderately useful content with some interesting points
            - 1-3: Basic/common information with limited novelty or application

            Finally, generate 3-7 relevant tags that categorize the content.

            {format_instructions}
            """),
            ("user", """Here is the content to analyze:
            {content}

            Additional metadata: {metadata}
            """)
        ])

        # Truncate content if necessary to avoid token limits
        # This is a simple approach - more sophisticated chunking would be better for long content
        max_content_length = 14000  # Approximate token limit for context
        if len(content) > max_content_length:
            logger.warning(f"Content truncated from {len(content)} characters to {max_content_length}")
            content = content[:max_content_length] + "...[Content truncated]"

        prompt = prompt_template.format_messages(
            content=content,
            metadata=metadata,
            format_instructions=parser.get_format_instructions()
        )

        try:
            output = self.llm.invoke(prompt)
            return parser.parse(output.content)
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Return a basic summary on error
            return ContentSummary(
                summary=f"Error generating summary: {str(e)}",
                key_points=["Error occurred during processing"],
                actionable_insights=[],
                priority_score=1.0,
                tags=["error", "processing_failed"]
            )

    def generate_answer(self, query: str, relevant_content: List[Dict[str, Any]]) -> str:
        """
        Generate an answer to a query based on relevant content.

        Args:
            query: The user's query
            relevant_content: List of relevant content pieces

        Returns:
            Answer to the query
        """
        # Format the relevant content
        formatted_content = ""
        for i, content in enumerate(relevant_content):
            formatted_content += f"\n--- Document {i+1} ---\n"
            formatted_content += f"Title: {content.get('title', 'Untitled')}\n"
            formatted_content += f"Content: {content.get('text', '')[:500]}...\n"  # Truncate for prompt space

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a knowledgeable research assistant with access to a personal knowledge base.
            Answer the user's question based on the relevant content provided. Be concise and specific.
            If the provided content doesn't contain enough information to answer the question confidently,
            acknowledge the limitations of your knowledge.

            If appropriate, include specific quotes or references from the content to support your answer.
            """),
            ("user", """Question: {query}

            Here are relevant documents from my knowledge base:
            {formatted_content}

            Please provide a concise, helpful answer based on this information.
            """)
        ])

        prompt = prompt_template.format_messages(
            query=query,
            formatted_content=formatted_content
        )

        try:
            output = self.llm.invoke(prompt)
            return output.content
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return f"I encountered an error while trying to answer your question: {str(e)}"

    def recommend_content(self, user_interests: List[str], recent_content: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Recommend content based on user interests and recent activity.

        Args:
            user_interests: List of user interest topics
            recent_content: List of recently saved content

        Returns:
            List of content recommendations with reasons
        """
        # Format the recent content
        formatted_content = ""
        for i, content in enumerate(recent_content[:5]):  # Limit to 5 recent items
            formatted_content += f"\n--- Recent Item {i+1} ---\n"
            formatted_content += f"Title: {content.get('title', 'Untitled')}\n"
            formatted_content += f"Summary: {content.get('summary', 'No summary available')}\n"
            formatted_content += f"Tags: {', '.join(content.get('tags', []))}\n"

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a personalized content recommendation system.
            Based on the user's interests and recent activity, recommend which content from their library
            they should revisit or prioritize. Provide a brief reason for each recommendation.

            Format your response as a list of recommendations, each with an ID (from the content),
            a title, and a reason for the recommendation.
            """),
            ("user", """User Interests: {interests}

            Recent Activity:
            {recent_content}

            What content should I prioritize revisiting? Provide 3-5 recommendations with reasons.
            """)
        ])

        prompt = prompt_template.format_messages(
            interests=", ".join(user_interests),
            recent_content=formatted_content
        )

        try:
            output = self.llm.invoke(prompt)

            # Parse the output manually
            # This is simplified - a more robust parser would be better
            recommendations = []
            lines = output.content.split("\n")
            current_rec = {}

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or \
                   line.startswith("4.") or line.startswith("5."):
                    if current_rec and "title" in current_rec:
                        recommendations.append(current_rec)
                    current_rec = {"id": f"rec_{len(recommendations) + 1}"}

                    # Extract title
                    title_part = line.split(":", 1)
                    if len(title_part) > 1:
                        current_rec["title"] = title_part[1].strip()
                    else:
                        current_rec["title"] = line.strip()

                elif "reason" in line.lower() and ":" in line:
                    reason_part = line.split(":", 1)
                    if len(reason_part) > 1:
                        current_rec["reason"] = reason_part[1].strip()

                elif current_rec and "reason" not in current_rec:
                    current_rec["reason"] = line

            # Add the last recommendation if it exists
            if current_rec and "title" in current_rec:
                recommendations.append(current_rec)

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return [{"id": "error", "title": "Error", "reason": f"Could not generate recommendations: {str(e)}"}]