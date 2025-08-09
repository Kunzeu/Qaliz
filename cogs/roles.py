import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List


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

    async def cog_load(self):
        """Al cargar el cog, re-registra vistas persistentes desde Firestore."""
        if not self.role_messages:
            return
        try:
            for doc in self.role_messages.stream():
                data = doc.to_dict()
                guild_id = int(data.get("guild_id"))
                message_id = int(data.get("message_id"))
                roles_data = data.get("roles") or []

                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue

                view = RoleButtonsView(message_id=message_id)
                for entry in roles_data:
                    role_id = entry.get("role_id")
                    emoji = entry.get("emoji")
                    if not role_id:
                        continue
                    role_obj = guild.get_role(int(role_id))
                    if role_obj:
                        # Parsear emoji aquí para soportar custom y unicode
                        parsed_emoji = None
                        if emoji:
                            try:
                                pe = discord.PartialEmoji.from_str(str(emoji))
                                parsed_emoji = pe if pe.id is not None else (pe.name or str(emoji))
                            except Exception:
                                parsed_emoji = str(emoji)
                        view.add_role_button(role_obj, emoji=parsed_emoji)

                # Registrar vista persistente
                self.bot.add_view(view)
        except Exception as e:
            print(f"❌ Error registrando vistas persistentes de roles: {e}")

    @staticmethod
    def _parse_emoji_value(emoji_value: Optional[str]):
        if not emoji_value:
            return None
        try:
            pe = discord.PartialEmoji.from_str(str(emoji_value))
            return pe if pe.id is not None else (pe.name or str(emoji_value))
        except Exception:
            return str(emoji_value)

    @app_commands.command(name="role", description="Crea un mensaje con botones (solo emoji) para auto-asignar/quitar roles sin mensajes de respuesta")
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

            # 2) Crear la vista de botones con emoji por rol (sin label)
            view = RoleButtonsView(message_id=sent_msg.id)
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
                parsed = self._parse_emoji_value(chosen_emoji)
                view.add_role_button(role, emoji=parsed, row=(idx // 5))

            # 3) Publicar la vista
            await sent_msg.edit(view=view)
            self.bot.add_view(view)

            # 4) Guardar en Firestore para reactivar al reiniciar
            if self.role_messages is not None:
                doc_id = f"{interaction.guild.id}-{sent_msg.id}"
                self.role_messages.document(doc_id).set({
                    "guild_id": interaction.guild.id,
                    "channel_id": canal.id,
                    "message_id": sent_msg.id,
                    "roles": [{"role_id": r.id, "emoji": e} for r, e in role_emoji_pairs],
                    "created_by": interaction.user.id,
                })

            await interaction.response.send_message(
                f"Mensaje creado en {canal.mention}.",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message("No tengo permisos para enviar mensajes en ese canal.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ocurrió un error: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleAssigner(bot))


