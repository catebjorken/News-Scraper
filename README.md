# News Scraper

A Python-based news aggregator that searches and scrapes articles from multiple news sources using RSS feeds. Extracts full article content, performs NLP analysis, and saves results in structured formats.

## Features

- RSS feed-based article discovery (reliable, no blocking)
- Keyword filtering across multiple news sources
- Full article content extraction with newspaper3k
- Automatic text cleaning and summarization
- NLP keyword extraction with NLTK
- JSON output for data processing

## Supported News Sources

- CNN
- BBC News
- Al Jazeera
- NPR
- The Guardian

## Installation

1. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the interactive scraper:
```bash
python news_scraper_v2.py
```

Enter a keyword when prompted (e.g., "technology", "climate change") and specify the maximum number of articles per source.

## Programmatic Usage

```python
from news_scraper_v2 import NewsScraperV2

scraper = NewsScraperV2()
articles = scraper.search_rss_feeds('artificial intelligence', max_articles_per_source=5)
scraper.display_results(articles)
scraper.save_to_json(articles, 'ai_articles.json')
```

## Output Structure

Each article contains:
- URL and title
- Authors and publish date
- Full text content (cleaned)
- Auto-generated summary
- Extracted keywords
- Source and metadata

Results are saved to `scraped_articles/` directory in JSON format.

