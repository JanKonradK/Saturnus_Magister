# `scripts/` - Utility Scripts

Helper scripts for setup, maintenance, and migration.

## Scripts

### `ticktick_oauth.py` - TickTick OAuth Flow

**Purpose**: Performs the OAuth 2.0 "dance" to obtain an Access Token for the TickTick API.

**Usage**:
1. Run `python scripts/ticktick_oauth.py`.
2. Enter your Client ID and Client Secret (from TickTick Developer Portal).
3. The script opens your browser to authorize the app.
4. It starts a local web server to capture the callback code.
5. Exchanges the code for an Access Token.
6. Saves the token to `.ticktick_tokens.json` and prints values for your `.env`.

### `migrate_to_cloud.py` - Cloud Migration (Phase 2)

*Placeholder.*

**Purpose**: Will contain logic to package the application for AWS Lambda or Google Cloud Run deployment.

## Usage

```bash
# Run from project root
python scripts/ticktick_oauth.py
```
