# Discord Bot - Qaliz

This is a Discord bot developed with `discord.py`, designed for *Guild Wars 2* players and server administrators. It integrates the *Guild Wars 2* (v2) API to provide real-time pricing, moderation tools and a custom command system.  

## Features

### Original Features (Guild Wars 2)
- **`/item <search>`**: Displays current item prices (e.g. Ectos, precursorys) using the GW2 API.
- **`/clovers`**: Calculates the current price of Mystic Clovers based on materials and market.
- **`/delivery`**: Check the content of your Trading Post delivery box (requires API key).
- **`/t3`, `/t4`, `/t5`, `/t6`**: Displays T3 to T6 material prices.
- **`/materials`**: Shows Gift of Condensed Magic and Gift of Condensed Might prices.
- **`/gift`**: Fixed price of GOMS (Gift of Magic), GOJMS (Gift of Jewelry Magic), and GOJW (Gift of Jade Weapon).
- **`/apikey add/remove/check`**: Manage your GW2 API key with “account”, “inventories”, and “tradingpost” permissions.
- **`/hora`**: Displays the current time on the server.
- **`/fractales`** Displays daily fractals.
- **`/tpcompra`**: Display your current purchase orders in the Guild Wars 2 Trading Post.
- **`/tpventa`**: Display your current sales in the Guild Wars 2 Trading Post.
- **`/search`**: Searching for items in the material bank, inventory and storage.
- **`/gemas`** Displays the value of gems currently in the game.
- - **`.to [duration]`**: Allows users to apply an auto-timeout (default 60 seconds, maximum 10 minutes) with validations.
- **Custom Command System (`CommandManager`)**:
  - crear (cmd), editar, eliminar commands with categories, alias and future support for actions (e.g. ban).
- Role Management**: Configure admin and mod roles with `.configure_roles`, persisting in Firestore.

## Requirements

- Python**: Version 3.8 or higher.
- **Libraries**:
  - `discord.py==2.3.2` (for slash commands and events).
  - aiohttp==3.8.6` (for asynchronous requests to APIs)
  - google-cloud-firestore==2.13.1` (for Firestore integration)
  - `python-dotenv==1.0.0` (for environment variables)
- Credentials:
  - Discord bot token (get it from [Discord Developer Portal](https://discord.com/developers/applications)).
  - Firestore credentials JSON file (download from Google Cloud).
  - Guild Wars 2 API key (optional, get it from [account.arena.net](https://account.arena.net/applications)).

## Installation

1. **Clone the Repository**:
   ````bash
   git clone https://github.com/Kunzeu/Qaliz.git
   cd Qaliz
2. Install the required dependencies using ``pip install -r requirements.txt`.
3. Get a Guild Wars 2 API key from (https://wiki.guildwars2.com/wiki/API:2) or directly in the code (be sure to keep it safe).
4. Run the bot using `python index.py`.


## Contact

You can contact me on Discord: [Kunzeu](https://discord.com/users/552563672162107431)