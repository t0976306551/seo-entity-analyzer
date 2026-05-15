-- supabase/migrations/001_initial_schema.sql

-- user_sheets: 每個用戶對應一個 Google Sheet
CREATE TABLE user_sheets (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  sheet_id   TEXT NOT NULL DEFAULT '',
  sheet_url  TEXT NOT NULL DEFAULT '',
  status     TEXT DEFAULT 'pending' CHECK (status IN ('pending','active','failed')),
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id)
);

-- query_history: 每次查詢的記錄
CREATE TABLE query_history (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  keyword    TEXT NOT NULL,
  sheet_url  TEXT,
  status     TEXT DEFAULT 'pending' CHECK (status IN ('pending','processing','searching','crawling','analyzing','writing','done','failed')),
  job_id     TEXT,
  error_msg  TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_history_user ON query_history(user_id, created_at DESC);

-- RLS: 每人只能看自己的資料
ALTER TABLE user_sheets ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "own_sheets" ON user_sheets FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "own_history" ON query_history FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
