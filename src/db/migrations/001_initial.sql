-- Saturnus_Magister Initial Schema
-- Syncs with Nyx_Venatrix database for job application tracking

-- Email storage and processing
CREATE TABLE IF NOT EXISTS emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gmail_id VARCHAR(255) UNIQUE NOT NULL,
    thread_id VARCHAR(255) NOT NULL,
    subject TEXT,
    sender_email VARCHAR(500),
    sender_name VARCHAR(500),
    recipient_email VARCHAR(500),
    received_at TIMESTAMPTZ NOT NULL,
    body_text TEXT,
    body_html TEXT,

    -- Classification results
    category VARCHAR(50),  -- interview_invite, assignment, rejection, offer, etc.
    sentiment VARCHAR(20), -- positive, negative, neutral
    confidence FLOAT,

    -- Processing metadata
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    error TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_gmail_id (gmail_id),
    INDEX idx_thread_id (thread_id),
    INDEX idx_sender_email (sender_email),
    INDEX idx_received_at (received_at DESC),
    INDEX idx_category (category),
    INDEX idx_processed (processed)
);

-- Email-to-job matching
CREATE TABLE IF NOT EXISTS email_job_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID NOT NULL REFERENCES emails(id) ON DELETE CASCADE,

    -- Nyx_Venatrix job reference (assumes applied_jobs table exists in shared DB)
    job_id UUID,  -- References Nyx_Venatrix applied_jobs.id

    -- Matching metadata
    match_score FLOAT NOT NULL,
    match_method VARCHAR(50), -- auto, manual, ai_disambiguation
    match_signals JSONB,  -- Stores company_name_fuzzy, domain_match, etc.

    -- Manual review
    needs_review BOOLEAN DEFAULT FALSE,
    reviewed BOOLEAN DEFAULT FALSE,
    reviewed_at TIMESTAMPTZ,
    reviewer_notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(email_id, job_id),

    -- Indexes
    INDEX idx_email_id (email_id),
    INDEX idx_job_id (job_id),
    INDEX idx_needs_review (needs_review),
    INDEX idx_match_score (match_score DESC)
);

-- TickTick task tracking
CREATE TABLE IF NOT EXISTS ticktick_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID NOT NULL REFERENCES emails(id) ON DELETE CASCADE,

    -- TickTick metadata
    ticktick_task_id VARCHAR(255),
    ticktick_project_id VARCHAR(255) NOT NULL,  -- Eisenhower quadrant or Work

    -- Task details
    title TEXT NOT NULL,
    content TEXT,
    due_date TIMESTAMPTZ,
    priority INTEGER,  -- 0-5 in TickTick
    tags TEXT[],

    -- Task type
    task_type VARCHAR(50),  -- task, calendar_event, countdown

    -- Sync status
    synced BOOLEAN DEFAULT FALSE,
    synced_at TIMESTAMPTZ,
    sync_error TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_email_id (email_id),
    INDEX idx_ticktick_task_id (ticktick_task_id),
    INDEX idx_synced (synced)
);

-- Manual review queue
CREATE TABLE IF NOT EXISTS manual_review_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID NOT NULL REFERENCES emails(id) ON DELETE CASCADE,

    -- Review reason
    reason VARCHAR(100) NOT NULL,  -- low_confidence_match, ambiguous_category, etc.
    reason_details JSONB,

    -- Review status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, in_progress, completed, skipped
    assigned_to VARCHAR(255),

    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolution_action VARCHAR(100),
    resolution_notes TEXT,

    -- Priority (higher = more urgent)
    priority INTEGER DEFAULT 5,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_email_id (email_id),
    INDEX idx_status (status),
    INDEX idx_resolved (resolved),
    INDEX idx_priority (priority DESC)
);

-- Company blocklist (for analytics and auto-suggest blocking)
CREATE TABLE IF NOT EXISTS company_blocklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(500) NOT NULL,
    domain VARCHAR(500),

    -- Blocklist metadata
    reason VARCHAR(100),  -- high_rejection_rate, low_quality_opportunities, etc.
    rejection_count INTEGER DEFAULT 0,

    -- Status
    blocked BOOLEAN DEFAULT TRUE,
    blocked_at TIMESTAMPTZ DEFAULT NOW(),
    unblocked_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(company_name, domain),

    -- Indexes
    INDEX idx_company_name (company_name),
    INDEX idx_domain (domain),
    INDEX idx_blocked (blocked)
);

-- Analytics events (for tracking all responses)
CREATE TABLE IF NOT EXISTS response_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
    job_id UUID,  -- References Nyx_Venatrix applied_jobs.id

    -- Response metadata
    response_type VARCHAR(50) NOT NULL,  -- rejection, interview, offer, etc.
    response_stage VARCHAR(50),  -- application, phone_screen, onsite, etc.

    -- Company info
    company_name VARCHAR(500),
    position_title VARCHAR(500),

    -- Effort/outcome tracking
    effort_level VARCHAR(20),  -- low, medium, high (from job application)
    had_feedback BOOLEAN DEFAULT FALSE,

    -- Timeline
    application_date DATE,
    response_date DATE,
    days_to_response INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_email_id (email_id),
    INDEX idx_job_id (job_id),
    INDEX idx_response_type (response_type),
    INDEX idx_company_name (company_name),
    INDEX idx_response_date (response_date DESC)
);

-- Processing state (for idempotency and resumability)
CREATE TABLE IF NOT EXISTS processing_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state_key VARCHAR(255) UNIQUE NOT NULL,  -- e.g., 'last_gmail_history_id'
    state_value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Update timestamps trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to all tables
CREATE TRIGGER update_emails_updated_at BEFORE UPDATE ON emails
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_job_matches_updated_at BEFORE UPDATE ON email_job_matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ticktick_tasks_updated_at BEFORE UPDATE ON ticktick_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_manual_review_queue_updated_at BEFORE UPDATE ON manual_review_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_company_blocklist_updated_at BEFORE UPDATE ON company_blocklist
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE emails IS 'Stores all processed emails from Gmail inbox and sent folder';
COMMENT ON TABLE email_job_matches IS 'Links emails to Nyx_Venatrix job applications with confidence scoring';
COMMENT ON TABLE ticktick_tasks IS 'Tracks TickTick task creation and sync status';
COMMENT ON TABLE manual_review_queue IS 'Queue for emails requiring human review';
COMMENT ON TABLE company_blocklist IS 'Companies to auto-reject or deprioritize';
COMMENT ON TABLE response_analytics IS 'Analytics for tracking application outcomes and company patterns';
