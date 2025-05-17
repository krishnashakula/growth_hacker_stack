CREATE TABLE IF NOT EXISTS posts (
  post_id TEXT PRIMARY KEY,
  content TEXT,
  keywords TEXT[],
  hook_style TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS post_stats (
  post_id TEXT,
  like_count INTEGER,
  comment_count INTEGER,
  fetched_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (post_id, fetched_at)
);

CREATE TABLE IF NOT EXISTS hook_performance (
  hook_style TEXT PRIMARY KEY,
  successes INTEGER DEFAULT 0,
  trials INTEGER DEFAULT 0
);
