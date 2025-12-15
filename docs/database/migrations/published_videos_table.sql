-- Migration: Create published_videos table for YouTubeUploaderAgent
-- Description: Stores metadata for videos uploaded to YouTube
-- Created: 2025-12-13

CREATE TABLE IF NOT EXISTS published_videos (
    id SERIAL PRIMARY KEY,
    video_id TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    tags TEXT[],
    privacy_status TEXT CHECK (privacy_status IN ('public', 'unlisted', 'private')),
    uploaded_at TIMESTAMPTZ NOT NULL,
    uploaded_by TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_published_videos_video_id ON published_videos(video_id);
CREATE INDEX IF NOT EXISTS idx_published_videos_uploaded_at ON published_videos(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_published_videos_uploaded_by ON published_videos(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_published_videos_privacy ON published_videos(privacy_status);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_published_videos_updated_at
    BEFORE UPDATE ON published_videos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments
COMMENT ON TABLE published_videos IS 'Videos uploaded to YouTube by YouTubeUploaderAgent';
COMMENT ON COLUMN published_videos.video_id IS 'YouTube video ID (e.g., dQw4w9WgXcQ)';
COMMENT ON COLUMN published_videos.url IS 'Full YouTube URL';
COMMENT ON COLUMN published_videos.privacy_status IS 'Video privacy: public, unlisted, or private';
COMMENT ON COLUMN published_videos.uploaded_by IS 'Agent name that uploaded the video';
COMMENT ON COLUMN published_videos.metadata IS 'Full metadata as JSONB (tags, category, etc.)';
