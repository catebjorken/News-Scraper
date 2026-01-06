"""
News Scraper V2 - Uses RSS feeds and alternative methods
More reliable than web scraping search pages which often block bots
"""

import requests
from bs4 import BeautifulSoup
from newspaper import Article, Config
from datetime import datetime
import json
import os
from typing import List, Dict, Optional
import re
import time
import feedparser
import nltk
from pathlib import Path


# Download required NLTK data
def setup_nltk():
    """Download required NLTK resources."""
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        print("Downloading required NLP resources...")
        try:
            nltk.download('punkt_tab', quiet=True)
            nltk.download('punkt', quiet=True)
        except Exception:
            pass

setup_nltk()


# News sources with RSS feeds
NEWS_SOURCES = {
    'CNN': {
        'rss': 'http://rss.cnn.com/rss/cnn_topstories.rss',
        'world': 'http://rss.cnn.com/rss/cnn_world.rss',
    },
    'BBC News': {
        'rss': 'http://feeds.bbci.co.uk/news/rss.xml',
        'world': 'http://feeds.bbci.co.uk/news/world/rss.xml',
    },
    'Al Jazeera': {
        'rss': 'https://www.aljazeera.com/xml/rss/all.xml',
    },
    'NPR': {
        'rss': 'https://feeds.npr.org/1001/rss.xml',
    },
    'The Guardian': {
        'rss': 'https://www.theguardian.com/world/rss',
    },
}


