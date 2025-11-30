-- Add countdown and calendar event features to TickTick tasks

-- Add calendar event fields
ALTER TABLE ticktick_tasks
ADD COLUMN IF NOT EXISTS is_calendar_event BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS start_time TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS end_time TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS is_all_day BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS reminders TEXT[], -- Array of reminder strings like '-1d', '-1h'
ADD COLUMN IF NOT EXISTS countdown_enabled BOOLEAN DEFAULT FALSE;

-- Add index for calendar events
CREATE INDEX IF NOT EXISTS idx_is_calendar_event ON ticktick_tasks(is_calendar_event);
CREATE INDEX IF NOT EXISTS idx_start_time ON ticktick_tasks(start_time);

-- Comments
COMMENT ON COLUMN ticktick_tasks.is_calendar_event IS 'True if this is a calendar event (interview, deadline)';
COMMENT ON COLUMN ticktick_tasks.countdown_enabled IS 'True if countdown widget should be enabled in TickTick';
COMMENT ON COLUMN ticktick_tasks.reminders IS 'Array of reminder strings in TickTick format';
