import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List, Dict, Any


class RoleToggleButton(discord.ui.Button):
    """Botón que alterna un rol específico."""

    def __init__(self, message_id: int, role_id: int, label: str, emoji: Optional[str] = None, row: Optional[int] = None):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            custom_id=f"role:toggle:{message_id}:{role_id}",
            emoji=emoji if emoji else None,
            row=row,
        )
        self.message_id = message_id
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction) -> None:  # type: ignore[override]
        if not interaction.guild:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            return

        guild = interaction.guild
        member = interaction.user  # type: ignore[assignment]

        role = guild.get_role(self.role_id)
        if role is None:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            return

        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            if role not in member.roles:  # type: ignore[attr-defined]
                await member.add_roles(role, reason=f"Self-assign via button (msg {self.message_id})")
            else:
                await member.remove_roles(role, reason=f"Self-assign via button (msg {self.message_id})")
        except discord.Forbidden:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)


class RoleButtonsView(discord.ui.View):
    """Vista persistente con múltiples botones, uno por rol."""

    def __init__(self, message_id: int):
        super().__init__(timeout=None)
        self.message_id = message_id

    def add_role_button(self, role: discord.Role, emoji: Optional[str] = None, row: Optional[int] = None):
        self.add_item(RoleToggleButton(message_id=self.message_id, role_id=role.id, label="", emoji=emoji, row=row))


