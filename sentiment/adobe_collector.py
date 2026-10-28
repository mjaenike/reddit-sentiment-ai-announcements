import praw
import csv
from datetime import datetime, timezone, timedelta
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

"""
Reddit Adobe Firefly Data Collector - REVISED VERSION

Event: Adobe Firefly announcement - March 21, 2023
Expected runtime: ~30-45 minutes
Expected data: 300-800 relevant posts + comments

This collector uses broader search terms to capture natural discussion:
- More general terms and product-specific terms
- Expanded subreddit list including creative communities
- Relaxed relevance filtering (allows comparison posts)
- Still maintains deduplication

⚠️ NOTE: Adobe Q1 2023 earnings were on March 15 (6 days before)
This is a potential confound but included for completeness.

Setup Instructions:
1. Use the same .env file with Reddit API credentials
2. Run: python adobe_collector.py
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
    
    def is_relevant_to_adobe(self, title, text):
        """
        RELAXED relevance check: Post must mention Adobe-related terms
        More permissive to capture varied discussion styles including comparisons
        """
        title_lower = title.lower()
        text_lower = text.lower()
        combined = title_lower + " " + text_lower
        
        # REQUIRED: Must mention Adobe (using broader terms)
        adobe_terms = [
            'adobe', 'firefly', 'photoshop', 'illustrator',
            'adobe\'s', 'shantanu narayen'
        ]
        
        has_adobe = any(term in combined for term in adobe_terms)
        
        if not has_adobe:
            return False
        
        # ONLY exclude if it's CLEARLY not about Adobe
        # (comparison posts like "Adobe vs Midjourney" are valuable!)
        strong_competitor_indicators = [
            'midjourney only', 'dalle only', 'stable diffusion only',
            'not adobe', 'except adobe', 'besides adobe'
        ]
        
        # Only reject if it's explicitly NOT about Adobe
        title_and_start = title_lower + " " + text_lower[:200]
        clearly_not_adobe = any(term in title_and_start for term in strong_competitor_indicators)
        
        if clearly_not_adobe:
            return False
        
        return True
    
    def search_posts(self, query, start_date, end_date, subreddits=None, max_posts=500, seen_ids=None):
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
                        limit=100  # Increased from 75
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
                            # RELAXED RELEVANCE CHECK (allows comparison posts)
                            if not self.is_relevant_to_adobe(submission.title, submission.selftext):
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
                    
                    time.sleep(0.2)  # Reduced sleep time
            
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
    
    def collect_comments_from_posts(self, posts, start_date, end_date, max_comments_per_post=100, query_keywords=None):
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
                
                time.sleep(0.3)  # Reduced sleep time
                
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
    # Load Reddit API credentials from environment variables
    CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    USER_AGENT = os.getenv('REDDIT_USER_AGENT')
    
    # Validate required credentials
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
    
    # DATE RANGE: Adobe Firefly announcement
    announcement_date = datetime(2023, 3, 21, tzinfo=timezone.utc)
    start_date = announcement_date - timedelta(days=14)  # March 7, 2023
    end_date = announcement_date + timedelta(days=14)    # April 4, 2023
    
    print(f"📅 COLLECTION PERIOD: {start_date.date()} to {end_date.date()} (4 weeks total)")
    print("🎯 Adobe Firefly announcement: March 21, 2023")
    print("⚠️  NOTE: Adobe Q1 earnings on March 15 (6 days before)")
    print("🔄 REVISED VERSION: Broader search terms, relaxed filtering")
    print()
    
    # BROADER SEARCH TERMS - More natural language
    search_terms = [
    "Adobe",
    "ADBE",
    "Adobe Creative Cloud",
    "Adobe Photoshop",
    "Adobe Illustrator",
    "Adobe AI",
    "Adobe artificial intelligence",
    "Adobe generative AI",
    "Adobe Firefly",
    "Firefly Adobe",
    "Photoshop AI",
    "Illustrator AI",
    "Adobe AI image",
    "Adobe AI generator",
    "Adobe generative",
    "Adobe AI tool",
    "Adobe new AI",
    "Adobe AI feature",
    "Adobe vs Midjourney",
    "Adobe vs DALLE",
    "Adobe image generation",
    "Adobe creative",
    "Adobe design"
    ]
    
    # EXPANDED SUBREDDITS - Cast wider net
    target_subreddits = [
        # Core Adobe
        "Adobe", "photoshop", "AdobeIllustrator",
        
        # Design/Creative communities
        "graphic_design", "design", "photography", 
        "DigitalArt", "Art", "creativecoding",
        
        # Major tech (likely to discuss any tech company's AI)
        "technology", "tech", "gadgets", "technews",
        
        # AI/ML (will discuss all AI features)
        "artificial", "ArtificialInteligence", 
        "StableDiffusion", "MediaSynthesis",
        
        # General discussion
        "news", "worldnews",
        
        # Marketing/business perspective
        "marketing", "advertising"
    ]
    
    # Remove duplicates
    search_terms = list(set(search_terms))
    target_subreddits = list(set(target_subreddits))
    
    print(f"🔍 Search terms: {len(search_terms)} Adobe-focused terms")
    print(f"🎯 Target subreddits: {len(target_subreddits)}")
    print(f"📊 Expected: 300-800 relevant posts + comments (broader search)")
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
            max_posts=500, seen_ids=global_seen_ids
        )
        all_posts.extend(posts)
        
        print(f"📊 Running total: {len(all_posts)} unique posts")
        time.sleep(0.3)
    
    print(f"\n✅ Phase 1 complete: {len(all_posts)} unique, relevant posts collected")
    
    # PHASE 2: Comment collection from high-value posts
    print("\n" + "=" * 60)
    print("PHASE 2: COLLECTING COMMENTS FROM HIGH-VALUE POSTS")
    print("=" * 60)
    
    # Top by score
    top_by_score = sorted(all_posts, key=lambda x: x['score'], reverse=True)[:30]  # Reduced from 50
    print(f"\n📊 Top 30 posts by score:")
    for post in top_by_score[:5]:
        print(f"   • [{post['score']}⬆️] {post['title'][:60]}... (r/{post['subreddit']})")
    
    # Top by comment count
    top_by_comments = sorted(all_posts, key=lambda x: x['num_comments'], reverse=True)[:30]
    print(f"\n💬 Top 30 posts by comment count:")
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
    
    # Adobe-specific keywords for comment filtering
    general_keywords = ["adobe", "firefly", "ai", "photoshop", "illustrator", "generative"]
    
    all_comments = collector.collect_comments_from_posts(
        high_value_posts, 
        start_date, 
        end_date,
        max_comments_per_post=100,  # Reduced from 200
        query_keywords=general_keywords
    )
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"   • Posts: {len(all_posts)} unique, relevant posts")
    print(f"   • Comments: {len(all_comments)} unique comments")
    print(f"   • TOTAL CONTENT: {len(all_posts) + len(all_comments)} pieces")
    print(f"   • Runtime: {elapsed_time/60:.1f} minutes")
    
    # Sort by creation date
    all_posts.sort(key=lambda x: x['created_at'])
    all_comments.sort(key=lambda x: x['created_at'])
    
    # Save to CSV files
    posts_filename = f"adobe_firefly_reddit_posts_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_CLEAN.csv"
    comments_filename = f"adobe_firefly_reddit_comments_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_CLEAN.csv"
    
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
        
        # Show top posts
        top_posts = sorted(all_posts, key=lambda x: x['score'], reverse=True)[:3]
        print(f"\n🏆 Top posts by score:")
        for post in top_posts:
            comments_collected = len([c for c in all_comments if c['post_id'] == post['id']])
            print(f"   • [{post['score']}⬆️] {post['title'][:70]}...")
            print(f"     └─ {comments_collected} comments collected from this post")
            
        # Timeline analysis
        march_21_posts = [p for p in all_posts if '2023-03-21' in p['created_at']]
        earnings_posts = [p for p in all_posts if '2023-03-15' in p['created_at']]
        print(f"\n📅 Timeline Analysis:")
        print(f"   • Posts on announcement day (March 21): {len(march_21_posts)}")
        print(f"   • Posts on earnings day (March 15): {len(earnings_posts)}")
        print(f"   • Pre-announcement (before March 21): {len([p for p in all_posts if p['created_at'] < '2023-03-21'])}")
        print(f"   • Post-announcement (after March 21): {len([p for p in all_posts if p['created_at'] > '2023-03-22'])}")
        
        if earnings_posts:
            print(f"\n   ⚠️  Found {len(earnings_posts)} posts on earnings day - potential confound!")
        
    print(f"\n🎯 REVISED VERSION Complete! Runtime: {elapsed_time/60:.1f} minutes")
    print(f"💾 Files saved: {posts_filename}, {comments_filename if all_comments else 'no comments file'}")
    print("\n✅ All posts are now relevant to Adobe and duplicates removed!")
    print("📝 Note: Used broader search terms and relaxed filtering to capture comparison posts")
    print("⚠️  NOTE: Include robustness check excluding earnings period in your analysis")

if __name__ == "__main__":
    main()