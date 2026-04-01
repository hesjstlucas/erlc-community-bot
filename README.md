# ERLC Community Bot

A completely new standalone Discord bot built for ERLC community servers with:

- persistent economy commands
- fun and gambling commands
- community profiles and reputation
- ERLC patrol, callsign, shift, and server utilities
- no moderation commands

## Commands

### Economy

- `/balance`
- `/daily`
- `/work`
- `/beg`
- `/crime`
- `/deposit`
- `/withdraw`
- `/pay`
- `/leaderboard`
- `/shop`
- `/buy`
- `/use`
- `/inventory`

### Community + ERLC

- `/profile`
- `/bio`
- `/rep`
- `/callsign_set`
- `/callsign_view`
- `/patrol_on`
- `/patrol_off`
- `/shift_start`
- `/shift_end`
- `/shift_stats`
- `/server`
- `/patrol_tip`

### Fun

- `/help`
- `/eightball`
- `/coinflip`
- `/dice`
- `/slots`
- `/scenario`
- `/rate`

## What It Tracks

- wallet and bank balances
- daily streaks
- profile bios and rep
- inventory and shop items
- callsigns
- patrol ads
- total shift time and payouts

All server data is stored in a local JSON file at `data/community-store.json` by default.

## Setup

1. Copy `.env.example` to `.env`.
2. Fill in your Discord bot token.
3. Optionally add your ERLC server join code, invite link, patrol channel ID, and ERLC API key settings.
4. Install dependencies:

```bash
py -m pip install -r requirements.txt
```

5. Start the bot:

```bash
py bot.py
```

## Environment Variables

- `DISCORD_TOKEN` is required.
- `REGISTER_GUILD_ID` is optional and lets slash commands sync instantly to one test server.
- `DATA_FILE_PATH` changes where the JSON data is stored.
- `STARTING_BALANCE` changes the default wallet value for new members.
- `PATROL_CHANNEL_ID` makes `/patrol_on` post in one specific channel.
- `ERLC_SERVER_NAME` sets the fallback server name shown in `/server`.
- `ERLC_JOIN_CODE` sets the fallback join code shown in `/server`.
- `COMMUNITY_INVITE_URL` adds a clickable invite link to `/server`.
- `ERLC_SERVER_KEY` enables live ERLC server player stats.
- `ERLC_GLOBAL_API_KEY` is optional if your ERLC API setup needs it.
- `ERLC_API_BASE_URL` lets you override the PRC server endpoint.
- `ERLC_HTTP_USER_AGENT` lets you override the request user-agent.

## Notes

- This bot is intentionally community-focused and ships with zero moderation commands.
- Economy data is stored per Discord server, so each ERLC community keeps its own progression.
- If `ERLC_SERVER_KEY` is not set, `/server` still works with your configured fallback info.
