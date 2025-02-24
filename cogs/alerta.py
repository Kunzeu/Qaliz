import discord
from discord.ext import commands
from discord import app_commands
import matplotlib.pyplot as plt
import io
from datetime import datetime
import json
from discord.ui import Button, View
import aiohttp
import asyncio
import re
from difflib import get_close_matches
import pickle
import os
from typing import Dict, Tuple, Any, Literal

def parse_coins(coin_str: str) -> int:
    """Convierte un string en formato XgYsZc a copper_amount"""
    total_copper = 0
    pattern = r'(\d+)([gsc])'
    matches = re.findall(pattern, coin_str.lower())
    
    for amount, unit in matches:
        amount = int(amount)
        if unit == 'g':
            total_copper += amount * 10000
        elif unit == 's':
            total_copper += amount * 100
        elif unit == 'c':
            total_copper += amount
            
    return total_copper

def format_coins(copper_amount: int) -> str:
    """Convierte copper_amount a formato XgYsZc"""
    gold = copper_amount // 10000
    silver = (copper_amount % 10000) // 100
    copper = copper_amount % 100
    
    parts = []
    if gold > 0:
        parts.append(f"{gold}g")
    if silver > 0:
        parts.append(f"{silver}s")
    if copper > 0 or not parts:
        parts.append(f"{copper}c")
    
    return "".join(parts)

class PriceView(View):
    def __init__(self, item_name):
        super().__init__(timeout=None)
        self.item_name = item_name

    @discord.ui.button(label="Detener monitoreo", style=discord.ButtonStyle.danger)
    async def stop_monitoring(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"Monitoreo detenido para {self.item_name}")
        self.stop()

    @discord.ui.button(label="Ver historial", style=discord.ButtonStyle.primary)
    async def show_history(self, interaction: discord.Interaction, button: Button):
        try:
            with open(f"price_history_{self.item_name.lower().replace(' ', '_')}.json", 'r') as f:
                history = json.load(f)
                formatted_history = []
                for entry in history:
                    formatted_entry = entry.copy()
                    formatted_entry['buy_price'] = format_coins(int(entry['buy_price']))
                    formatted_entry['sell_price'] = format_coins(int(entry['sell_price']))
                    formatted_history.append(formatted_entry)
                await interaction.response.send_message(
                    f"Historial de precios para {self.item_name}:\n```json\n{json.dumps(formatted_history, indent=2)}```"
                )
        except FileNotFoundError:
            await interaction.response.send_message("No hay historial disponible todavía.")

