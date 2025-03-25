import logging
from typing import List, Dict, Any, Optional
import json
from pydantic import BaseModel, Field
from ragflow_sdk import RAGFlow

from app.config.settings import OPENAI_API_KEY, DEFAULT_AGENT_MODEL, MAX_TOKENS_SUMMARY
from app.config.settings import RAGFLOW_API_URL, RAGFLOW_API_KEY, RAGFLOW_COLLECTION_NAME
from app.models.content_summary import ContentSummary, ContentRecommendation

logger = logging.getLogger(__name__)

class ContentSummary(BaseModel):
    """Model for content summary output."""
    summary: str = Field(description="A concise summary of the content")
    key_points: List[str] = Field(description="Key points from the content")
    actionable_insights: List[str] = Field(description="Actionable insights extracted from the content")
    priority_score: float = Field(description="Priority score from 1-10, with 10 being highest importance")
    tags: List[str] = Field(description="Relevant tags/topics for this content")

class LLMService:
    """Service for LLM-based content processing using RAGFlow."""

    def __init__(self):
        self.ragflow = RAGFlow(
            api_key=RAGFLOW_API_KEY,
            base_url=RAGFLOW_API_URL
        )

        # Get or create the dataset
        datasets = self.ragflow.list_datasets(name=RAGFLOW_COLLECTION_NAME)
        if datasets:
            self.dataset = datasets[0]
        else:
            self.dataset = self.ragflow.create_dataset(name=RAGFLOW_COLLECTION_NAME)

    def summarize_content(self, content: str, metadata: Dict[str, Any]) -> ContentSummary:
        """
        Generate a summary and extract insights from content.

        Args:
            content: The content to summarize
            metadata: Additional metadata about the content

        Returns:
            ContentSummary object with summary and insights
        """
        # Format system and user prompts
        system_message = """You are an expert research assistant. You are analyzing content to extract valuable
        information. For the content provided, create a concise summary, extract key points, and identify
        actionable insights that could be useful for the researcher.

        Also provide a priority score from 1-10, where:
        - 10: Groundbreaking/essential content that represents unique, highly actionable insights
        - 7-9: Very important content with novel information and clear applications
        - 4-6: Moderately useful content with some interesting points
        - 1-3: Basic/common information with limited novelty or application

        Finally, generate 3-7 relevant tags that categorize the content.

        Your response should be in JSON format with these fields:
        {
            "summary": "A concise summary of the content",
            "key_points": ["Key point 1", "Key point 2", ...],
            "actionable_insights": ["Insight 1", "Insight 2", ...],
            "priority_score": 5.0,
            "tags": ["tag1", "tag2", ...]
        }
        """

        user_message = f"""Here is the content to analyze:
        {content[:15000]}  # Truncate content if necessary

        Additional metadata: {json.dumps(metadata)}
        """

        try:
            # Create a chat assistant for the summarization task
            assistant = self.ragflow.create_chat_assistant(
                title="Content Summarizer",
                model=DEFAULT_AGENT_MODEL,
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            # Create a session and send the messages
            session = assistant.create_session(name="summarization")
            response = session.converse(
                system_prompt=system_message,
                user_prompt=user_message
            )

            # Parse the response
            try:
                result = json.loads(response.text)
            except json.JSONDecodeError:
                # If response is not valid JSON, extract content between curly braces
                text = response.text
                start = text.find('{')
                end = text.rfind('}') + 1
                if start >= 0 and end > start:
                    result = json.loads(text[start:end])
                else:
                    raise Exception("Invalid JSON response")

            return ContentSummary(
                summary=result.get("summary", "Summary unavailable"),
                key_points=result.get("key_points", []),
                actionable_insights=result.get("actionable_insights", []),
                priority_score=result.get("priority_score", 1.0),
                tags=result.get("tags", [])
            )
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
        # Format the relevant content as context
        context_docs = []
        for i, content in enumerate(relevant_content):
            context_docs.append({
                "title": content.get('title', f'Document {i+1}'),
                "content": content.get('text', ''),
                "metadata": content.get('metadata', {})
            })

        system_message = """You are a knowledgeable research assistant with access to a personal knowledge base.
        Answer the user's question based on the relevant content provided. Be concise and specific.
        If the provided content doesn't contain enough information to answer the question confidently,
        acknowledge the limitations of your knowledge.

        If appropriate, include specific quotes or references from the content to support your answer.
        """

        try:
            # Create a chat assistant for the Q&A task
            assistant = self.ragflow.create_chat_assistant(
                title="Q&A Assistant",
                model=DEFAULT_AGENT_MODEL,
                temperature=0.1
            )

            # Create a session and send the messages with context
            session = assistant.create_session(name="qa")
            response = session.converse(
                system_prompt=system_message,
                user_prompt=query,
                context_docs=context_docs
            )

            return response.text
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

        system_message = """You are a personalized content recommendation system.
        Based on the user's interests and recent activity, recommend which content from their library
        they should revisit or prioritize. Provide a brief reason for each recommendation.

        Format your response as a JSON list of recommendations, each with an 'id', 'title', and 'reason' field.
        """

        user_message = f"""User Interests: {", ".join(user_interests)}

        Recent Activity:
        {formatted_content}

        What content should I prioritize revisiting? Provide 3-5 recommendations with reasons.
        """

        try:
            # Create a chat assistant for recommendations
            assistant = self.ragflow.create_chat_assistant(
                title="Content Recommender",
                model=DEFAULT_AGENT_MODEL,
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            # Create a session and get recommendations
            session = assistant.create_session(name="recommendations")
            response = session.converse(
                system_prompt=system_message,
                user_prompt=user_message
            )

            # Parse the response
            try:
                text = response.text
                start = text.find('[')
                end = text.rfind(']') + 1
                if start >= 0 and end > start:
                    recommendations = json.loads(text[start:end])
                else:
                    raise Exception("Invalid JSON response")
            except json.JSONDecodeError:
                recommendations = []

            # Ensure the response is a list
            if not isinstance(recommendations, list):
                recommendations = []

            # Add IDs if missing
            for i, rec in enumerate(recommendations):
                if "id" not in rec:
                    rec["id"] = f"rec_{i+1}"

            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return [{"id": "error", "title": "Error", "reason": f"Could not generate recommendations: {str(e)}"}]