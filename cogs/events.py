import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import pytz
import re
from typing import Optional
from utils.database import dbManager

TZ_CEST = pytz.timezone('Europe/Madrid')  # CEST / CET

# ─────────────────────────────────────────────────────────
#  Plantillas de composición GW2
# ─────────────────────────────────────────────────────────
TEMPLATES: dict = {
    "raid": {
        "display": "Raid",
        "roles": [
            {"id": "hboon", "name": "HBoon", "emoji": "💙", "max_slots": 2, "category": None},
            {"id": "bdps",  "name": "BDPS",  "emoji": "🟠", "max_slots": 2, "category": None},
            {"id": "dps",   "name": "DPS",   "emoji": "🔴", "max_slots": 6, "category": None},
        ],
    },
    "convergencia": {
        "display": "Convergencia",
        "roles": [
            {"id": "hboon", "name": "HBoon", "emoji": "💙", "max_slots": 5,  "category": None},
            {"id": "bdps",  "name": "BDPS",  "emoji": "🟠", "max_slots": 5,  "category": None},
            {"id": "dps",   "name": "DPS",   "emoji": "🔴", "max_slots": 40, "category": None},
        ],
    },
    "custom": {
        "display": "Personalizado",
        "roles": [],
    },
}

# ─────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────

def _total_slots(roles: list) -> int:
    return sum(r.get("max_slots", 1) for r in roles)


def _total_participants(roles: list) -> int:
    return sum(len(r.get("participants", [])) for r in roles)


def _participant_display(p: dict) -> str:
    """Texto a mostrar para un participante: nombre de cuenta + mención opcional."""
    name = p.get("name", "")
    discord_id = p.get("discord_id")
    if name and discord_id:
        return f"{name} (<@{discord_id}>)"
    if discord_id:
        return f"<@{discord_id}>"
    return name or "Desconocido"


def build_event_embed(event: dict, guild: Optional[discord.Guild]) -> discord.Embed:
    """Construye el embed visual de un evento."""
    status = event.get("status", "open")
    color_map = {"open": 0x5865F2, "closed": 0xFEE75C, "cancelled": 0xED4245}
    color = color_map.get(status, 0x5865F2)

    start_ts: int = event.get("start_ts", 0)
    end_ts: int   = event.get("end_ts", 0)
    creator_id    = event.get("creator_id", 0)
    roles: list   = event.get("roles", [])
    title: str    = event.get("title", "Evento")

    total_p = _total_participants(roles)
    total_s = _total_slots(roles)

    # ── Tiempo relativo + absoluto ────────────────────────
    time_lines: list[str] = []
    if start_ts:
        now_ts   = int(datetime.now().timestamp())
        diff_sec = start_ts - now_ts
        diff_days = diff_sec // 86400
        if diff_days > 0:
            time_lines.append(f"This event will start in **{diff_days} day{'s' if diff_days != 1 else ''}**.")
        elif diff_days == 0:
            time_lines.append("This event starts **today**.")
        else:
            time_lines.append("This event has already started.")
        time_lines.append(f"🗓 Start time: <t:{start_ts}:F>")
        if end_ts:
            time_lines.append(f"🏁 End time: <t:{end_ts}:t>")

    # ── Descripción: estado si no es open ────────────────
    desc_parts: list[str] = []
    if status == "closed":
        desc_parts.append("🔒 **Inscripciones cerradas**")
    elif status == "cancelled":
        desc_parts.append("❌ **Evento cancelado**")

    embed = discord.Embed(
        title=title,
        description="\n".join(desc_parts) if desc_parts else None,
        color=color,
    )
    embed.add_field(name="👑 Leader",       value=f"<@{creator_id}>",     inline=True)
    embed.add_field(name="👥 Participants", value=f"{total_p}/{total_s}", inline=True)
    embed.add_field(name="\u200b",          value="\u200b",               inline=False)

    # ── Separar roles con y sin categoría ────────────────
    categories: dict  = {}
    uncategorized: list = []
    for role in roles:
        cat = role.get("category")
        if cat:
            categories.setdefault(cat, []).append(role)
        else:
            uncategorized.append(role)

    # ── Roles sin categoría ───────────────────────────────
    for role in uncategorized:
        participants: list = role.get("participants", [])
        max_s: int         = role.get("max_slots", 1)
        filled             = len(participants)
        emoji              = role.get("emoji", "")
        name_str           = f"{emoji} {role['name']}" if emoji else role["name"]

        lines = [f"> {_participant_display(p)}" for p in participants]
        lines += ["> "] * (max_s - filled)

        embed.add_field(
            name=f"{name_str} ({filled}/{max_s})",
            value="\n".join(lines) if lines else "> \u200b",
            inline=False,
        )

    # ── Roles agrupados por categoría ────────────────────
    for cat_name, cat_roles in categories.items():
        cat_p = sum(len(r.get("participants", [])) for r in cat_roles)
        cat_s = sum(r.get("max_slots", 1) for r in cat_roles)
        lines: list[str] = []

        for role in cat_roles:
            participants = role.get("participants", [])
            max_s        = role.get("max_slots", 1)
            filled       = len(participants)
            emoji        = role.get("emoji", "")
            role_label   = f"{emoji} {role['name']}" if emoji else role["name"]
            lines.append(f"**{role_label} ({filled}/{max_s})**")
            for p in participants:
                lines.append(f"> {_participant_display(p)}")
            lines += ["> "] * (max_s - filled)

        embed.add_field(
            name=f"{cat_name} ({cat_p}/{cat_s})",
            value="\n".join(lines),
            inline=False,
        )

    # ── Tiempo al final ───────────────────────────────────
    if time_lines:
        embed.add_field(name="\u200b", value="\n".join(time_lines), inline=False)

    status_footer = {
        "open":      "📝 Open for registration",
        "closed":    "🔒 Registration closed",
        "cancelled": "❌ Event cancelled",
    }.get(status, "")
    embed.set_footer(text=f"ID: {event.get('doc_id', 'N/A')} • {status_footer}")
    return embed


