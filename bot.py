import praw
from collections import Counter
import datetime

# Reddit API Authentication Configuration
reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="EcoShield Bot v1.0 by /u/YOUR_USERNAME",
    username="YOUR_BOT_USERNAME",
    password="YOUR_BOT_PASSWORD"
)

def calculate_trust_score(username):
    try:
        user = reddit.redditor(username)
        if not hasattr(user, 'id'):
            return 0, ["Account is suspended or shadowbanned"]
            
        score = 100
        flags = []
        
        # --- VECTOR 1: Account Longevity ---
        created_utc = user.created_utc
        account_age_days = (datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(created_utc)).days
        
        if account_age_days < 7:
            score -= 30
            flags.append(f"Critical: Ultra-fresh account ({account_age_days} days old)")
        elif account_age_days < 30:
            score -= 15
            flags.append(f"Warning: New account ({account_age_days} days old)")
            
        # --- VECTOR 2: Karma Distribution Analytics ---
        total_karma = user.link_karma + user.comment_karma
        if total_karma < 50:
            score -= 20
            flags.append(f"Low reputation: Total Karma is critically low ({total_karma})")
            
        # --- VECTOR 3: Behavioral Frequency & Spam Detection ---
        comments = list(user.comments.new(limit=20))
        if comments:
            comment_texts = [c.body.strip().lower() for c in comments]
            text_counts = Counter(comment_texts)
            most_common = text_counts.most_common(1)[0]
            
            if most_common[1] >= 3:
                score -= 25
                flags.append(f"Spam signature detected: Repeated same phrase {most_common[1]} times in recent history")
        else:
            if account_age_days > 30:
                score -= 10
                flags.append("Sleeper Profile: Aged account with zero historical engagement")

        score = max(0, score)
        return score, flags
    except Exception as e:
        return None, [f"API Execution Error: {str(e)}"]

# Live Stream Subreddit Monitoring
TARGET_SUBREDDIT = "YOUR_SUBREDDIT_NAME" 
print(f"🛡️ [EcoShield Initialized] Guarding r/{TARGET_SUBREDDIT}...")

try:
    subreddit = reddit.subreddit(TARGET_SUBREDDIT)
    for comment in subreddit.stream.comments(skip_existing=True):
        author = comment.author
        if author is None: continue
        
        trust_score, flags = calculate_trust_score(author.name)
        if trust_score and trust_score < 60:
            print(f"⚠️ High Threat Level Registered: u/{author.name} (Score: {trust_score}/100)")
            comment.report(reason=f"EcoShield: Low Trust Score ({trust_score}/100)")
except KeyboardInterrupt:
    print("\n🛑 EcoShield deactivated.")
