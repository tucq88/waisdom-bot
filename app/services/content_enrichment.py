import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import re
from typing import Dict, Any, Optional, Tuple
import logging
from urllib.parse import urlparse

from app.config.settings import CONTENT_TYPES

logger = logging.getLogger(__name__)

class ContentEnrichmentService:
    """Service for extracting and enriching content from various sources."""

    def detect_content_type(self, url: Optional[str] = None,
                           file_extension: Optional[str] = None) -> str:
        """
        Detect the type of content based on URL or file extension.

        Args:
            url: URL of the content
            file_extension: File extension

        Returns:
            Content type
        """
        if url:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()

            # Check for known domains
            if "twitter.com" in domain or "x.com" in domain:
                return CONTENT_TYPES["TWEET"]
            elif "notion.so" in domain:
                return CONTENT_TYPES["NOTION"]
            elif parsed_url.path.lower().endswith(".pdf"):
                return CONTENT_TYPES["PDF"]
            elif re.search(r'\.(jpg|jpeg|png|gif|bmp|webp)$', parsed_url.path.lower()):
                return CONTENT_TYPES["IMAGE"]
            else:
                return CONTENT_TYPES["ARTICLE"]

        if file_extension:
            ext = file_extension.lower().lstrip('.')
            if ext == "pdf":
                return CONTENT_TYPES["PDF"]
            elif ext in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
                return CONTENT_TYPES["IMAGE"]
            elif ext in ["txt", "md", "markdown"]:
                return CONTENT_TYPES["TEXT"]

        return CONTENT_TYPES["OTHER"]

    def extract_from_url(self, url: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Extract content from a URL.

        Args:
            url: URL to extract content from

        Returns:
            Tuple of (title, content, metadata)
        """
        content_type = self.detect_content_type(url=url)

        if content_type == CONTENT_TYPES["ARTICLE"]:
            return self._extract_article(url)
        elif content_type == CONTENT_TYPES["TWEET"]:
            return self._extract_tweet(url)
        elif content_type == CONTENT_TYPES["NOTION"]:
            return self._extract_notion(url)
        elif content_type == CONTENT_TYPES["PDF"]:
            return self._extract_pdf_from_url(url)
        else:
            # Default extraction
            return self._extract_article(url)

    def _extract_article(self, url: str) -> Tuple[str, str, Dict[str, Any]]:
        """Extract content from an article URL."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title = soup.title.text.strip() if soup.title else "Untitled Article"

            # Extract content (simplified version - could be improved with readability parser)
            content = ""

            # Try to find article content
            article = soup.find('article')
            if article:
                content = article.get_text(separator="\n\n")
            else:
                # Fallback to main content or body
                main = soup.find('main') or soup.find('body')
                if main:
                    # Remove script, style, and nav elements
                    for tag in main(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()

                    # Extract paragraphs
                    paragraphs = main.find_all('p')
                    content = "\n\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])

            # Clean up content
            content = re.sub(r'\s+', ' ', content).strip()

            # Extract metadata
            metadata = {
                "url": url,
                "title": title,
                "word_count": len(content.split()),
            }

            # Try to extract author
            author_elem = soup.find('meta', {'name': 'author'}) or soup.find('meta', {'property': 'article:author'})
            if author_elem and author_elem.get('content'):
                metadata["author"] = author_elem.get('content')

            # Try to extract publication date
            date_elem = soup.find('meta', {'name': 'published_time'}) or soup.find('meta', {'property': 'article:published_time'})
            if date_elem and date_elem.get('content'):
                metadata["published_date"] = date_elem.get('content')

            return title, content, metadata

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return "Failed to extract content", f"Error extracting content from {url}: {str(e)}", {"url": url, "error": str(e)}

    def _extract_tweet(self, url: str) -> Tuple[str, str, Dict[str, Any]]:
        """Extract content from a tweet URL."""
        # Note: Twitter/X requires API access or sophisticated scraping which is beyond
        # the scope of this implementation. This is a placeholder.

        title = "Tweet"
        content = f"Tweet content could not be extracted directly. URL: {url}"
        metadata = {
            "url": url,
            "platform": "Twitter/X",
            "note": "Twitter content extraction requires API access"
        }

        return title, content, metadata

    def _extract_notion(self, url: str) -> Tuple[str, str, Dict[str, Any]]:
        """Extract content from a Notion page."""
        # Note: Notion requires API access which is beyond the scope of this implementation.
        # This is a placeholder.

        title = "Notion Page"
        content = f"Notion content could not be extracted directly. URL: {url}"
        metadata = {
            "url": url,
            "platform": "Notion",
            "note": "Notion content extraction requires API access"
        }

        return title, content, metadata

    def _extract_pdf_from_url(self, url: str) -> Tuple[str, str, Dict[str, Any]]:
        """Extract content from a PDF URL."""
        try:
            # Download the PDF
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Extract text from PDF
            pdf_file = io.BytesIO(response.content)
            return self.extract_from_pdf(pdf_file, url)

        except Exception as e:
            logger.error(f"Error extracting content from PDF {url}: {str(e)}")
            return "Failed to extract PDF content", f"Error extracting content from PDF {url}: {str(e)}", {"url": url, "error": str(e)}

    def extract_from_pdf(self, pdf_file, url: Optional[str] = None) -> Tuple[str, str, Dict[str, Any]]:
        """Extract content from a PDF file."""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Extract text from all pages
            content = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                content += page.extract_text() + "\n\n"

            # Try to extract title from the document
            title = "Untitled PDF"
            if pdf_reader.metadata and pdf_reader.metadata.title:
                title = pdf_reader.metadata.title

            # Extract metadata
            metadata = {
                "page_count": len(pdf_reader.pages),
                "word_count": len(content.split()),
            }

            if url:
                metadata["url"] = url

            # Try to extract author
            if pdf_reader.metadata and pdf_reader.metadata.author:
                metadata["author"] = pdf_reader.metadata.author

            return title, content, metadata

        except Exception as e:
            logger.error(f"Error extracting content from PDF: {str(e)}")
            return "Failed to extract PDF content", f"Error extracting PDF content: {str(e)}", {"error": str(e)}

    def extract_from_text(self, text: str, source: Optional[str] = None) -> Tuple[str, str, Dict[str, Any]]:
        """Extract content from plain text."""
        # For plain text, we just need to generate a title and return the content as is

        # Generate a title from the first line or first few words
        lines = text.strip().split('\n')
        first_line = lines[0].strip() if lines else "Untitled Text"

        if len(first_line) > 50:
            title = first_line[:47] + "..."
        else:
            title = first_line

        metadata = {
            "word_count": len(text.split()),
            "line_count": len(lines),
        }

        if source:
            metadata["source"] = source

        return title, text, metadata