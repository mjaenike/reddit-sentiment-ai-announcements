import praw
import csv
from datetime import datetime, timezone, timedelta
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

"""
Reddit Google Gemini Data Collector - IMPROVED VERSION

Key improvements over previous version:
1. STRICT RELEVANCE FILTERING: Posts must mention Google/Gemini/Bard-specific terms
2. COMPETITOR EXCLUSION: Filters out posts about ChatGPT, Claude, Meta LLaMA, etc.
3. ENHANCED DEDUPLICATION: Better tracking of duplicate posts
4. RELEVANCE SCORING: Only keeps highly relevant posts

This prevents collecting posts about OpenAI, Anthropic, or Meta
when searching for Google Gemini content.

Expected runtime: 6-8 hours
Expected data: 600-1500 RELEVANT posts + comprehensive comments

Setup Instructions:
1. Install dependencies: pip install praw python-dotenv
2. Create Reddit app: https://www.reddit.com/prefs/apps/ (choose "script" type)
3. Create .env file in this directory with:
   REDDIT_CLIENT_ID=your_client_id_here
   REDDIT_CLIENT_SECRET=your_client_secret_here
   REDDIT_USER_AGENT=YourAppName/1.0 by YourRedditUsername
4. Run: python google_collector_improved.py
"""

class RedditCollector:
    def __init__(self, client_id, client_secret, user_agent):
        """Initialize Reddit API client"""
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            # Test the connection
            self.reddit.user.me()
            print("✅ Successfully connected to Reddit API")
        except Exception as e:
            print(f"❌ Failed to connect to Reddit API: {e}")
            print("💡 Make sure you've registered an app at https://www.reddit.com/prefs/apps/")
            self.reddit = None
    
    def is_relevant_to_google(self, title, text):
        """
        STRICT relevance check: Post must mention Google/Gemini/Bard-specific terms
        AND should not be primarily about competitors
        """
        title_lower = title.lower()
        text_lower = text.lower()
        combined = title_lower + " " + text_lower
        
        # REQUIRED: Must mention Google, Gemini, or Bard
        google_terms = [
            'google', 'gemini', 'bard', 'google\'s', 'googles',
            'sundar pichai', 'deepmind', 'palm', 'lamda'
        ]
        
        has_google = any(term in combined for term in google_terms)
        
        if not has_google:
            return False
        
        # EXCLUSION: Filter out posts primarily about competitors
        # These indicate the post is mainly about another company
        competitor_indicators = [
            'openai', 'chatgpt', 'gpt-4', 'gpt-3', 'sam altman',
            'anthropic', 'claude', 'anthropic\'s',
            'meta llama', 'meta\'s llama', 'facebook llama', 'zuckerberg llama',
            'microsoft copilot', 'bing chat',
            'amazon bedrock',
            'mistral ai', 'inflection ai'
        ]
        
        # Check if competitor is mentioned prominently (in title or early in text)
        title_and_start = title_lower + " " + text_lower[:200]
        has_competitor_focus = any(term in title_and_start for term in competitor_indicators)
        
        if has_competitor_focus:
            # Allow if Google/Gemini/Bard is also prominently mentioned (comparison posts)
            google_prominent = any(term in title_lower for term in google_terms)
            if not google_prominent:
                return False
        
        return True
    
    def search_posts(self, query, start_date, end_date, subreddits=None, max_posts=1000, seen_ids=None):
        """Search for posts with strict relevance filtering"""
        if not self.reddit:
            print("❌ Reddit client not initialized")
            return []
        
        if seen_ids is None:
            seen_ids = set()
        
        all_posts = []
        
        # Determine which subreddits to search
        if subreddits is None:
            subreddits = ["all"]
        
        # Create keyword list for post-processing filter (case-insensitive)
        query_keywords = [word.lower().strip() for word in query.split() if len(word) > 2]
        
        for subreddit_name in subreddits:
            print(f"🔍 Searching r/{subreddit_name} for '{query}'")
            
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                search_methods = [
                    ("new", "newest first"),
                    ("top", "most popular")
                ]
                
                for sort_method, description in search_methods:
                    print(f"  📊 Searching by {description}...")
                    
                    search_results = subreddit.search(
                        query,
                        sort=sort_method,
                        time_filter="all",
                        limit=150
                    )
                    
                    posts_found = 0
                    posts_filtered = 0
                    
                    for submission in search_results:
                        # Check if we've seen this post before
                        if submission.id in seen_ids:
                            continue
                        
                        post_date = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
                        
                        # Filter by date range
                        if start_date <= post_date <= end_date:
                            # STRICT RELEVANCE CHECK
                            if not self.is_relevant_to_google(submission.title, submission.selftext):
                                posts_filtered += 1
                                continue
                            
                            # Additional keyword matching
                            title_lower = submission.title.lower()
                            selftext_lower = submission.selftext.lower()
                            query_lower = query.lower()
                            
                            content_match = any(
                                keyword in title_lower or keyword in selftext_lower 
                                for keyword in query_keywords
                            )
                            
                            if content_match or query_lower in title_lower or query_lower in selftext_lower:
                                post_data = self.extract_post_data(submission)
                                all_posts.append(post_data)
                                seen_ids.add(submission.id)
                                posts_found += 1
                                
                                if len(all_posts) >= max_posts:
                                    print(f"🎯 Reached maximum posts limit ({max_posts})")
                                    return all_posts, seen_ids
                    
                    if posts_found > 0 or posts_filtered > 0:
                        print(f"     Found {posts_found} relevant posts (filtered {posts_filtered} irrelevant)")
                    
                    time.sleep(0.3)
            
            except Exception as e:
                print(f"❌ Error searching r/{subreddit_name}: {e}")
                continue
        
        print(f"✅ Total posts collected: {len(all_posts)}")
        return all_posts, seen_ids
    
    def extract_post_data(self, submission):
        """Extract relevant data from a Reddit post"""
        return {
            'id': submission.id,
            'title': submission.title,
            'text': submission.selftext,
            'author': str(submission.author) if submission.author else '[deleted]',
            'subreddit': submission.subreddit.display_name,
            'created_at': datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).isoformat(),
            'score': submission.score,
            'upvote_ratio': submission.upvote_ratio,
            'num_comments': submission.num_comments,
            'url': submission.url,
            'permalink': f"https://reddit.com{submission.permalink}",
            'is_self': submission.is_self,
            'domain': submission.domain,
            'gilded': submission.gilded,
            'over_18': submission.over_18
        }
    
    def collect_comments_from_posts(self, posts, start_date, end_date, max_comments_per_post=None, query_keywords=None):
        """Collect comments from a list of posts"""
        print("\n💬 Collecting comments from high-value posts...")
        print(f"   Processing {len(posts)} posts for comment collection")
        
        all_comments = []
        seen_comment_ids = set()
        
        for i, post_data in enumerate(posts, 1):
            print(f"   🔎 [{i}/{len(posts)}] Getting comments from: {post_data['title'][:50]}... (r/{post_data['subreddit']}, {post_data['num_comments']} comments)")
            
            try:
                submission = self.reddit.submission(id=post_data['id'])
                submission.comments.replace_more(limit=0)
                
                comments_collected = 0
                for comment in submission.comments.list():
                    if hasattr(comment, 'created_utc') and hasattr(comment, 'body'):
                        # Skip if we've seen this comment
                        if comment.id in seen_comment_ids:
                            continue
                        
                        comment_date = datetime.fromtimestamp(comment.created_utc, tz=timezone.utc)
                        
                        if start_date <= comment_date <= end_date:
                            if query_keywords:
                                comment_body_lower = comment.body.lower()
                                keyword_match = any(
                                    keyword in comment_body_lower 
                                    for keyword in query_keywords
                                )
                                if not keyword_match:
                                    continue
                            
                            comment_data = {
                                'id': comment.id,
                                'post_id': post_data['id'],
                                'post_title': post_data['title'],
                                'text': comment.body,
                                'author': str(comment.author) if comment.author else '[deleted]',
                                'subreddit': post_data['subreddit'],
                                'created_at': comment_date.isoformat(),
                                'score': comment.score,
                                'permalink': f"https://reddit.com{comment.permalink}",
                                'is_submitter': comment.is_submitter
                            }
                            all_comments.append(comment_data)
                            seen_comment_ids.add(comment.id)
                            comments_collected += 1
                            
                            if max_comments_per_post and comments_collected >= max_comments_per_post:
                                break
                
                if comments_collected > 0:
                    print(f"      ✓ Collected {comments_collected} comments")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"      ❌ Error processing post {post_data['id']}: {e}")
                continue
        
        print(f"✅ Total comments collected: {len(all_comments)}")
        return all_comments
    
    def save_to_csv(self, data, filename, data_type="posts"):
        """Save data to CSV file"""
        if not data:
            print("❌ No data to save")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if data_type == "posts":
                fieldnames = [
                    'id', 'title', 'text', 'author', 'subreddit', 'created_at',
                    'score', 'upvote_ratio', 'num_comments', 'url', 'permalink',
                    'is_self', 'domain', 'gilded', 'over_18'
                ]
            else:  # comments
                fieldnames = [
                    'id', 'post_id', 'post_title', 'text', 'author', 'subreddit',
                    'created_at', 'score', 'permalink', 'is_submitter'
                ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in data:
                writer.writerow(item)
        
        print(f"✅ Saved {len(data)} {data_type} to {filename}")

def main():
    # Load Reddit API credentials
    CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    USER_AGENT = os.getenv('REDDIT_USER_AGENT')
    
    # Validate credentials
    missing_vars = []
    if not CLIENT_ID:
        missing_vars.append('REDDIT_CLIENT_ID')
    if not CLIENT_SECRET:
        missing_vars.append('REDDIT_CLIENT_SECRET')
    if not USER_AGENT:
        missing_vars.append('REDDIT_USER_AGENT')
    
    if missing_vars:
        print("❌ Missing required environment variables in .env file:")
        for var in missing_vars:
            print(f"   • {var}")
        return
    
    print("✅ Successfully loaded credentials from .env file")
    print(f"📱 User Agent: {USER_AGENT}")
    print(f"🔑 Client ID: {CLIENT_ID[:8]}{'*' * (len(CLIENT_ID) - 8) if len(CLIENT_ID) > 8 else ''}")
    print()
    
    # Initialize collector
    collector = RedditCollector(CLIENT_ID, CLIENT_SECRET, USER_AGENT)
    
    if not collector.reddit:
        return
    
    # DATE RANGE: Google Gemini announcement
    announcement_date = datetime(2023, 12, 6, tzinfo=timezone.utc)
    start_date = announcement_date - timedelta(days=14)  # November 22, 2023
    end_date = announcement_date + timedelta(days=14)    # December 20, 2023
    
    print(f"📅 COLLECTION PERIOD: {start_date.date()} to {end_date.date()} (4 weeks total)")
    print("🎯 Google Gemini announcement: December 6, 2023")
    print("🎯 IMPROVED VERSION: Strict relevance filtering + deduplication")
    print()
    
    # FOCUSED SEARCH TERMS - Prioritize Google/Gemini-specific terms
    search_terms = [
    "Google",
    "GOOGL",
    "Alphabet",
    "Google Bard",
    "Google AI",
    "Google Assistant",
    "Google Gemini",
    "Gemini AI",
    "Gemini Pro",
    "Gemini Ultra",
    "Gemini announcement",
    "Gemini Google",
    "Google Bard Gemini",
    "Bard Gemini",
    "Bard powered by Gemini",
    "Google Bard update",
    "Google AI model",
    "Google LLM",
    "Google language model",
    "PaLM 2 Google",
    "Gemini in Bard",
    "Gemini API",
    "Gemini benchmark",
    "Google artificial intelligence",
    "Google search",
    "Google LLM",
    "Google products",
    "Google update"
    ]
    
    # TARGETED SUBREDDITS
    target_subreddits = [
        # Core Google
        "google", "GooglePixel", "Android",
        
        # Major tech
        "technology", "gadgets", "tech", "news",
        
        # AI/ML
        "artificial", "ArtificialInteligence", "MachineLearning",
        "singularity", "LocalLLaMA",
        
        # Developer communities
        "programming", "webdev",
        
        # General discussion
        "futurology",
        
        # Financial
        "investing", "stocks"
    ]
    
    # Remove duplicates
    search_terms = list(set(search_terms))
    target_subreddits = list(set(target_subreddits))
    
    print(f"🔍 Search terms: {len(search_terms)} Google/Gemini-focused terms")
    print(f"🎯 Target subreddits: {len(target_subreddits)}")
    print(f"🎯 Strategy:")
    print(f"   1. STRICT relevance filtering (must mention Google/Gemini/Bard)")
    print(f"   2. Competitor exclusion (filters OpenAI, Anthropic, Meta, etc.)")
    print(f"   3. Enhanced deduplication across all searches")
    print(f"📊 Expected: 600-1,500 RELEVANT posts + comprehensive comments")
    print()
    
    start_time = time.time()
    all_posts = []
    global_seen_ids = set()  # Track ALL post IDs across all searches
    
    # PHASE 1: Post collection with global deduplication
    print("=" * 60)
    print("PHASE 1: COLLECTING POSTS (WITH STRICT FILTERING)")
    print("=" * 60)
    
    for i, term in enumerate(search_terms, 1):
        print(f"\n🔍 [{i}/{len(search_terms)}] Searching for: '{term}'")
        posts, global_seen_ids = collector.search_posts(
            term, start_date, end_date, target_subreddits, 
            max_posts=2000, seen_ids=global_seen_ids
        )
        all_posts.extend(posts)
        
        print(f"📊 Running total: {len(all_posts)} unique posts")
        time.sleep(0.5)
    
    print(f"\n✅ Phase 1 complete: {len(all_posts)} unique, relevant posts collected")
    
    # PHASE 2: Comment collection from high-value posts
    print("\n" + "=" * 60)
    print("PHASE 2: COLLECTING COMMENTS FROM HIGH-VALUE POSTS")
    print("=" * 60)
    
    # Top by score
    top_by_score = sorted(all_posts, key=lambda x: x['score'], reverse=True)[:50]
    print(f"\n📊 Top 50 posts by score:")
    for post in top_by_score[:5]:
        print(f"   • [{post['score']}⬆️] {post['title'][:60]}... (r/{post['subreddit']})")
    
    # Top by comment count
    top_by_comments = sorted(all_posts, key=lambda x: x['num_comments'], reverse=True)[:50]
    print(f"\n💬 Top 50 posts by comment count:")
    for post in top_by_comments[:5]:
        print(f"   • [{post['num_comments']} comments] {post['title'][:60]}... (r/{post['subreddit']})")
    
    # Combine and deduplicate
    high_value_posts = []
    seen_comment_post_ids = set()
    
    for post in top_by_score + top_by_comments:
        if post['id'] not in seen_comment_post_ids:
            high_value_posts.append(post)
            seen_comment_post_ids.add(post['id'])
    
    print(f"\n🎯 Collecting comments from {len(high_value_posts)} high-value posts")
    
    # Google-specific keywords for comment filtering
    general_keywords = ["gemini", "google", "bard", "ai", "model", "llm"]
    
    all_comments = collector.collect_comments_from_posts(
        high_value_posts, 
        start_date, 
        end_date,
        max_comments_per_post=200,
        query_keywords=general_keywords
    )
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"   • Posts: {len(all_posts)} unique, relevant posts")
    print(f"   • Comments: {len(all_comments)} unique comments")
    print(f"   • TOTAL CONTENT: {len(all_posts) + len(all_comments)} pieces")
    print(f"   • Runtime: {elapsed_time/3600:.1f} hours ({elapsed_time/60:.0f} minutes)")
    
    # Sort by creation date
    all_posts.sort(key=lambda x: x['created_at'])
    all_comments.sort(key=lambda x: x['created_at'])
    
    # Save to CSV
    posts_filename = f"google_gemini_reddit_posts_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_CLEAN.csv"
    comments_filename = f"google_gemini_reddit_comments_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_CLEAN.csv"
    
    collector.save_to_csv(all_posts, posts_filename, "posts")
    if all_comments:
        collector.save_to_csv(all_comments, comments_filename, "comments")
    
    # Summary stats
    if all_posts:
        print(f"\n📈 Collection Summary:")
        print(f"   • Total posts: {len(all_posts)}")
        print(f"   • Total comments: {len(all_comments)}")
        print(f"   • Date range: {all_posts[0]['created_at'][:10]} to {all_posts[-1]['created_at'][:10]}")
        print(f"   • Average score: {sum(p['score'] for p in all_posts) / len(all_posts):.1f}")
        
        # Top posts
        top_posts = sorted(all_posts, key=lambda x: x['score'], reverse=True)[:5]
        print(f"\n🏆 Top posts by score:")
        for post in top_posts:
            comments_collected = len([c for c in all_comments if c['post_id'] == post['id']])
            print(f"   • [{post['score']}⬆️] {post['title'][:70]}...")
            print(f"     └─ {comments_collected} comments collected from this post")
            
        # Timeline analysis
        dec_6_posts = [p for p in all_posts if '2023-12-06' in p['created_at']]
        print(f"\n📅 Timeline Analysis:")
        print(f"   • Posts on announcement day (Dec 6): {len(dec_6_posts)}")
        print(f"   • Pre-announcement (before Dec 6): {len([p for p in all_posts if p['created_at'] < '2023-12-06'])}")
        print(f"   • Post-announcement (after Dec 6): {len([p for p in all_posts if p['created_at'] > '2023-12-07'])}")
        
        # Bard vs Gemini breakdown
        bard_posts = [p for p in all_posts if 'bard' in p['title'].lower()]
        gemini_posts = [p for p in all_posts if 'gemini' in p['title'].lower()]
        print(f"\n🔤 Term Analysis:")
        print(f"   • Posts mentioning 'Bard' in title: {len(bard_posts)}")
        print(f"   • Posts mentioning 'Gemini' in title: {len(gemini_posts)}")
        
    print(f"\n🎯 IMPROVED VERSION Complete! Runtime: {elapsed_time/3600:.1f} hours")
    print(f"💾 Files saved: {posts_filename}, {comments_filename if all_comments else 'no comments file'}")
    print("\n✅ All posts are now relevant to Google/Gemini/Bard and duplicates removed!")

if __name__ == "__main__":
    main()