class NewsScraperV2:
    """
    Enhanced news scraper using RSS feeds and direct article URLs.
    """
    
    def __init__(self, user_agent: str = None):
        """Initialize the scraper."""
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        
        # Configure newspaper3k
        self.config = Config()
        self.config.browser_user_agent = self.user_agent
        self.config.request_timeout = 15
        self.config.fetch_images = False
        
    def scrape_article(self, url: str) -> Optional[Dict]:
        """Scrape a single article."""
        try:
            article = Article(url, config=self.config)
            article.download()
            article.parse()
            
            try:
                article.nlp()
            except:
                pass
            
            # Clean content
            text = article.text
            summary = article.summary if hasattr(article, 'summary') else ''
            
            # Remove ad patterns
            ad_patterns = [
                r'How relevant is this ad to you\?.*?Other',
                r'Video player was slow to load content.*?Other',
                r'Advertisement\s*',
            ]
            
            for pattern in ad_patterns:
                text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
                summary = re.sub(pattern, '', summary, flags=re.DOTALL | re.IGNORECASE)
            
            text = re.sub(r'\n\s*\n', '\n\n', text.strip())
            summary = re.sub(r'\n\s*\n', '\n\n', summary.strip())
            
            return {
                'url': url,
                'title': article.title,
                'authors': article.authors,
                'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                'text': text,
                'summary': summary,
                'keywords': article.keywords if hasattr(article, 'keywords') else [],
                'top_image': article.top_image,
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            return None
    
    def search_rss_feeds(self, keyword: str, max_articles_per_source: int = 5) -> List[Dict]:
        """
        Search for articles in RSS feeds by keyword.
        
        Args:
            keyword: Search keyword
            max_articles_per_source: Max articles per source
            
        Returns:
            List of matching articles
        """
        print(f"\nSearching RSS feeds for: '{keyword}'")
        print(f"Checking {len(NEWS_SOURCES)} news sources...\n")
        
        all_articles = []
        keyword_lower = keyword.lower()
        
        for source_name, feeds in NEWS_SOURCES.items():
            print(f"\n{'='*60}")
            print(f"{source_name}")
            print(f"{'='*60}")
            
            source_articles = []
            
            try:
                # Check all RSS feeds for this source
                for feed_name, feed_url in feeds.items():
                    if len(source_articles) >= max_articles_per_source:
                        break
                    
                    print(f"  Parsing {feed_name} RSS feed...")
                    feed = feedparser.parse(feed_url)
                    
                    if not feed.entries:
                        continue
                    
                    # Filter entries by keyword
                    matching_entries = []
                    for entry in feed.entries:
                        title = entry.get('title', '').lower()
                        summary = entry.get('summary', '').lower()
                        
                        if keyword_lower in title or keyword_lower in summary:
                            matching_entries.append(entry)
                    
                    print(f"  Found {len(matching_entries)} matching entries in feed")
                    
                    # Scrape matching articles
                    for entry in matching_entries[:max_articles_per_source - len(source_articles)]:
                        if len(source_articles) >= max_articles_per_source:
                            break
                        
                        url = entry.get('link', '')
                        if not url:
                            continue
                        
                        print(f"  Scraping: {entry.get('title', '')[:50]}...")
                        article = self.scrape_article(url)
                        
                        if article and len(article.get('text', '')) > 200:
                            article['source'] = source_name
                            article['search_keyword'] = keyword
                            article['rss_title'] = entry.get('title', '')
                            article['rss_published'] = entry.get('published', '')
                            source_articles.append(article)
                            print(f"  ✓ [{len(source_articles)}] Scraped successfully")
                        
                        time.sleep(0.3)
                
                all_articles.extend(source_articles)
                print(f"\n  Got {len(source_articles)} articles from {source_name}")
                
            except Exception as e:
                print(f"Error with {source_name}: {str(e)}")
                continue
        
        print(f"\n{'='*60}")
        print(f"Total articles found: {len(all_articles)}")
        print(f"{'='*60}\n")
        
        return all_articles
    
    def display_results(self, articles: List[Dict]):
        """Display search results."""
        if not articles:
            print("❌ No articles found.")
            return
        
        print(f"\n{'='*80}")
        print(f"SEARCH RESULTS - {len(articles)} Articles")
        print(f"{'='*80}\n")
        
        for i, article in enumerate(articles, 1):
            print(f"\n[{i}] {article['title']}")
            print(f"    Source: {article.get('source', 'Unknown')}")
            print(f"    Published: {article.get('publish_date') or article.get('rss_published', 'Unknown')}")
            if article.get('summary'):
                print(f"    Summary: {article['summary'][:200]}...")
            print(f"    URL: {article['url']}")
            print(f"    {'-'*76}")
    
    def save_to_json(self, articles: List[Dict], filename: str):
        """Save articles to JSON."""
        os.makedirs('scraped_articles', exist_ok=True)
        filepath = os.path.join('scraped_articles', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved {len(articles)} articles to {filepath}")


def main():
    """Main CLI interface."""
    print("\n" + "="*80)
    print("NEWS SCRAPER V2 - RSS Feed Search")
    print("="*80)
    print("\nUsing RSS feeds from:")
    for source in NEWS_SOURCES.keys():
        print(f"  • {source}")
    print("\nThis version is more reliable as RSS feeds are meant for automated access!")
    print("-"*80)
    
    keyword = input("\nEnter a keyword to search for: ").strip()
    
    if not keyword:
        print("No keyword entered.")
        return
    
    try:
        max_articles = input("\nMaximum articles per source (default 5): ").strip()
        max_articles = int(max_articles) if max_articles else 5
    except ValueError:
        max_articles = 5
    
    print(f"\n{'='*80}")
    print(f"Starting RSS feed search for: '{keyword}'")
    print(f"{'='*80}")
    
    scraper = NewsScraperV2()
    articles = scraper.search_rss_feeds(keyword, max_articles_per_source=max_articles)
    
    if articles:
        scraper.display_results(articles)
        
        save = input("\nSave results? (y/n): ").strip().lower()
        if save == 'y':
            filename = keyword.replace(' ', '_').lower() + '_articles.json'
            scraper.save_to_json(articles, filename)
            print("\nSaved successfully!")
        
        print(f"\nFound {len(articles)} articles about '{keyword}'!\n")
    else:
        print(f"\nNo articles found for '{keyword}'")
        print("Try a more common keyword or check your internet connection.\n")


if __name__ == "__main__":
    main()
