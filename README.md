# ERLC Community Bot

A standalone Discord bot for ERLC communities that focuses on economy, profiles, fun, generators, and casual utility commands.

- no moderation commands
- no staff patrol or shift systems
- 70+ community-focused slash commands

## Command Categories

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

### Profiles

- `/profile`
- `/bio`
- `/rep`
- `/rep_leaderboard`
- `/networth`
- `/callsign_set`
- `/callsign_view`
- `/pronouns_set`
- `/pronouns_view`
- `/location_set`
- `/location_view`
- `/birthday_set`
- `/birthday_view`
- `/hobbies_set`
- `/hobbies_view`
- `/likes_set`
- `/likes_view`
- `/dislikes_set`
- `/dislikes_view`
- `/status_set`
- `/status_view`
- `/motto_set`
- `/motto_view`
- `/favorite_song_set`
- `/favorite_song_view`
- `/favorite_vehicle_set`
- `/favorite_vehicle_view`

### Social

- `/avatar`
- `/friendship`
- `/ship`
- `/compliment`
- `/roast`
- `/motivate`
- `/truth`
- `/dare`
- `/wouldyourather`
- `/nhie`
- `/mood`
- `/poll`
- `/topic`

### Utility

- `/choose`
- `/random_number`
- `/reverse`
- `/clap`
- `/emojify`
- `/say`
- `/wordcount`
- `/charcount`
- `/binary`
- `/hex`
- `/membercount`
- `/joined`

### Fun

- `/help`
- `/eightball`
- `/coinflip`
- `/dice`
- `/slots`
- `/scenario`
- `/rate`
- `/question`
- `/fortune`
- `/joke`
- `/fact`
- `/pickup`
- `/nickname_idea`
- `/colorcombo`
- `/moviepick`
- `/foodpick`

### ERLC Generators

- `/server`
- `/rp_name`
- `/business_name`
- `/plate`
- `/eventidea`
- `/vehicleidea`
- `/scene_twist`
- `/civilian_call`
- `/serverad`
- `/outfitidea`
- `/crewname`
- `/street_name`
- `/playlist_name`
- `/petname`

## What It Tracks

- wallet and bank balances
- daily streaks
- profile bios and reputation
- favorite things and profile details
- inventory and shop items
- callsigns

All server data is stored in a local JSON file at `data/community-store.json` by default.

## Setup

1. Copy `.env.example` to `.env`.
2. Fill in your Discord bot token.
3. Optionally add your ERLC server join code, invite link, and ERLC API key settings.
4. Install dependencies:

```bash
py -m pip install -r requirements.txt
```

5. Start the bot:

```bash
py bot.py
```

Railway can use the included `Procfile` directly.

## Environment Variables

- `DISCORD_TOKEN` is required.
- `REGISTER_GUILD_ID` is optional and lets slash commands sync instantly to one test server.
- `DATA_FILE_PATH` changes where the JSON data is stored.
- `STARTING_BALANCE` changes the default wallet value for new members.
- `ERLC_SERVER_NAME` sets the fallback server name shown in `/server`.
- `ERLC_JOIN_CODE` sets the fallback join code shown in `/server`.
- `COMMUNITY_INVITE_URL` adds a clickable invite link to `/server`.
- `ERLC_SERVER_KEY` enables live ERLC server player stats.
- `ERLC_GLOBAL_API_KEY` is optional if your ERLC API setup needs it.
- `ERLC_API_BASE_URL` lets you override the PRC server endpoint.
- `ERLC_HTTP_USER_AGENT` lets you override the request user-agent.

## Notes

- This bot is intentionally community-focused and ships with zero moderation tools.
- Economy data is stored per Discord server, so each community keeps its own progression.
- If `ERLC_SERVER_KEY` is not set, `/server` still works with your configured fallback info.