class GW2PriceMonitor:
    def __init__(self, bot):
        self.base_url = "https://api.guildwars2.com/v2"
        self.bot = bot
        self.price_history = {}
        self.session = None
        self.items_cache: Dict[str, Tuple[int, Any]] = {}
        self.items_cache_es: Dict[str, Tuple[int, Any]] = {}
        self.initialized = False
        self.cache_file = "items_cache.pkl"
        self.cache_expiry = 24 * 60 * 60  # 24 horas en segundos

    async def create_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    def load_cache_from_file(self) -> bool:
        """Carga el caché desde el archivo si existe y no ha expirado"""
        try:
            if not os.path.exists(self.cache_file):
                return False
                
            # Verificar si el caché ha expirado
            if (datetime.now().timestamp() - os.path.getmtime(self.cache_file)) > self.cache_expiry:
                return False
                
            with open(self.cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                self.items_cache = cached_data['en']
                self.items_cache_es = cached_data['es']
                return True
        except Exception as e:
            print(f"Error loading cache: {e}")
            return False

    def save_cache_to_file(self):
        """Guarda el caché en un archivo"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump({
                    'en': self.items_cache,
                    'es': self.items_cache_es
                }, f)
        except Exception as e:
            print(f"Error saving cache: {e}")

    async def fetch_items_chunk(self, chunk: list, lang: str = 'en') -> None:
        """Obtiene información detallada para un grupo de items"""
        try:
            ids_str = ','.join(map(str, chunk))
            url = f"{self.base_url}/items?ids={ids_str}"
            if lang != 'en':
                url += f"&lang={lang}"
                
            async with self.session.get(url) as response:
                if response.status == 200:
                    items = await response.json()
                    cache_to_use = self.items_cache if lang == 'en' else self.items_cache_es
                    
                    for item in items:
                        cache_to_use[item['name'].lower()] = (item['id'], item)
                else:
                    print(f"Error fetching items chunk: {response.status}")
        except Exception as e:
            print(f"Error in fetch_items_chunk: {e}")

    async def initialize_cache(self):
        """Inicializa el caché de items de manera eficiente"""
        if self.initialized:
            return

        print("Iniciando carga del caché de items...")
        
        # Intentar cargar desde archivo primero
        if self.load_cache_from_file():
            print("Caché cargado desde archivo")
            self.initialized = True
            return

        await self.create_session()
        
        try:
            # Obtener lista de IDs
            async with self.session.get(f"{self.base_url}/items") as response:
                if response.status != 200:
                    print(f"Error al obtener lista de items: {response.status}")
                    return
                all_item_ids = await response.json()

            # Procesar items en chunks
            chunk_size = 200
            chunks = [all_item_ids[i:i + chunk_size] for i in range(0, len(all_item_ids), chunk_size)]
            
            # Crear tareas para ambos idiomas
            tasks = []
            for chunk in chunks:
                tasks.append(self.fetch_items_chunk(chunk, 'en'))
                tasks.append(self.fetch_items_chunk(chunk, 'es'))
            
            # Ejecutar tareas en grupos para evitar sobrecarga
            batch_size = 5
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                await asyncio.gather(*batch)
                print(f"Progreso: {min(i + batch_size, len(tasks))}/{len(tasks)} tareas completadas")
            
            # Guardar caché en archivo
            self.save_cache_to_file()
            
            print("Caché de items completado")
            self.initialized = True
            
        except Exception as e:
            print(f"Error durante la inicialización del caché: {e}")

    async def get_item_id(self, item_name: str) -> Tuple[int, Any]:
        """Busca un item por nombre y retorna su ID y detalles"""
        if not self.initialized:
            print("Inicializando caché...")
            await self.initialize_cache()
            
        item_name_lower = item_name.lower()
        
        # Búsqueda exacta
        if item_name_lower in self.items_cache:
            return self.items_cache[item_name_lower]
        if item_name_lower in self.items_cache_es:
            return self.items_cache_es[item_name_lower]
            
        # Búsqueda aproximada
        all_names = list(self.items_cache.keys()) + list(self.items_cache_es.keys())
        matches = get_close_matches(item_name_lower, all_names, n=1, cutoff=0.8)
        
        if matches:
            matched_name = matches[0]
            return (self.items_cache.get(matched_name) or 
                   self.items_cache_es.get(matched_name))
            
        return None, None

    async def get_current_price(self, item_id):
        await self.create_session()
        async with self.session.get(f"{self.base_url}/commerce/prices/{item_id}") as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'buy_price': data['buys']['unit_price'],
                    'sell_price': data['sells']['unit_price']
                }
        return None

    def save_price_history(self, item_name, price_data):
        filename = f"price_history_{item_name.lower().replace(' ', '_')}.json"
        try:
            with open(filename, 'r') as f:
                history = json.load(f)
        except FileNotFoundError:
            history = []
            
        history.append({
            'timestamp': datetime.now().isoformat(),
            'buy_price': price_data['buy_price'],
            'sell_price': price_data['sell_price']
        })
        
        with open(filename, 'w') as f:
            json.dump(history, f, indent=2)
            
        return history

    async def create_price_chart(self, item_name, history):
        plt.figure(figsize=(10, 6))
        dates = [datetime.fromisoformat(entry['timestamp']) for entry in history]
        prices = [entry['sell_price'] / 10000 for entry in history]
        
        plt.plot(dates, prices, marker='o')
        plt.title(f'Tendencia de precios para {item_name}')
        plt.xlabel('Fecha')
        plt.ylabel('Precio (oro)')
        plt.xticks(rotation=45)
        plt.grid(True)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf

    async def create_price_embed(self, item_details, current_prices, target_price, history, price_type: str):
        price_key = 'buy_price' if price_type == 'buy' else 'sell_price'
        current_price = current_prices[price_key]
        
        embed = discord.Embed(
            title=f"Monitor de precios: {item_details['name']} ({price_type.upper()})",
            color=discord.Color.blue() if current_price > target_price else discord.Color.green()
        )
        
        if 'icon' in item_details:
            embed.set_thumbnail(url=item_details['icon'])
            
        embed.add_field(
            name="Precio actual",
            value=f"💰 Venta: **{format_coins(current_prices['sell_price'])}**\n"
                  f"💵 Compra: **{format_coins(current_prices['buy_price'])}**",
            inline=False
        )
        
        embed.add_field(
            name="Precio objetivo",
            value=f"🎯 **{format_coins(target_price)}**",
            inline=True
        )
        
        diff = current_price - target_price
        embed.add_field(
            name="Diferencia",
            value=f"{'🔺' if diff > 0 else '🔽'} **{format_coins(abs(diff))}**",
            inline=True
        )
        
        if len(history) > 1:
            price_change = history[-1][price_key] - history[0][price_key]
            trend = "📈" if price_change > 0 else "📉"
            embed.add_field(
                name="Tendencia",
                value=f"{trend} {format_coins(abs(price_change))}",
                inline=True
            )
            
        embed.set_footer(text=f"Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return embed

    async def monitor_price(self, user_id: int, item_name: str, target_price: int, price_type: str, check_interval: int = 300):
        await self.create_session()
        item_id, item_details = await self.get_item_id(item_name)
        if not item_id:
            return f"No se encontró el ítem: {item_name}"

        user = await self.bot.fetch_user(user_id)
        if not user:
            return "No se pudo encontrar el usuario en Discord"

        view = PriceView(item_name)
        initial_message = await user.send(f"🔍 Iniciando monitoreo ({price_type.upper()}) para **{item_name}**...")

        try:
            while True:
                current_prices = await self.get_current_price(item_id)
                if current_prices:
                    history = self.save_price_history(item_name, current_prices)
                    chart_buffer = await self.create_price_chart(item_name, history)
                    embed = await self.create_price_embed(item_details, current_prices, target_price, history, price_type)
                    
                    file = discord.File(chart_buffer, filename="price_trend.png")
                    embed.set_image(url="attachment://price_trend.png")
                    
                    await initial_message.edit(content=None, embed=embed, attachments=[file], view=view)
                    
                    current_price = current_prices['buy_price'] if price_type == 'buy' else current_prices['sell_price']
                    price_condition = (current_price >= target_price if price_type == 'buy' else current_price <= target_price)
                    
                    if price_condition:
                        alert_embed = discord.Embed(
                            title="🎯 ¡Precio objetivo alcanzado!",
                            description=f"El precio de **{item_name}** ha llegado a tu objetivo ({price_type.upper()})",
                            color=discord.Color.green()
                        )
                        await user.send(embed=alert_embed)
                        break
                        
                await asyncio.sleep(check_interval)
                
        except Exception as e:
            await user.send(f"❌ Error durante el monitoreo: {str(e)}")
            raise e

class PriceAlert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.price_monitor = GW2PriceMonitor(bot)

    @app_commands.command(
        name="monitor",
        description="Monitorea el precio de un ítem de GW2 hasta que alcance el precio objetivo"
    )
    @app_commands.describe(
        item_name="Nombre exacto del ítem (en inglés o español)",
        precio="Precio objetivo en formato XgYsZc (ejemplo: 500g50s0c)",
        tipo="Tipo de precio a monitorear (buy/sell)"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Buy", value="buy"),
        app_commands.Choice(name="Sell", value="sell")
    ])
    async def monitor(self, interaction: discord.Interaction, item_name: str, precio: str, 
                     tipo: Literal["buy", "sell"]):
        try:
            await interaction.response.defer(ephemeral=True, thinking=True)
            
            if not self.price_monitor.initialized:
                await interaction.followup.send(
                    "🔄 Inicializando base de datos de items por primera vez...\n"
                    "Esto puede tomar unos momentos...",
                    ephemeral=True
                )
            
            target_price = parse_coins(precio)
            
            if target_price == 0:
                await interaction.followup.send(
                    "❌ El precio objetivo debe ser mayor que 0",
                    ephemeral=True
                )
                return
            
            item_id, item_details = await self.price_monitor.get_item_id(item_name)
            if not item_id:
                await interaction.followup.send(
                    f"❌ No se encontró el ítem: {item_name}\n"
                    "Asegúrate de escribir el nombre exactamente como aparece en el juego.",
                    ephemeral=True
                )
                return
                
            await interaction.followup.send(
                f"✅ Iniciando monitoreo de precio ({tipo.upper()}) para {item_details['name']}. "
                "Te enviaré actualizaciones por DM.",
                ephemeral=True
            )
            
            await self.price_monitor.monitor_price(interaction.user.id, item_details['name'], target_price, tipo)
            
        except ValueError as e:
            await interaction.followup.send(
                f"❌ Error en el formato del precio. Usa el formato XgYsZc (ejemplo: 500g50s0c)",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Ocurrió un error: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(PriceAlert(bot))
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")    