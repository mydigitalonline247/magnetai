-- Supabase Schema for MagnetAI
-- Run this in your Supabase SQL Editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    google_id TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    picture TEXT,
    last_login TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_google_id ON public.users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON public.users(created_at);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Create RLS policies

-- Policy 1: Users can read their own data
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid()::text = google_id);

-- Policy 2: Users can update their own data
CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid()::text = google_id);

-- Policy 3: Service role has full access (for backend operations)
CREATE POLICY "Service role full access" ON public.users
    FOR ALL USING (auth.role() = 'service_role');

-- Policy 4: Allow insert for new users (service role)
CREATE POLICY "Allow insert for new users" ON public.users
    FOR INSERT WITH CHECK (auth.role() = 'service_role');

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON public.users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Grant necessary permissions
GRANT ALL ON public.users TO authenticated;
GRANT ALL ON public.users TO service_role;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;

-- Insert a test user (optional - remove in production)
-- INSERT INTO public.users (google_id, email, name, picture) 
-- VALUES ('test_google_id', 'test@example.com', 'Test User', 'https://example.com/picture.jpg')
-- ON CONFLICT (google_id) DO NOTHING; 