# ─────────────────────────────────────────────────────────
#  Modal — nombre de cuenta al registrarse
# ─────────────────────────────────────────────────────────

class RegisterNameModal(discord.ui.Modal, title="📝 Registrarse en el evento"):
    nombre = discord.ui.TextInput(
        label="Nombre de cuenta / ID",
        placeholder="Ej: NombreCuenta.1234",
        required=True,
        max_length=100,
    )

    def __init__(self, doc_id: str, role_id: str, default_name: str = ""):
        super().__init__()
        self.doc_id = doc_id
        self.role_id = role_id
        if default_name:
            self.nombre.default = default_name

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        account_name = self.nombre.value.strip()
        user_id = interaction.user.id

        event = await dbManager.getEvent(self.doc_id)
        if not event:
            await interaction.followup.send("❌ Evento no encontrado.", ephemeral=True)
            return
        if event.get("status") != "open":
            await interaction.followup.send("❌ Las inscripciones están cerradas.", ephemeral=True)
            return

        roles: list = event.get("roles", [])
        target = next((r for r in roles if r["id"] == self.role_id), None)
        if not target:
            await interaction.followup.send("❌ Rol no encontrado.", ephemeral=True)
            return
        if len(target.get("participants", [])) >= target.get("max_slots", 1):
            await interaction.followup.send(
                f"❌ El rol **{target['name']}** está completo.", ephemeral=True
            )
            return

        # Quitar del rol actual si ya estaba (por discord_id)
        already_in: Optional[str] = None
        for role in roles:
            for p in list(role.get("participants", [])):
                if p.get("discord_id") == user_id:
                    role["participants"].remove(p)
                    already_in = role["name"]
                    break

        target.setdefault("participants", []).append(
            {"name": account_name, "discord_id": user_id}
        )

        await dbManager.updateEventRoles(self.doc_id, roles)
        event["roles"] = roles
        await _refresh_event_message(event, interaction.guild)

        if already_in:
            await interaction.followup.send(
                f"✅ Cambiado de **{already_in}** a **{target['name']}** como `{account_name}`.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                f"✅ Registrado en **{target['name']}** como `{account_name}`.",
                ephemeral=True,
            )


# ─────────────────────────────────────────────────────────
#  Select temporal — elige rol → abre RegisterNameModal
# ─────────────────────────────────────────────────────────

