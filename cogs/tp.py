import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from datetime import datetime
from typing import List, Dict, Any

from utils.database import dbManager


# Navigation buttons class
class NavigationView(discord.ui.View):
    def __init__(self, items: List[Dict[str, Any]], user_id: str, page_size: int = 5, is_sell: bool = True):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.items = items
        self.user_id = user_id
        self.current_page = 0
        self.page_size = page_size
        self.total_pages = (len(items) - 1) // page_size + 1
        self.is_sell = is_sell  # True for sells, False for buys

        # Disable left button if we're on the first page
        self.update_buttons()

    def update_buttons(self):
        # Update button states based on current page
        self.previous_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page >= self.total_pages - 1)

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.gray)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verify it's the same user
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ You cannot use buttons on messages that aren't yours.",
                                                    ephemeral=True)
            return

        # Go to previous page
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()

            # Create embed with current page items
            embed = self.create_page_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verify it's the same user
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ You cannot use buttons on messages that aren't yours.",
                                                    ephemeral=True)
            return

        # Go to next page
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()

            # Create embed with current page items
            embed = self.create_page_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    def create_page_embed(self):
        # Function to create current page embed
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.items))

        page_items = self.items[start_idx:end_idx]

        # Title and color based on sell/buy
        if self.is_sell:
            embed = discord.Embed(
                title="📊 Your Trading Post Sell Orders",
                description=f"Showing {start_idx + 1}-{end_idx} of {len(self.items)} items (Page {self.current_page + 1}/{self.total_pages})",
                color=0xFFD700  # Gold color for sells
            )
        else:
            embed = discord.Embed(
                title="🛒 Your Trading Post Buy Orders",
                description=f"Showing {start_idx + 1}-{end_idx} of {len(self.items)} items (Page {self.current_page + 1}/{self.total_pages})",
                color=0x3498DB  # Blue color for buys
            )

        # Total accumulated on this page
        page_total = sum(item['total_value'] for item in page_items)

        # Global total
        total_all = sum(item['total_value'] for item in self.items)

        # Add each item to embed
        for item in page_items:
            embed.add_field(
                name=item['name'],
                value=item['value_text'],
                inline=False
            )

        # Footer with totals
        if self.is_sell:
            footer_text = f"Total value: {total_all // 10000}g {(total_all % 10000) // 100}s {total_all % 100}c"
        else:
            footer_text = f"Total invested: {total_all // 10000}g {(total_all % 10000) // 100}s {total_all % 100}c"

        embed.set_footer(text=footer_text)
        return embed


class TradingPostCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="tpsell",
        description="Shows your current Trading Post sell orders in Guild Wars 2"
    )
    async def tp_sells(self, interaction: discord.Interaction):
        """Shows the list of active sell orders in the GW2 Trading Post"""
        await interaction.response.defer(ephemeral=False)

        user_id = str(interaction.user.id)
        api_key = await dbManager.getApiKey(user_id)

        if not api_key:
            await interaction.followup.send(
                "❌ You don't have a GW2 API key registered. Use `/apikey add` to set one up.",
                ephemeral=False
            )
            return

        try:
            # Get Trading Post sales
            async with aiohttp.ClientSession() as session:
                # First get sell listings
                async with session.get(
                        f"https://api.guildwars2.com/v2/commerce/transactions/current/sells?access_token={api_key}") as response:
                    if response.status != 200:
                        await interaction.followup.send(f"❌ Error querying GW2 API: {response.status}",
                                                        ephemeral=False)
                        return

                    sell_listings = await response.json()

                    if not sell_listings:
                        await interaction.followup.send("📊 You don't have any items listed for sale in the Trading Post.",
                                                        ephemeral=False)
                        return

                # Get current Trading Post prices for comparison
                item_ids = [str(item["item_id"]) for item in sell_listings]
                items_param = ",".join(item_ids)

                # Get prices and item details
                async with session.get(
                        f"https://api.guildwars2.com/v2/commerce/prices?ids={items_param}") as prices_response:
                    prices_data = await prices_response.json() if prices_response.status == 200 else []

                async with session.get(f"https://api.guildwars2.com/v2/items?ids={items_param}") as items_response:
                    items_data = await items_response.json() if items_response.status == 200 else []

            # Create dictionaries for easy lookup
            prices_dict = {item["id"]: item for item in prices_data}
            items_dict = {item["id"]: item for item in items_data}

            # Prepare data for all sales
            formatted_items = []

            for selling in sell_listings:
                item_id = selling["item_id"]
                item_name = items_dict[item_id]["name"] if item_id in items_dict else f"Item {item_id}"
                quantity = selling["quantity"]
                price_each = selling["price"]
                price_total = price_each * quantity

                # Format price in gold/silver/copper
                price_gold = price_each // 10000
                price_silver = (price_each % 10000) // 100
                price_copper = price_each % 100

                price_formatted = f"{price_gold}g {price_silver}s {price_copper}c"

                # Check current lowest sell price in market
                current_lowest_sell = None
                undercut_message = ""
                if item_id in prices_dict and "sells" in prices_dict[item_id]:
                    current_lowest_sell = prices_dict[item_id]["sells"]["unit_price"]

                    # Detect if sell price has been undercut
                    if current_lowest_sell and current_lowest_sell < price_each:
                        diff = price_each - current_lowest_sell
                        diff_gold = diff // 10000
                        diff_silver = (diff % 10000) // 100
                        diff_copper = diff % 100
                        undercut_message = (
                            f" ⚠️ **Undercut!** Current lowest price is "
                            f"{current_lowest_sell // 10000}g {(current_lowest_sell % 10000) // 100}s "
                            f"{current_lowest_sell % 100}c "
                            f"(difference: {diff_gold}g {diff_silver}s {diff_copper}c)"
                        )

                # Text to show in embed field
                value_text = (
                    f"**Quantity:** {quantity}\n"
                    f"**Price:** {price_formatted} each{undercut_message}\n"
                    f"**Total:** {price_total // 10000}g {(price_total % 10000) // 100}s {price_total % 100}c"
                )

                # Add formatted data to list
                formatted_items.append({
                    'name': item_name,
                    'value_text': value_text,
                    'total_value': price_total
                })

            # Create navigation view with items
            view = NavigationView(formatted_items, user_id, is_sell=True)

            # Create initial embed
            embed = view.create_page_embed()

            # Send message with navigation view
            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred while processing your request: {str(e)}", ephemeral=False)

    @app_commands.command(
        name="tpbuy",
        description="Shows your current Trading Post buy orders in Guild Wars 2"
    )
    async def tp_buys(self, interaction: discord.Interaction):
        """Shows the list of active buy orders in the GW2 Trading Post"""
        await interaction.response.defer(ephemeral=False)

        user_id = str(interaction.user.id)
        api_key = await dbManager.getApiKey(user_id)

        if not api_key:
            await interaction.followup.send(
                "❌ You don't have a GW2 API key registered. Use `/apikey add` to set one up.",
                ephemeral=False
            )
            return

        try:
            # Get Trading Post buy orders
            async with aiohttp.ClientSession() as session:
                # First get buy listings
                async with session.get(
                        f"https://api.guildwars2.com/v2/commerce/transactions/current/buys?access_token={api_key}") as response:
                    if response.status != 200:
                        await interaction.followup.send(f"❌ Error querying GW2 API: {response.status}",
                                                        ephemeral=False)
                        return

                    buy_listings = await response.json()

                    if not buy_listings:
                        await interaction.followup.send(
                            "📊 You don't have any active buy orders in the Trading Post.", ephemeral=False)
                        return

                # Get current Trading Post prices for comparison
                item_ids = [str(item["item_id"]) for item in buy_listings]
                items_param = ",".join(item_ids)

                # Get prices and item details
                async with session.get(
                        f"https://api.guildwars2.com/v2/commerce/prices?ids={items_param}") as prices_response:
                    prices_data = await prices_response.json() if prices_response.status == 200 else []

                async with session.get(f"https://api.guildwars2.com/v2/items?ids={items_param}") as items_response:
                    items_data = await items_response.json() if items_response.status == 200 else []

            # Create dictionaries for easy lookup
            prices_dict = {item["id"]: item for item in prices_data}
            items_dict = {item["id"]: item for item in items_data}

            # Prepare data for all buys
            formatted_items = []

            for buying in buy_listings:
                item_id = buying["item_id"]
                item_name = items_dict[item_id]["name"] if item_id in items_dict else f"Item {item_id}"
                quantity = buying["quantity"]
                price_each = buying["price"]
                price_total = price_each * quantity

                # Format price in gold/silver/copper
                price_gold = price_each // 10000
                price_silver = (price_each % 10000) // 100
                price_copper = price_each % 100

                price_formatted = f"{price_gold}g {price_silver}s {price_copper}c"

                # Check current highest buy price in market
                current_highest = None
                if item_id in prices_dict and "buys" in prices_dict[item_id]:
                    current_highest = prices_dict[item_id]["buys"]["unit_price"]

                # Check current lowest sell price
                current_lowest_sell = None
                if item_id in prices_dict and "sells" in prices_dict[item_id]:
                    current_lowest_sell = prices_dict[item_id]["sells"]["unit_price"]

                # Prepare price status messages
                price_status = ""
                buy_sell_diff = ""

                if current_highest:
                    if current_highest > price_each:
                        price_status = " ⚠️ (Not the highest offer)"

                    # Calculate difference with lowest sell price
                    if current_lowest_sell:
                        diff = current_lowest_sell - price_each
                        diff_gold = diff // 10000
                        diff_silver = (diff % 10000) // 100
                        diff_copper = diff % 100

                        buy_sell_diff = f"\n**Difference to sell price:** {diff_gold}g {diff_silver}s {diff_copper}c"

                # Item information with formatting
                value_text = (
                    f"**Quantity:** {quantity}\n"
                    f"**Your offer:** {price_formatted} each{price_status}\n"
                    f"**Total invested:** {price_total // 10000}g {(price_total % 10000) // 100}s {price_total % 100}c"
                )

                # Add market price information if available
                if current_highest:
                    highest_gold = current_highest // 10000
                    highest_silver = (current_highest % 10000) // 100
                    highest_copper = current_highest % 100
                    highest_formatted = f"{highest_gold}g {highest_silver}s {highest_copper}c"

                    value_text += f"\n**Current highest offer:** {highest_formatted}"

                if current_lowest_sell:
                    lowest_gold = current_lowest_sell // 10000
                    lowest_silver = (current_lowest_sell % 10000) // 100
                    lowest_copper = current_lowest_sell % 100
                    lowest_formatted = f"{lowest_gold}g {lowest_silver}s {lowest_copper}c"

                    value_text += f"\n**Lowest sell price:** {lowest_formatted}{buy_sell_diff}"

                # Add formatted data to list
                formatted_items.append({
                    'name': item_name,
                    'value_text': value_text,
                    'total_value': price_total
                })

            # Create navigation view with items
            view = NavigationView(formatted_items, user_id, is_sell=False)

            # Create initial embed
            embed = view.create_page_embed()

            # Send message with navigation view
            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred while processing your request: {str(e)}", ephemeral=False)


async def setup(bot):
    await bot.add_cog(TradingPostCommands(bot))