class RoleAssigner(commands.Cog):
    """Cog para crear mensajes con botones de auto-asignación de rol."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Firestore
        self.db = getattr(self.bot, "db", None)
        self.firestore = self.db.db if self.db else None
        self.role_messages = self.firestore.collection("role_messages") if self.firestore else None
        # Mapeo en memoria para mensajes de reacción: {message_id: [{"role_id": int, "emoji": str}]}
        self.reaction_role_messages: Dict[int, List[Dict[str, Any]]] = {}

    async def cog_load(self):
        """Al cargar el cog, re-registra vistas persistentes desde Firestore."""
        if not self.role_messages:
            return
        try:
            for doc in self.role_messages.stream():
                data = doc.to_dict()
                message_id = int(data.get("message_id"))
                roles_data = data.get("roles") or []
                # Guardar mapeo de reacciones en memoria
                self.reaction_role_messages[message_id] = [
                    {"role_id": int(entry.get("role_id")), "emoji": str(entry.get("emoji"))}
                    for entry in roles_data if entry.get("role_id") and entry.get("emoji")
                ]
        except Exception as e:
            print(f"❌ Error cargando mapeo de roles por reacción: {e}")

    @staticmethod
    def _parse_emoji_value(emoji_value: Optional[str]):
        if not emoji_value:
            return None
        try:
            pe = discord.PartialEmoji.from_str(str(emoji_value))
            return pe if pe.id is not None else (pe.name or str(emoji_value))
        except Exception:
            return str(emoji_value)

    @staticmethod
    def _emoji_matches(payload_emoji: discord.PartialEmoji, stored_emoji: str) -> bool:
        try:
            pe = discord.PartialEmoji.from_str(stored_emoji)
            if pe.id is not None and payload_emoji.id is not None:
                return pe.id == payload_emoji.id
            # Unicode
            return (pe.name or stored_emoji) == (payload_emoji.name or str(payload_emoji))
        except Exception:
            return str(payload_emoji) == stored_emoji

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # Ignorar bots
        if payload.user_id == (self.bot.user.id if self.bot.user else 0):
            return
        roles_cfg = self.reaction_role_messages.get(payload.message_id)
        if not roles_cfg:
            return
        guild = self.bot.get_guild(payload.guild_id) if payload.guild_id else None
        if guild is None:
            return
        member = guild.get_member(payload.user_id)
        if member is None or member.bot:
            return
        matched_role_id = None
        for entry in roles_cfg:
            if self._emoji_matches(payload.emoji, str(entry.get("emoji"))):
                matched_role_id = int(entry.get("role_id"))
                break
        if not matched_role_id:
            return
        role = guild.get_role(matched_role_id)
        if role is None:
            return
        me = guild.me
        if me is None or not me.guild_permissions.manage_roles or role >= me.top_role:
            return
        if role in member.roles:
            return
        try:
            await member.add_roles(role, reason=f"Self-assign via reaction (msg {payload.message_id})")
        except Exception:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        roles_cfg = self.reaction_role_messages.get(payload.message_id)
        if not roles_cfg or not payload.guild_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        member = guild.get_member(payload.user_id)
        if member is None or member.bot:
            return
        matched_role_id = None
        for entry in roles_cfg:
            if self._emoji_matches(payload.emoji, str(entry.get("emoji"))):
                matched_role_id = int(entry.get("role_id"))
                break
        if not matched_role_id:
            return
        role = guild.get_role(matched_role_id)
        if role is None:
            return
        me = guild.me
        if me is None or not me.guild_permissions.manage_roles or role >= me.top_role:
            return
        if role not in member.roles:
            return
        try:
            await member.remove_roles(role, reason=f"Self-assign via reaction removal (msg {payload.message_id})")
        except Exception:
            return

    @app_commands.command(name="role", description="Crea un mensaje con reacciones para auto-asignar/quitar roles (estilo Discord)")
    @app_commands.describe(
        canal="Canal donde se publicará el mensaje",
        texto="Texto del mensaje (opcional)",
        rol1="Rol 1 (obligatorio)",
        rol2="Rol 2 (opcional)",
        rol3="Rol 3 (opcional)",
        rol4="Rol 4 (opcional)",
        rol5="Rol 5 (opcional)",
        emoji1="Emoji para Rol 1 (opcional)",
        emoji2="Emoji para Rol 2 (opcional)",
        emoji3="Emoji para Rol 3 (opcional)",
        emoji4="Emoji para Rol 4 (opcional)",
        emoji5="Emoji para Rol 5 (opcional)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def crear_mensaje_rol(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        texto: str = "Pulsa los botones para obtener/quitar el rol",
        rol1: discord.Role = None,
        rol2: Optional[discord.Role] = None,
        rol3: Optional[discord.Role] = None,
        rol4: Optional[discord.Role] = None,
        rol5: Optional[discord.Role] = None,
        emoji1: Optional[str] = None,
        emoji2: Optional[str] = None,
        emoji3: Optional[str] = None,
        emoji4: Optional[str] = None,
        emoji5: Optional[str] = None,
    ):
        # Validaciones básicas
        if not interaction.guild:
            await interaction.response.send_message("Este comando solo puede usarse en servidores.", ephemeral=True)
            return

        me = interaction.guild.me
        if me is None or not me.guild_permissions.manage_roles:
            await interaction.response.send_message("No tengo permisos de gestionar roles.", ephemeral=True)
            return

        # Construir lista de roles
        roles: List[discord.Role] = [r for r in [rol1, rol2, rol3, rol4, rol5] if r is not None]
        # Validaciones
        if not roles:
            await interaction.response.send_message("Debes especificar al menos un rol.", ephemeral=True)
            return
        # Duplicados
        seen = set()
        unique_roles: List[discord.Role] = []
        for r in roles:
            if r.id not in seen:
                unique_roles.append(r)
                seen.add(r.id)
        roles = unique_roles

        # Jerarquía de roles para todos
        top_role = interaction.guild.me.top_role
        invalid = [r for r in roles if r >= top_role]
        if invalid:
            names = ", ".join(r.mention for r in invalid)
            await interaction.response.send_message(f"No puedo gestionar estos roles por jerarquía: {names}", ephemeral=True)
            return

        try:
            # 1) Enviar el mensaje
            sent_msg = await canal.send(texto)
            per_role_emojis: List[Optional[str]] = [emoji1, emoji2, emoji3, emoji4, emoji5]
            role_emoji_pairs: List[tuple[discord.Role, str]] = []
            for idx, role in enumerate(roles):
                chosen_emoji = per_role_emojis[idx] if idx < len(per_role_emojis) else None
                if not chosen_emoji:
                    await interaction.response.send_message(
                        f"Debes especificar un emoji para el rol {role.mention} (usa emoji{idx+1}).",
                        ephemeral=True,
                    )
                    return
                role_emoji_pairs.append((role, chosen_emoji))
                # Añadir reacción
                parsed = self._parse_emoji_value(chosen_emoji)
                if parsed:
                    try:
                        await sent_msg.add_reaction(parsed)
                    except Exception:
                        pass

            # 2) Guardar en Firestore para reactivar al reiniciar
            if self.role_messages is not None:
                doc_id = f"{interaction.guild.id}-{sent_msg.id}"
                self.role_messages.document(doc_id).set({
                    "guild_id": interaction.guild.id,
                    "channel_id": canal.id,
                    "message_id": sent_msg.id,
                    "roles": [{"role_id": r.id, "emoji": e} for r, e in role_emoji_pairs],
                    "created_by": interaction.user.id,
                })

            # 3) Guardar en memoria el mapeo para los listeners
            self.reaction_role_messages[sent_msg.id] = [
                {"role_id": r.id, "emoji": e} for r, e in role_emoji_pairs
            ]

            await interaction.response.send_message(
                f"Mensaje creado en {canal.mention}.",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message("No tengo permisos para enviar mensajes en ese canal.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ocurrió un error: {e}", ephemeral=True)

    @app_commands.command(name="role_migrar", description="Convierte un mensaje antiguo de botones a reacciones (mantiene roles/emoji)")
    @app_commands.describe(
        canal="Canal donde está el mensaje",
        message_id="ID del mensaje original"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def migrar_mensaje_roles(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        message_id: str,
    ):
        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.response.send_message("ID de mensaje inválido.", ephemeral=True)
            return

        # Buscar documento en Firestore
        doc_id = f"{interaction.guild.id}-{msg_id}"
        doc = self.role_messages.document(doc_id).get() if self.role_messages else None
        if not doc or not doc.exists:
            await interaction.response.send_message("No encontré configuración guardada para ese mensaje.", ephemeral=True)
            return

        data = doc.to_dict()
        roles_data = data.get("roles") or []
        if not roles_data:
            await interaction.response.send_message("No hay roles configurados para ese mensaje.", ephemeral=True)
            return

        # Obtener el mensaje
        try:
            message = await canal.fetch_message(msg_id)
        except Exception:
            await interaction.response.send_message("No pude obtener el mensaje. Revisa canal e ID.", ephemeral=True)
            return

        # Quitar vista si la tiene (migración desde botones)
        try:
            await message.edit(view=None)
        except Exception:
            pass

        # Añadir reacciones
        added = 0
        for entry in roles_data:
            emoji_val = entry.get("emoji")
            parsed = self._parse_emoji_value(emoji_val)
            if parsed:
                try:
                    await message.add_reaction(parsed)
                    added += 1
                except Exception:
                    continue

        # Registrar en memoria para listeners
        self.reaction_role_messages[msg_id] = [
            {"role_id": int(e.get("role_id")), "emoji": str(e.get("emoji"))}
            for e in roles_data if e.get("role_id") and e.get("emoji")
        ]

        await interaction.response.send_message(
            f"Migración completada. Se añadieron {added} reacciones.", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleAssigner(bot))


