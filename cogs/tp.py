import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from datetime import datetime
from typing import List, Dict, Any

from utils.database import dbManager  # Importamos la clase dbManager que ya tienes


# Clase para los botones de navegación
class NavigationView(discord.ui.View):
    def __init__(self, items: List[Dict[str, Any]], user_id: str, page_size: int = 5, is_sell: bool = True):
        super().__init__(timeout=300)  # 5 minutos de timeout
        self.items = items
        self.user_id = user_id
        self.current_page = 0
        self.page_size = page_size
        self.total_pages = (len(items) - 1) // page_size + 1
        self.is_sell = is_sell  # True para ventas, False para compras

        # Deshabilitamos el botón izquierdo si estamos en la primera página
        self.update_buttons()

    def update_buttons(self):
        # Actualizar estado de botones según la página actual
        self.previous_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page >= self.total_pages - 1)

    @discord.ui.button(label="◀️ Anterior", style=discord.ButtonStyle.gray)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verificar que es el mismo usuario
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ No puedes usar estos botones en mensajes que no son tuyos.",
                                                    ephemeral=True)
            return

        # Ir a la página anterior
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()

            # Crear el embed con los ítems de la página actual
            embed = self.create_page_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶️ Siguiente", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verificar que es el mismo usuario
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ No puedes usar estos botones en mensajes que no son tuyos.",
                                                    ephemeral=True)
            return

        # Ir a la página siguiente
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()

            # Crear el embed con los ítems de la página actual
            embed = self.create_page_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    def create_page_embed(self):
        # Función para crear el embed de la página actual
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.items))

        page_items = self.items[start_idx:end_idx]

        # Título y color según si son ventas o compras
        if self.is_sell:
            embed = discord.Embed(
                title="📊 Tus artículos en venta en el bazar",
                description=f"Mostrando {start_idx + 1}-{end_idx} de {len(self.items)} artículos (Página {self.current_page + 1}/{self.total_pages})",
                color=0xFFD700  # Color dorado para ventas
            )
        else:
            embed = discord.Embed(
                title="🛒 Tus órdenes de compra en el bazar",
                description=f"Mostrando {start_idx + 1}-{end_idx} de {len(self.items)} artículos (Página {self.current_page + 1}/{self.total_pages})",
                color=0x3498DB  # Color azul para compras
            )

        # Total acumulado en esta página
        page_total = sum(item['total_value'] for item in page_items)

        # Total global
        total_all = sum(item['total_value'] for item in self.items)

        # Añadir cada ítem al embed
        for item in page_items:
            embed.add_field(
                name=item['name'],
                value=item['value_text'],
                inline=False
            )

        # Pie de página con totales
        if self.is_sell:
            footer_text = f"Valor total: {total_all // 10000}g {(total_all % 10000) // 100}s {total_all % 100}c"
        else:
            footer_text = f"Total invertido: {total_all // 10000}g {(total_all % 10000) // 100}s {total_all % 100}c"

        embed.set_footer(text=footer_text)
        return embed


class BazarCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="tpventa",
        description="Muestra tus ventas actuales en el bazar de Guild Wars 2"
    )
    async def bazar_ventas(self, interaction: discord.Interaction):
        """Muestra la lista de ventas activas del usuario en el bazar de GW2"""
        await interaction.response.defer(ephemeral=False)

        user_id = str(interaction.user.id)
        api_key = await dbManager.getApiKey(user_id)

        if not api_key:
            await interaction.followup.send(
                "❌ No tienes una clave API de GW2 registrada. Usa `/apikey añadir` para configurar una.",
                ephemeral=False
            )
            return

        try:
            # Obtenemos las ventas en el bazar
            async with aiohttp.ClientSession() as session:
                # Primero obtenemos los listados de venta
                async with session.get(
                        f"https://api.guildwars2.com/v2/commerce/transactions/current/sells?access_token={api_key}") as response:
                    if response.status != 200:
                        await interaction.followup.send(f"❌ Error al consultar la API de GW2: {response.status}",
                                                        ephemeral=False)
                        return

                    sell_listings = await response.json()

                    if not sell_listings:
                        await interaction.followup.send("📊 No tienes ningún artículo en venta en el bazar actualmente.",
                                                        ephemeral=False)
                        return

                # Obtenemos los precios actuales en el bazar para comparar
                item_ids = [str(item["item_id"]) for item in sell_listings]
                items_param = ",".join(item_ids)

                # Obtenemos precios y detalles de los items
                async with session.get(
                        f"https://api.guildwars2.com/v2/commerce/prices?ids={items_param}") as prices_response:
                    prices_data = await prices_response.json() if prices_response.status == 200 else []

                async with session.get(f"https://api.guildwars2.com/v2/items?ids={items_param}") as items_response:
                    items_data = await items_response.json() if items_response.status == 200 else []

            # Crear diccionarios para facilitar búsquedas
            prices_dict = {item["id"]: item for item in prices_data}
            items_dict = {item["id"]: item for item in items_data}

            # Preparamos los datos para todas las ventas
            formatted_items = []

            for selling in sell_listings:
                item_id = selling["item_id"]
                item_name = items_dict[item_id]["name"] if item_id in items_dict else f"Item {item_id}"
                quantity = selling["quantity"]
                price_each = selling["price"]
                price_total = price_each * quantity

                # Precio formateado en oro/plata/cobre
                price_gold = price_each // 10000
                price_silver = (price_each % 10000) // 100
                price_copper = price_each % 100

                price_formatted = f"{price_gold}g {price_silver}s {price_copper}c"

                # Verificar el precio de venta más bajo actual en el mercado
                current_lowest_sell = None
                undercut_message = ""
                if item_id in prices_dict and "sells" in prices_dict[item_id]:
                    current_lowest_sell = prices_dict[item_id]["sells"]["unit_price"]

                    # Detectar si el precio de venta ha sido superado (undercut)
                    if current_lowest_sell and current_lowest_sell < price_each:
                        diff = price_each - current_lowest_sell
                        diff_gold = diff // 10000
                        diff_silver = (diff % 10000) // 100
                        diff_copper = diff % 100
                        undercut_message = (
                            f" ⚠️ **Undercut!** El precio más bajo actual es "
                            f"{current_lowest_sell // 10000}g {(current_lowest_sell % 10000) // 100}s "
                            f"{current_lowest_sell % 100}c "
                            f"(diferencia: {diff_gold}g {diff_silver}s {diff_copper}c)"
                        )

                # Texto para mostrar en el campo del embed
                value_text = (
                    f"**Cantidad:** {quantity}\n"
                    f"**Precio:** {price_formatted} c/u{undercut_message}\n"
                    f"**Total:** {price_total // 10000}g {(price_total % 10000) // 100}s {price_total % 100}c"
                )

                # Añadir datos formateados a la lista
                formatted_items.append({
                    'name': item_name,
                    'value_text': value_text,
                    'total_value': price_total
                })

            # Crear vista de navegación con los items
            view = NavigationView(formatted_items, user_id, is_sell=True)

            # Crear el embed inicial
            embed = view.create_page_embed()

            # Enviar mensaje con la vista de navegación
            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"❌ Ocurrió un error al procesar tu solicitud: {str(e)}", ephemeral=False)

    @app_commands.command(
        name="tpcompra",
        description="Muestra tus órdenes de compra actuales en el bazar de Guild Wars 2"
    )
    async def bazar_compras(self, interaction: discord.Interaction):
        """Muestra la lista de órdenes de compra activas del usuario en el bazar de GW2"""
        await interaction.response.defer(ephemeral=False)

        user_id = str(interaction.user.id)
        api_key = await dbManager.getApiKey(user_id)

        if not api_key:
            await interaction.followup.send(
                "❌ No tienes una clave API de GW2 registrada. Usa `/apikey añadir` para configurar una.",
                ephemeral=False
            )
            return

        try:
            # Obtenemos las órdenes de compra en el bazar
            async with aiohttp.ClientSession() as session:
                # Primero obtenemos los listados de compra
                async with session.get(
                        f"https://api.guildwars2.com/v2/commerce/transactions/current/buys?access_token={api_key}") as response:
                    if response.status != 200:
                        await interaction.followup.send(f"❌ Error al consultar la API de GW2: {response.status}",
                                                        ephemeral=False)
                        return

                    buy_listings = await response.json()

                    if not buy_listings:
                        await interaction.followup.send(
                            "📊 No tienes ninguna orden de compra activa en el bazar actualmente.", ephemeral=False)
                        return

                # Obtenemos los precios actuales en el bazar para comparar
                item_ids = [str(item["item_id"]) for item in buy_listings]
                items_param = ",".join(item_ids)

                # Obtenemos precios y detalles de los items
                async with session.get(
                        f"https://api.guildwars2.com/v2/commerce/prices?ids={items_param}") as prices_response:
                    prices_data = await prices_response.json() if prices_response.status == 200 else []

                async with session.get(f"https://api.guildwars2.com/v2/items?ids={items_param}") as items_response:
                    items_data = await items_response.json() if items_response.status == 200 else []

            # Crear diccionarios para facilitar búsquedas
            prices_dict = {item["id"]: item for item in prices_data}
            items_dict = {item["id"]: item for item in items_data}

            # Preparamos los datos para todas las compras
            formatted_items = []

            for buying in buy_listings:
                item_id = buying["item_id"]
                item_name = items_dict[item_id]["name"] if item_id in items_dict else f"Item {item_id}"
                quantity = buying["quantity"]
                price_each = buying["price"]
                price_total = price_each * quantity

                # Precio formateado en oro/plata/cobre
                price_gold = price_each // 10000
                price_silver = (price_each % 10000) // 100
                price_copper = price_each % 100

                price_formatted = f"{price_gold}g {price_silver}s {price_copper}c"

                # Verificar el precio actual más alto de compra en el mercado
                current_highest = None
                if item_id in prices_dict and "buys" in prices_dict[item_id]:
                    current_highest = prices_dict[item_id]["buys"]["unit_price"]

                # Verificar el precio más bajo de venta actual
                current_lowest_sell = None
                if item_id in prices_dict and "sells" in prices_dict[item_id]:
                    current_lowest_sell = prices_dict[item_id]["sells"]["unit_price"]

                # Preparar mensajes de estado del precio
                price_status = ""
                buy_sell_diff = ""

                if current_highest:
                    if current_highest > price_each:
                        price_status = " ⚠️ (No es la oferta más alta)"

                    # Calcular diferencia con precio de venta más bajo
                    if current_lowest_sell:
                        diff = current_lowest_sell - price_each
                        diff_gold = diff // 10000
                        diff_silver = (diff % 10000) // 100
                        diff_copper = diff % 100

                        buy_sell_diff = f"\n**Diferencia con precio de venta:** {diff_gold}g {diff_silver}s {diff_copper}c"

                # Información del item con formato
                value_text = (
                    f"**Cantidad:** {quantity}\n"
                    f"**Tu oferta:** {price_formatted} c/u{price_status}\n"
                    f"**Total invertido:** {price_total // 10000}g {(price_total % 10000) // 100}s {price_total % 100}c"
                )

                # Añadir información de precios del mercado si está disponible
                if current_highest:
                    highest_gold = current_highest // 10000
                    highest_silver = (current_highest % 10000) // 100
                    highest_copper = current_highest % 100
                    highest_formatted = f"{highest_gold}g {highest_silver}s {highest_copper}c"

                    value_text += f"\n**Mejor oferta actual:** {highest_formatted}"

                if current_lowest_sell:
                    lowest_gold = current_lowest_sell // 10000
                    lowest_silver = (current_lowest_sell % 10000) // 100
                    lowest_copper = current_lowest_sell % 100
                    lowest_formatted = f"{lowest_gold}g {lowest_silver}s {lowest_copper}c"

                    value_text += f"\n**Precio de venta más bajo:** {lowest_formatted}{buy_sell_diff}"

                # Añadir datos formateados a la lista
                formatted_items.append({
                    'name': item_name,
                    'value_text': value_text,
                    'total_value': price_total
                })

            # Crear vista de navegación con los items
            view = NavigationView(formatted_items, user_id, is_sell=False)

            # Crear el embed inicial
            embed = view.create_page_embed()

            # Enviar mensaje con la vista de navegación
            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"❌ Ocurrió un error al procesar tu solicitud: {str(e)}", ephemeral=False)


async def setup(bot):
    await bot.add_cog(BazarCommands(bot))