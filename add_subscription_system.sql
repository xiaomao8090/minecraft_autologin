USE minecraft_autologin;

ALTER TABLE accounts ADD COLUMN IF NOT EXISTS subscription_days INT DEFAULT 0;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS auto_renew BOOLEAN DEFAULT FALSE;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS subscription_updated_at DATE;

ALTER TABLE cards ADD COLUMN IF NOT EXISTS last_used_email VARCHAR(255);

CREATE INDEX IF NOT EXISTS idx_subscription_days ON accounts(subscription_days);
CREATE INDEX IF NOT EXISTS idx_auto_renew ON accounts(auto_renew);