class RolePickerSelect(discord.ui.Select):
    def __init__(self, doc_id: str, roles: list, default_name: str):
        self.doc_id = doc_id
        self.default_name = default_name

        options = []
        for role in roles:
            filled = len(role.get("participants", []))
            max_s = role.get("max_slots", 1)
            if filled >= max_s:
                continue
            emoji_raw = role.get("emoji")
            try:
                parsed_emoji = discord.PartialEmoji.from_str(emoji_raw) if emoji_raw else None
            except Exception:
                parsed_emoji = None
            options.append(
                discord.SelectOption(
                    label=f"{role['name']} ({filled}/{max_s})",
                    value=role["id"],
                    description=f"{max_s - filled} slot(s) libre(s)",
                    emoji=parsed_emoji,
                )
            )

        if not options:
            options = [discord.SelectOption(label="Todos los roles están llenos", value="_full")]

        super().__init__(
            placeholder="Selecciona un rol...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        role_id = self.values[0]
        if role_id == "_full":
            await interaction.response.send_message(
                "❌ Todos los roles están completos.", ephemeral=True
            )
            return
        modal = RegisterNameModal(self.doc_id, role_id, self.default_name)
        await interaction.response.send_modal(modal)


class RolePickerView(discord.ui.View):
    def __init__(self, doc_id: str, roles: list, default_name: str):
        super().__init__(timeout=60)
        self.add_item(RolePickerSelect(doc_id, roles, default_name))


# ─────────────────────────────────────────────────────────
#  Vista principal persistente del evento
# ─────────────────────────────────────────────────────────

class RegisterButton(discord.ui.Button):
    def __init__(self, doc_id: str, disabled: bool = False):
        super().__init__(
            label="Register",
            style=discord.ButtonStyle.success,
            emoji="📝",
            custom_id=f"event:register:{doc_id}",
            disabled=disabled,
            row=0,
        )
        self.event_doc_id = doc_id

    async def callback(self, interaction: discord.Interaction) -> None:
        event = await dbManager.getEvent(self.event_doc_id)
        if not event:
            await interaction.response.send_message("❌ Evento no encontrado.", ephemeral=True)
            return
        if event.get("status") != "open":
            await interaction.response.send_message("❌ Las inscripciones están cerradas.", ephemeral=True)
            return

        roles: list = event.get("roles", [])
        any_free = any(
            len(r.get("participants", [])) < r.get("max_slots", 1) for r in roles
        )
        if not any_free:
            await interaction.response.send_message(
                "❌ Todos los roles están completos.", ephemeral=True
            )
            return

        default_name = await _get_gw2_account_name(interaction.user.id)
        view = RolePickerView(self.event_doc_id, roles, default_name)
        await interaction.response.send_message(
            "Selecciona el rol al que quieres apuntarte:", view=view, ephemeral=True
        )


class UnregisterButton(discord.ui.Button):
    def __init__(self, doc_id: str, disabled: bool = False):
        super().__init__(
            label="Unregister",
            style=discord.ButtonStyle.danger,
            emoji="✖️",
            custom_id=f"event:unregister:{doc_id}",
            disabled=disabled,
            row=0,
        )
        self.event_doc_id = doc_id

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id

        event = await dbManager.getEvent(self.event_doc_id)
        if not event:
            await interaction.followup.send("❌ Evento no encontrado.", ephemeral=True)
            return
        if event.get("status") != "open":
            await interaction.followup.send("❌ Las inscripciones están cerradas.", ephemeral=True)
            return

        roles: list = event.get("roles", [])
        removed: Optional[str] = None
        removed_role: Optional[str] = None

        for role in roles:
            for p in list(role.get("participants", [])):
                if p.get("discord_id") == user_id:
                    role["participants"].remove(p)
                    removed = p.get("name", str(user_id))
                    removed_role = role["name"]
                    break
            if removed:
                break

        if not removed:
            await interaction.followup.send(
                "❌ No estás registrado en ningún rol.", ephemeral=True
            )
            return

        await dbManager.updateEventRoles(self.event_doc_id, roles)
        event["roles"] = roles
        await _refresh_event_message(event, interaction.guild)
        await interaction.followup.send(
            f"✅ Te has retirado del rol **{removed_role}** (`{removed}`).", ephemeral=True
        )


class InterestedButton(discord.ui.Button):
    def __init__(self, doc_id: str, disabled: bool = False):
        super().__init__(
            label="Interested",
            style=discord.ButtonStyle.secondary,
            emoji="🔔",
            custom_id=f"event:interested:{doc_id}",
            disabled=disabled,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "🔔 Se te notificará si hay plazas disponibles.", ephemeral=True
        )


class EventMainView(discord.ui.View):
    """Vista persistente del evento: Register · Unregister · Interested."""

    def __init__(self, event_data: dict):
        super().__init__(timeout=None)
        is_closed = event_data.get("status", "open") != "open"
        doc_id = str(event_data.get("doc_id", "0"))
        self.add_item(RegisterButton(doc_id,    disabled=is_closed))
        self.add_item(UnregisterButton(doc_id,  disabled=is_closed))
        self.add_item(InterestedButton(doc_id,  disabled=is_closed))


# ─────────────────────────────────────────────────────────
#  Shared helper para refrescar el mensaje del evento
# ─────────────────────────────────────────────────────────

async def _get_gw2_account_name(user_id: int) -> str:
    """Devuelve el nombre de cuenta GW2 activa del usuario, o cadena vacía."""
    try:
        keys = await dbManager.getApiKeysList(user_id)
        for key in keys:
            if key.get("active"):
                return key.get("account_name", "")
    except Exception:
        pass
    return ""


async def _refresh_event_message(event: dict, guild: Optional[discord.Guild]) -> None:
    if not guild:
        return
    try:
        channel = guild.get_channel(int(event.get("channel_id", 0)))
        if not channel:
            return
        msg = await channel.fetch_message(int(event.get("message_id", 0)))
        embed = build_event_embed(event, guild)
        view = EventMainView(event)
        await msg.edit(embed=embed, view=view)
    except Exception as e:
        print(f"⚠️ Error refrescando mensaje del evento: {e}")


# ─────────────────────────────────────────────────────────
#  Modals
# ─────────────────────────────────────────────────────────

class EventCreateModal(discord.ui.Modal, title="📅 Crear Evento"):
    titulo = discord.ui.TextInput(
        label="Título del evento",
        placeholder="Ej: Weekly Fractals T4",
        required=True,
        max_length=100,
    )
    fecha_inicio = discord.ui.TextInput(
        label="Fecha (DD/MM/YYYY)",
        placeholder="31/05/2026",
        required=True,
        max_length=10,
    )
    hora_inicio = discord.ui.TextInput(
        label="Hora inicio (HH:MM) — CEST",
        placeholder="15:00",
        required=True,
        max_length=5,
    )
    hora_fin = discord.ui.TextInput(
        label="Hora fin (HH:MM) — CEST",
        placeholder="19:00",
        required=True,
        max_length=5,
    )

    def __init__(self, template_key: str, cog: "Events"):
        super().__init__()
        self.template_key = template_key
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        # Parsear fecha/hora
        try:
            date_str   = self.fecha_inicio.value.strip()
            start_str  = self.hora_inicio.value.strip()
            end_str    = self.hora_fin.value.strip()
            start_dt   = TZ_CEST.localize(datetime.strptime(f"{date_str} {start_str}", "%d/%m/%Y %H:%M"))
            end_dt     = TZ_CEST.localize(datetime.strptime(f"{date_str} {end_str}",   "%d/%m/%Y %H:%M"))
            start_ts   = int(start_dt.timestamp())
            end_ts     = int(end_dt.timestamp())
        except ValueError:
            await interaction.followup.send(
                "❌ Formato inválido. Fecha: `DD/MM/YYYY`, hora: `HH:MM`.", ephemeral=True
            )
            return

        template = TEMPLATES.get(self.template_key, TEMPLATES["custom"])
        roles = [{**r, "participants": []} for r in template["roles"]]

        event_data: dict = {
            "guild_id":   interaction.guild_id,
            "channel_id": interaction.channel_id,
            "creator_id": interaction.user.id,
            "title":      self.titulo.value.strip(),
            "start_ts":   start_ts,
            "end_ts":     end_ts,
            "status":     "open",
            "roles":      roles,
            "created_at": datetime.now(),
        }

        # Enviar mensaje provisional para obtener el message_id
        placeholder = discord.Embed(title="⏳ Creando evento…", color=0x5865F2)
        msg = await interaction.channel.send(embed=placeholder)

        event_data["message_id"] = msg.id
        event_data["doc_id"]     = str(msg.id)

        saved = await dbManager.saveEvent(event_data)
        if not saved:
            await msg.delete()
            await interaction.followup.send("❌ Error al guardar el evento en la base de datos.", ephemeral=True)
            return

        embed = build_event_embed(event_data, interaction.guild)
        view  = EventMainView(event_data)
        self.cog.bot.add_view(view, message_id=msg.id)
        await msg.edit(embed=embed, view=view)

        await interaction.followup.send("✅ Evento creado exitosamente.", ephemeral=True)


class EventAddRoleModal(discord.ui.Modal, title="➕ Añadir Rol al Evento"):
    nombre = discord.ui.TextInput(
        label="Nombre del rol",
        placeholder="Ej: Heal Quickness",
        required=True,
        max_length=50,
    )
    emoji = discord.ui.TextInput(
        label="Emoji (opcional)",
        placeholder="💙",
        required=False,
        max_length=10,
    )
    slots = discord.ui.TextInput(
        label="Número de slots",
        placeholder="2",
        required=True,
        max_length=2,
    )
    categoria = discord.ui.TextInput(
        label="Categoría (opcional)",
        placeholder="Special Roles",
        required=False,
        max_length=50,
    )

    def __init__(self, doc_id: str, cog: "Events"):
        super().__init__()
        self.doc_id = doc_id
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        try:
            num_slots = int(self.slots.value.strip())
            if not (1 <= num_slots <= 50):
                raise ValueError
        except ValueError:
            await interaction.followup.send("❌ Número de slots inválido (1–50).", ephemeral=True)
            return

        event = await dbManager.getEvent(self.doc_id)
        if not event:
            await interaction.followup.send("❌ Evento no encontrado.", ephemeral=True)
            return
        if (
            event.get("creator_id") != interaction.user.id
            and not interaction.user.guild_permissions.administrator
        ):
            await interaction.followup.send("❌ No tienes permiso para modificar este evento.", ephemeral=True)
            return

        roles: list = event.get("roles", [])
        role_name = self.nombre.value.strip()

        # Generar ID único
        base_id = re.sub(r"[^a-z0-9_]", "_", role_name.lower())[:20]
        role_id = base_id
        existing_ids = {r["id"] for r in roles}
        counter = 1
        while role_id in existing_ids:
            role_id = f"{base_id}_{counter}"
            counter += 1

        roles.append({
            "id":           role_id,
            "name":         role_name,
            "emoji":        self.emoji.value.strip() or None,
            "max_slots":    num_slots,
            "category":     self.categoria.value.strip() or None,
            "participants": [],
        })

        await dbManager.updateEventRoles(self.doc_id, roles)
        event["roles"] = roles
        await _refresh_event_message(event, interaction.guild)
        await interaction.followup.send(f"✅ Rol **{role_name}** añadido al evento.", ephemeral=True)


# ─────────────────────────────────────────────────────────
#  Cog principal
# ─────────────────────────────────────────────────────────

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        """Restaura las vistas persistentes de todos los eventos abiertos."""
        try:
            events = await dbManager.getOpenEvents()
            for event in events:
                view = EventMainView(event)
                self.bot.add_view(view, message_id=int(event.get("message_id", 0)))
            print(f"✅ {len(events)} evento(s) restaurado(s)")
        except Exception as e:
            print(f"⚠️ Error restaurando eventos: {e}")

    # ── Grupo de comandos /raid ────────────────────────────

    raid = app_commands.Group(name="raid", description="Gestión de raids/eventos con inscripción de roles")

    @raid.command(name="crear", description="Crea un nuevo evento con sign-up por roles")
    @app_commands.describe(plantilla="Composición predefinida de roles")
    @app_commands.choices(plantilla=[
        app_commands.Choice(name="Raid",         value="raid"),
        app_commands.Choice(name="Convergencia", value="convergencia"),
    ])
    async def crear(self, interaction: discord.Interaction, plantilla: str = "raid") -> None:
        await interaction.response.send_modal(EventCreateModal(plantilla, self))

    @raid.command(name="addrol", description="Añade un rol personalizado a un evento existente")
    @app_commands.describe(mensaje_id="ID del mensaje del evento (clic derecho → Copiar ID)")
    async def addrol(self, interaction: discord.Interaction, mensaje_id: str) -> None:
        event = await dbManager.getEvent(mensaje_id)
        if not event:
            await interaction.response.send_message("❌ Evento no encontrado.", ephemeral=True)
            return
        if (
            event.get("creator_id") != interaction.user.id
            and not interaction.user.guild_permissions.administrator
        ):
            await interaction.response.send_message(
                "❌ Solo el creador o un administrador puede modificar este evento.", ephemeral=True
            )
            return
        await interaction.response.send_modal(EventAddRoleModal(mensaje_id, self))

    @raid.command(name="cerrar", description="Cierra las inscripciones de un evento")
    @app_commands.describe(mensaje_id="ID del mensaje del evento")
    async def cerrar(self, interaction: discord.Interaction, mensaje_id: str) -> None:
        await interaction.response.defer(ephemeral=True)
        event = await dbManager.getEvent(mensaje_id)
        if not event:
            await interaction.followup.send("❌ Evento no encontrado.", ephemeral=True)
            return
        if (
            event.get("creator_id") != interaction.user.id
            and not interaction.user.guild_permissions.administrator
        ):
            await interaction.followup.send("❌ No tienes permiso.", ephemeral=True)
            return

        await dbManager.updateEventStatus(mensaje_id, "closed")
        event["status"] = "closed"
        await _refresh_event_message(event, interaction.guild)
        await interaction.followup.send("✅ Inscripciones cerradas.", ephemeral=True)

    @raid.command(name="abrir", description="Vuelve a abrir las inscripciones de un evento")
    @app_commands.describe(mensaje_id="ID del mensaje del evento")
    async def abrir(self, interaction: discord.Interaction, mensaje_id: str) -> None:
        await interaction.response.defer(ephemeral=True)
        event = await dbManager.getEvent(mensaje_id)
        if not event:
            await interaction.followup.send("❌ Evento no encontrado.", ephemeral=True)
            return
        if (
            event.get("creator_id") != interaction.user.id
            and not interaction.user.guild_permissions.administrator
        ):
            await interaction.followup.send("❌ No tienes permiso.", ephemeral=True)
            return

        await dbManager.updateEventStatus(mensaje_id, "open")
        event["status"] = "open"
        view = EventMainView(event)
        self.bot.add_view(view, message_id=int(event.get("message_id", 0)))
        await _refresh_event_message(event, interaction.guild)
        await interaction.followup.send("✅ Inscripciones abiertas de nuevo.", ephemeral=True)

    @raid.command(name="sign", description="Registra manualmente a alguien en un rol del evento")
    @app_commands.describe(
        mensaje_id="ID del mensaje del evento",
        rol="Nombre del rol (ej: Heal Quickness)",
        nombre="Nombre de cuenta / ID a registrar",
        usuario="Usuario de Discord (opcional)",
    )
    async def sign(
        self,
        interaction: discord.Interaction,
        mensaje_id: str,
        rol: str,
        nombre: str,
        usuario: Optional[discord.Member] = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        event = await dbManager.getEvent(mensaje_id)
        if not event:
            await interaction.followup.send("❌ Evento no encontrado.", ephemeral=True)
            return
        if (
            event.get("creator_id") != interaction.user.id
            and not interaction.user.guild_permissions.administrator
        ):
            await interaction.followup.send("❌ No tienes permiso.", ephemeral=True)
            return

        roles: list = event.get("roles", [])
        target = next(
            (r for r in roles if r["name"].lower() == rol.lower() or r["id"].lower() == rol.lower()),
            None,
        )
        if not target:
            await interaction.followup.send(
                f"❌ Rol `{rol}` no encontrado. Comprueba el nombre exacto.", ephemeral=True
            )
            return
        if len(target.get("participants", [])) >= target.get("max_slots", 1):
            await interaction.followup.send(
                f"❌ El rol **{target['name']}** está completo.", ephemeral=True
            )
            return

        discord_id = usuario.id if usuario else None
        # Quitar de otro rol si ya estaba (por discord_id)
        if discord_id:
            for role in roles:
                for p in list(role.get("participants", [])):
                    if p.get("discord_id") == discord_id:
                        role["participants"].remove(p)
                        break

        target.setdefault("participants", []).append(
            {"name": nombre.strip(), "discord_id": discord_id}
        )
        await dbManager.updateEventRoles(mensaje_id, roles)
        event["roles"] = roles
        await _refresh_event_message(event, interaction.guild)
        mention = usuario.mention if usuario else f"`{nombre}`"
        await interaction.followup.send(
            f"✅ {mention} registrado en **{target['name']}** como `{nombre}`.", ephemeral=True
        )

    @raid.command(name="unsign", description="Elimina a un participante del evento por nombre de cuenta")
    @app_commands.describe(
        mensaje_id="ID del mensaje del evento",
        nombre="Nombre de cuenta a eliminar",
    )
    async def unsign(self, interaction: discord.Interaction, mensaje_id: str, nombre: str) -> None:
        await interaction.response.defer(ephemeral=True)
        event = await dbManager.getEvent(mensaje_id)
        if not event:
            await interaction.followup.send("❌ Evento no encontrado.", ephemeral=True)
            return
        if (
            event.get("creator_id") != interaction.user.id
            and not interaction.user.guild_permissions.administrator
        ):
            await interaction.followup.send("❌ No tienes permiso.", ephemeral=True)
            return

        roles: list = event.get("roles", [])
        target_name = nombre.strip().lower()
        removed: Optional[str] = None
        removed_role: Optional[str] = None

        for role in roles:
            for p in list(role.get("participants", [])):
                if p.get("name", "").lower() == target_name:
                    role["participants"].remove(p)
                    removed = p["name"]
                    removed_role = role["name"]
                    break
            if removed:
                break

        if not removed:
            await interaction.followup.send(
                f"❌ No se encontró ningún participante con el nombre `{nombre}`.", ephemeral=True
            )
            return

        await dbManager.updateEventRoles(mensaje_id, roles)
        event["roles"] = roles
        await _refresh_event_message(event, interaction.guild)
        await interaction.followup.send(
            f"✅ `{removed}` eliminado del rol **{removed_role}**.", ephemeral=True
        )

    @raid.command(name="cancelar", description="Cancela un evento")
    @app_commands.describe(mensaje_id="ID del mensaje del evento")
    async def cancelar(self, interaction: discord.Interaction, mensaje_id: str) -> None:
        await interaction.response.defer(ephemeral=True)
        event = await dbManager.getEvent(mensaje_id)
        if not event:
            await interaction.followup.send("❌ Evento no encontrado.", ephemeral=True)
            return
        if (
            event.get("creator_id") != interaction.user.id
            and not interaction.user.guild_permissions.administrator
        ):
            await interaction.followup.send("❌ No tienes permiso.", ephemeral=True)
            return

        await dbManager.updateEventStatus(mensaje_id, "cancelled")
        event["status"] = "cancelled"
        await _refresh_event_message(event, interaction.guild)
        await interaction.followup.send("✅ Evento cancelado.", ephemeral=True)

    @raid.command(name="lista", description="Muestra los eventos del servidor")
    async def lista(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        events = await dbManager.getGuildEvents(str(interaction.guild_id))
        if not events:
            await interaction.followup.send("📭 No hay eventos registrados en este servidor.", ephemeral=True)
            return

        status_icon = {"open": "🟢", "closed": "🔒", "cancelled": "❌"}
        lines = []
        for ev in events[:15]:
            icon  = status_icon.get(ev.get("status", "open"), "❓")
            start = ev.get("start_ts", 0)
            ts    = f"<t:{start}:d>" if start else "Sin fecha"
            lines.append(
                f"{icon} **{ev.get('title', 'Sin título')}** — {ts} "
                f"(ID: `{ev.get('doc_id')}`)"
            )

        embed = discord.Embed(
            title="📅 Eventos del servidor",
            description="\n".join(lines),
            color=0x5865F2,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Events(bot))
