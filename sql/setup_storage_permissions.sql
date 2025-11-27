-- ============================================================================
-- Setup Supabase Storage Permissions for FAQ Index
-- ============================================================================
-- Run this script in Supabase SQL Editor to allow file uploads to Storage bucket
-- ============================================================================

-- 1. Create Storage bucket "Storage" if it doesn't exist (do this in Dashboard first)
-- Go to: Storage → Create bucket → Name: "Storage" → Public or Private

-- 2. Allow authenticated users to upload files
-- Replace 'Storage' with your bucket name if different

-- For Public bucket (anyone can read, authenticated users can write):
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'Storage',
  'Storage',
  true,  -- Set to false for private bucket
  52428800,  -- 50MB limit
  ARRAY['application/octet-stream', 'application/x-pickle', 'application/binary']
)
ON CONFLICT (id) DO NOTHING;

-- 3. Set up Storage Policies for the bucket
-- Note: Drop existing policies first if they exist

DROP POLICY IF EXISTS "Allow authenticated uploads" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated reads" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated updates" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated deletes" ON storage.objects;

-- Policy: Allow authenticated users to upload files (simplified - allows all files in bucket)
CREATE POLICY "Allow authenticated uploads"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'Storage');

-- Alternative: Allow service role (backend) to upload (bypasses RLS)
-- This is automatically allowed if you use service_role key
-- RECOMMENDED: Use service_role key in .env instead of configuring policies

-- Policy: Allow authenticated users to read files
CREATE POLICY "Allow authenticated reads"
ON storage.objects
FOR SELECT
TO authenticated
USING (bucket_id = 'Storage');

-- Policy: Allow authenticated users to update files
CREATE POLICY "Allow authenticated updates"
ON storage.objects
FOR UPDATE
TO authenticated
USING (bucket_id = 'Storage')
WITH CHECK (bucket_id = 'Storage');

-- Policy: Allow authenticated users to delete files
CREATE POLICY "Allow authenticated deletes"
ON storage.objects
FOR DELETE
TO authenticated
USING (bucket_id = 'Storage');

-- Alternative: If you want to allow service role (from backend) to access:
-- You can use the service_role key in your .env file instead of anon key
-- The service_role key bypasses RLS policies

-- ============================================================================
-- Quick Fix: Make bucket public (if you don't need security)
-- ============================================================================
-- If you just want it to work quickly, you can make the bucket public:
-- UPDATE storage.buckets SET public = true WHERE id = 'Storage';

-- ============================================================================
-- Note: For production, use service_role key in backend, not anon key
-- ============================================================================
-- In your .env file, use SUPABASE_KEY=service_role_key (not anon key)
-- Service role key bypasses RLS and is safe for backend use

