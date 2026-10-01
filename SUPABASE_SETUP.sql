# Run this SQL in your Supabase Dashboard → SQL Editor
# URL: https://supabase.com/dashboard/project/aczptmsfeueejysaajod/sql/new

-- 1. Create tenders table
CREATE TABLE IF NOT EXISTS tenders (
    id          BIGSERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create bids table (with FK to tenders)
CREATE TABLE IF NOT EXISTS bids (
    id                 BIGSERIAL PRIMARY KEY,
    tender_id          BIGINT REFERENCES tenders(id) ON DELETE CASCADE,
    vendor_email       TEXT NOT NULL,
    vendor_name        TEXT NOT NULL,
    spec_text          TEXT NOT NULL,
    compliance_score   INTEGER DEFAULT 0,
    compliance_report  TEXT,
    created_at         TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Disable Row Level Security so the anon key can read/write
--    (This is fine for a demo app. For production, use proper RLS policies.)
ALTER TABLE tenders DISABLE ROW LEVEL SECURITY;
ALTER TABLE bids    DISABLE ROW LEVEL SECURITY;
