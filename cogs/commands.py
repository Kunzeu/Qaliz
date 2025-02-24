<<<<<<< HEAD
from typing import Optional, Dict, Any, List, Set
from datetime import datetime
import discord
from discord.ext import commands

class GuildConfig:
    def __init__(self, guild_id: int, admin_roles: List[int] = None, mod_roles: List[int] = None):
        self.guild_id = guild_id
        self.admin_roles = admin_roles or []
        self.mod_roles = mod_roles or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "guild_id": self.guild_id,
            "admin_roles": self.admin_roles,
            "mod_roles": self.mod_roles
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GuildConfig':
        return cls(
            guild_id=data["guild_id"],
            admin_roles=data.get("admin_roles", []),
            mod_roles=data.get("mod_roles", [])
        )

class CustomCommand:
    def __init__(self, name: str, response: str, guild_id: int, created_by: int):
        self.name = name.lower()
        self.response = response
        self.guild_id = guild_id
        self.created_by = created_by
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
        self.aliases: Set[str] = set()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "response": self.response,
            "guild_id": self.guild_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "aliases": list(self.aliases)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomCommand':
        cmd = cls(
            name=data["name"],
            response=data["response"],
            guild_id=data["guild_id"],
            created_by=data["created_by"]
        )
        cmd.created_at = datetime.fromisoformat(data["created_at"])
        cmd.last_modified = datetime.fromisoformat(data["last_modified"])
        cmd.aliases = set(data.get("aliases", []))
        return cmd

class CommandManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db.db  # Acceder a la instancia de Firestore
        # Colecciones de Firestore
        self.commands_collection = self.db.collection('commands')
        self.guild_configs_collection = self.db.collection('guild_configs')
        # Cache en memoria
        self.guild_commands = {}  # {guild_id: {command_name: Command}}
        self.guild_aliases = {}   # {guild_id: {alias: command_name}}
        self.guild_configs = {}   # {guild_id: GuildConfig}
        # Cargar datos al iniciar
        self._load_data()
    
    def _load_data(self):
        """Carga comandos y configuraciones desde Firestore"""
        try:
            # Cargar configuraciones de servidor
            configs = self.guild_configs_collection.stream()
            for config_doc in configs:
                config_data = config_doc.to_dict()
                config = GuildConfig.from_dict(config_data)
                self.guild_configs[config.guild_id] = config
            
            # Cargar comandos y alias
            commands = self.commands_collection.stream()
            for cmd_doc in commands:
                cmd_data = cmd_doc.to_dict()
                command = CustomCommand.from_dict(cmd_data)
                guild_id = command.guild_id
                
                # Inicializar diccionarios si no existen
                if guild_id not in self.guild_commands:
                    self.guild_commands[guild_id] = {}
                if guild_id not in self.guild_aliases:
                    self.guild_aliases[guild_id] = {}
                
                # Agregar comando y sus alias
                self.guild_commands[guild_id][command.name] = command
                for alias in command.aliases:
                    self.guild_aliases[guild_id][alias] = command.name
                    
            print("✅ Comandos y configuraciones cargados exitosamente")
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")

    def has_permission(self, member: discord.Member) -> bool:
        """Verifica si el miembro tiene rol de admin o mod en su servidor"""
        guild_id = member.guild.id
        if guild_id not in self.guild_configs:
            return member.guild_permissions.administrator
        
        config = self.guild_configs[guild_id]
        member_role_ids = {role.id for role in member.roles}
        
        is_admin = any(role_id in member_role_ids for role_id in config.admin_roles)
        is_mod = any(role_id in member_role_ids for role_id in config.mod_roles)
        
        return is_admin or is_mod or member.guild_permissions.administrator

    @commands.command(name='configurar_roles', aliases=['croles'])
    @commands.has_permissions(administrator=True)
    async def configure_roles(self, ctx, role_type: str, *, role_mentions: str):
        """Configura roles de admin/mod para el servidor"""
        guild_id = ctx.guild.id
        
        role_ids = [role.id for role in ctx.message.role_mentions]
        
        if not role_ids:
            await ctx.send("❌ Debes mencionar al menos un rol.")
            return
        
        if guild_id not in self.guild_configs:
            self.guild_configs[guild_id] = GuildConfig(guild_id)
        
        config = self.guild_configs[guild_id]
        
        if role_type.lower() == 'admin':
            config.admin_roles = role_ids
            role_type_str = "administrador"
        elif role_type.lower() == 'mod':
            config.mod_roles = role_ids
            role_type_str = "moderador"
        else:
            await ctx.send("❌ El tipo de rol debe ser 'admin' o 'mod'.")
            return
        
        # Guardar en Firestore
        try:
            self.guild_configs_collection.document(str(guild_id)).set(config.to_dict())
            roles_str = ", ".join(f"<@&{role_id}>" for role_id in role_ids)
            await ctx.send(f"✅ Roles de {role_type_str} actualizados: {roles_str}")
        except Exception as e:
            await ctx.send("❌ Error al guardar la configuración.")
            print(f"Error guardando configuración: {e}")
            
    def _normalize_name(self, name: str) -> str:
        """Normaliza el nombre del comando o alias a minúsculas"""
        return name[1:].lower() if name.startswith('.') else name.lower()

    @commands.command(name='crear', aliases=['cmd'])
    async def create_command(self, ctx, name: str, *, response: str):
        """Crea un nuevo comando personalizado"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para crear comandos.")
            return

        guild_id = ctx.guild.id
        name = self._normalize_name(name)
        
        # Inicializar diccionarios del servidor si no existen
        if guild_id not in self.guild_commands:
            self.guild_commands[guild_id] = {}
        if guild_id not in self.guild_aliases:
            self.guild_aliases[guild_id] = {}
            
        # Verificar si el comando o alias ya existe
        if (name in self.guild_commands[guild_id] or 
            name in self.guild_aliases[guild_id]):
            await ctx.send(f"❌ El comando o alias `.{name}` ya existe.")
            return

        try:
            # Crear comando
            command = CustomCommand(name, response, guild_id, ctx.author.id)
            
            # Guardar en memoria
            self.guild_commands[guild_id][name] = command
            
            # Guardar en Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{name}")
            cmd_doc_ref.set(command.to_dict())
            
            await ctx.send(f"✅ Comando `.{name}` creado exitosamente.")
        except Exception as e:
            await ctx.send("❌ Error al crear el comando.")
            print(f"Error creando comando: {e}")

    @commands.command(name='editar')
    async def edit_command(self, ctx, name: str, *, new_response: str):
        """Edita un comando existente"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para editar comandos.")
            return

        guild_id = ctx.guild.id
        name = self._normalize_name(name)

        if guild_id not in self.guild_commands or name not in self.guild_commands[guild_id]:
            await ctx.send(f"❌ El comando `.{name}` no existe.")
            return

        try:
            # Actualizar comando en memoria
            command = self.guild_commands[guild_id][name]
            command.response = new_response
            command.last_modified = datetime.now()

            # Actualizar en Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{name}")
            cmd_doc_ref.update({
                "response": new_response,
                "last_modified": command.last_modified.isoformat()
            })

            await ctx.send(f"✅ Comando `.{name}` actualizado exitosamente.")
        except Exception as e:
            await ctx.send("❌ Error al actualizar el comando.")
            print(f"Error actualizando comando: {e}")

    @commands.command(name='eliminar')
    async def delete_command(self, ctx, name: str):
        """Elimina un comando existente"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para eliminar comandos.")
            return

        guild_id = ctx.guild.id
        name = name[1:] if name.startswith('.') else name

        if guild_id not in self.guild_commands or name not in self.guild_commands[guild_id]:
            await ctx.send(f"❌ El comando `.{name}` no existe.")
            return

        try:
            # Eliminar de Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{name}")
            cmd_doc_ref.delete()

            # Eliminar de memoria
            command = self.guild_commands[guild_id].pop(name)
            # Eliminar aliases asociados
            self.guild_aliases[guild_id] = {
                alias: cmd_name 
                for alias, cmd_name in self.guild_aliases[guild_id].items() 
                if cmd_name != name
            }

            await ctx.send(f"✅ Comando `.{name}` eliminado exitosamente.")
        except Exception as e:
            await ctx.send("❌ Error al eliminar el comando.")
            print(f"Error eliminando comando: {e}")

    @commands.command(name='alias')
    async def add_alias(self, ctx, command_name: str, alias: str):
        """Añade un alias a un comando existente"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para crear aliases.")
            return

        guild_id = ctx.guild.id
        command_name = self._normalize_name(command_name)
        alias = self._normalize_name(alias)

        # Verificar que el comando existe
        if guild_id not in self.guild_commands or command_name not in self.guild_commands[guild_id]:
            await ctx.send(f"❌ El comando `.{command_name}` no existe.")
            return

        # Verificar que el alias no existe ya como comando o como alias
        if guild_id in self.guild_commands and alias in self.guild_commands[guild_id]:
            await ctx.send(f"❌ Ya existe un comando llamado `.{alias}`.")
            return

        if guild_id in self.guild_aliases and alias in self.guild_aliases[guild_id]:
            await ctx.send(f"❌ El alias `.{alias}` ya está en uso.")
            return

        try:
            # Añadir alias al comando
            command = self.guild_commands[guild_id][command_name]
            command.aliases.add(alias)
            command.last_modified = datetime.now()

            # Actualizar en memoria
            if guild_id not in self.guild_aliases:
                self.guild_aliases[guild_id] = {}
            self.guild_aliases[guild_id][alias] = command_name

            # Actualizar en Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{command_name}")
            cmd_doc_ref.update({
                "aliases": list(command.aliases),
                "last_modified": command.last_modified.isoformat()
            })

            await ctx.send(f"✅ Alias `.{alias}` creado para el comando `.{command_name}`.")
        except Exception as e:
            await ctx.send("❌ Error al crear el alias.")
            print(f"Error creando alias: {e}")

    @commands.command(name='quitar_alias')
    async def remove_alias(self, ctx, alias: str):
        """Elimina un alias existente"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para eliminar aliases.")
            return

        guild_id = ctx.guild.id
        alias = self._normalize_name(alias)
        
        if guild_id not in self.guild_aliases or alias not in self.guild_aliases[guild_id]:
            await ctx.send(f"❌ El alias `.{alias}` no existe.")
            return

        try:
            # Obtener el comando original
            command_name = self.guild_aliases[guild_id][alias]
            command = self.guild_commands[guild_id][command_name]
            
            # Eliminar alias
            command.aliases.remove(alias)
            del self.guild_aliases[guild_id][alias]
            command.last_modified = datetime.now()

            # Actualizar en Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{command_name}")
            cmd_doc_ref.update({
                "aliases": list(command.aliases),
                "last_modified": command.last_modified.isoformat()
            })

            await ctx.send(f"✅ Alias `.{alias}` eliminado exitosamente.")
        except Exception as e:
            await ctx.send("❌ Error al eliminar el alias.")
            print(f"Error eliminando alias: {e}")

    @commands.command(name='lista')
    async def list_aliases(self, ctx, command_name: Optional[str] = None):
        """Lista los aliases de un comando o todos los aliases del servidor"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.guild_aliases or not self.guild_aliases[guild_id]:
            await ctx.send("❌ No hay aliases configurados en este servidor.")
            return

        if command_name:
            # Limpiar el nombre del comando si viene con punto
            command_name = command_name[1:] if command_name.startswith('.') else command_name
            
            # Verificar que el comando existe
            if command_name not in self.guild_commands[guild_id]:
                await ctx.send(f"❌ El comando `.{command_name}` no existe.")
                return
            
            # Obtener aliases del comando específico
            command = self.guild_commands[guild_id][command_name]
            if not command.aliases:
                await ctx.send(f"❌ El comando `.{command_name}` no tiene aliases.")
                return
            
            aliases_list = ", ".join(f"`.{alias}`" for alias in sorted(command.aliases))
            await ctx.send(f"Aliases para el comando `.{command_name}`:\n{aliases_list}")
        else:
            # Mostrar todos los aliases organizados por comando
            embed = discord.Embed(
                title="Aliases del Servidor",
                color=discord.Color.blue(),
                description="Lista de todos los aliases configurados"
            )
            
            # Organizar aliases por comando
            commands_with_aliases = {}
            for alias, cmd_name in self.guild_aliases[guild_id].items():
                if cmd_name not in commands_with_aliases:
                    commands_with_aliases[cmd_name] = []
                commands_with_aliases[cmd_name].append(alias)
            
            # Añadir cada comando y sus aliases al embed
            for cmd_name, aliases in sorted(commands_with_aliases.items()):
                aliases_str = ", ".join(f"`.{alias}`" for alias in sorted(aliases))
                embed.add_field(
                    name=f"Comando `.{cmd_name}`",
                    value=aliases_str,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
    @commands.command(name='comandos')
    async def list_commands(self, ctx):
        """Lista todos los comandos personalizados del servidor"""
        guild_id = ctx.guild.id
    
        if guild_id not in self.guild_commands or not self.guild_commands[guild_id]:
            await ctx.send("❌ No hay comandos personalizados configurados en este servidor.")
            return    
        # Crear un embed para mostrar los comandos
        embed = discord.Embed(
            title="Comandos Personalizados del Servidor",
            color=discord.Color.green(),
            description="Lista de todos los comandos configurados"
        )
        for name, command in sorted(self.guild_commands[guild_id].items()):
            aliases = ", ".join(f"`.{alias}`" for alias in sorted(command.aliases))
            embed.add_field(
                name=f"Comando `.{name}`",
                value=f"**Respuesta:** {command.response}\n**Aliases:** {aliases if aliases else 'Ninguno'}",
                inline=False
            )
            
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Detecta y ejecuta comandos personalizados"""
        if message.author.bot or not message.content.startswith('.'):
            return

        guild_id = message.guild.id
        if guild_id not in self.guild_commands:
            return

        command_name = self._normalize_name(message.content.split()[0])
        
        # Buscar comando directo o alias
        if command_name in self.guild_commands[guild_id]:
            await message.channel.send(self.guild_commands[guild_id][command_name].response)
        elif command_name in self.guild_aliases[guild_id]:
            original_name = self.guild_aliases[guild_id][command_name]
            await message.channel.send(self.guild_commands[guild_id][original_name].response)

async def setup(bot):
=======
<<<<<<< HEAD
from typing import Optional, Dict, Any, List, Set
from datetime import datetime
import discord
from discord.ext import commands

class GuildConfig:
    def __init__(self, guild_id: int, admin_roles: List[int] = None, mod_roles: List[int] = None):
        self.guild_id = guild_id
        self.admin_roles = admin_roles or []
        self.mod_roles = mod_roles or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "guild_id": self.guild_id,
            "admin_roles": self.admin_roles,
            "mod_roles": self.mod_roles
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GuildConfig':
        return cls(
            guild_id=data["guild_id"],
            admin_roles=data.get("admin_roles", []),
            mod_roles=data.get("mod_roles", [])
        )

class CustomCommand:
    def __init__(self, name: str, response: str, guild_id: int, created_by: int):
        self.name = name.lower()
        self.response = response
        self.guild_id = guild_id
        self.created_by = created_by
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
        self.aliases: Set[str] = set()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "response": self.response,
            "guild_id": self.guild_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "aliases": list(self.aliases)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomCommand':
        cmd = cls(
            name=data["name"],
            response=data["response"],
            guild_id=data["guild_id"],
            created_by=data["created_by"]
        )
        cmd.created_at = datetime.fromisoformat(data["created_at"])
        cmd.last_modified = datetime.fromisoformat(data["last_modified"])
        cmd.aliases = set(data.get("aliases", []))
        return cmd

class CommandManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db.db  # Acceder a la instancia de Firestore
        # Colecciones de Firestore
        self.commands_collection = self.db.collection('commands')
        self.guild_configs_collection = self.db.collection('guild_configs')
        # Cache en memoria
        self.guild_commands = {}  # {guild_id: {command_name: Command}}
        self.guild_aliases = {}   # {guild_id: {alias: command_name}}
        self.guild_configs = {}   # {guild_id: GuildConfig}
        # Cargar datos al iniciar
        self._load_data()
    
    def _load_data(self):
        """Carga comandos y configuraciones desde Firestore"""
        try:
            # Cargar configuraciones de servidor
            configs = self.guild_configs_collection.stream()
            for config_doc in configs:
                config_data = config_doc.to_dict()
                config = GuildConfig.from_dict(config_data)
                self.guild_configs[config.guild_id] = config
            
            # Cargar comandos y alias
            commands = self.commands_collection.stream()
            for cmd_doc in commands:
                cmd_data = cmd_doc.to_dict()
                command = CustomCommand.from_dict(cmd_data)
                guild_id = command.guild_id
                
                # Inicializar diccionarios si no existen
                if guild_id not in self.guild_commands:
                    self.guild_commands[guild_id] = {}
                if guild_id not in self.guild_aliases:
                    self.guild_aliases[guild_id] = {}
                
                # Agregar comando y sus alias
                self.guild_commands[guild_id][command.name] = command
                for alias in command.aliases:
                    self.guild_aliases[guild_id][alias] = command.name
                    
            print("✅ Comandos y configuraciones cargados exitosamente")
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")

    def has_permission(self, member: discord.Member) -> bool:
        """Verifica si el miembro tiene rol de admin o mod en su servidor"""
        guild_id = member.guild.id
        if guild_id not in self.guild_configs:
            return member.guild_permissions.administrator
        
        config = self.guild_configs[guild_id]
        member_role_ids = {role.id for role in member.roles}
        
        is_admin = any(role_id in member_role_ids for role_id in config.admin_roles)
        is_mod = any(role_id in member_role_ids for role_id in config.mod_roles)
        
        return is_admin or is_mod or member.guild_permissions.administrator

    @commands.command(name='configurar_roles', aliases=['croles'])
    @commands.has_permissions(administrator=True)
    async def configure_roles(self, ctx, role_type: str, *, role_mentions: str):
        """Configura roles de admin/mod para el servidor"""
        guild_id = ctx.guild.id
        
        role_ids = [role.id for role in ctx.message.role_mentions]
        
        if not role_ids:
            await ctx.send("❌ Debes mencionar al menos un rol.")
            return
        
        if guild_id not in self.guild_configs:
            self.guild_configs[guild_id] = GuildConfig(guild_id)
        
        config = self.guild_configs[guild_id]
        
        if role_type.lower() == 'admin':
            config.admin_roles = role_ids
            role_type_str = "administrador"
        elif role_type.lower() == 'mod':
            config.mod_roles = role_ids
            role_type_str = "moderador"
        else:
            await ctx.send("❌ El tipo de rol debe ser 'admin' o 'mod'.")
            return
        
        # Guardar en Firestore
        try:
            self.guild_configs_collection.document(str(guild_id)).set(config.to_dict())
            roles_str = ", ".join(f"<@&{role_id}>" for role_id in role_ids)
            await ctx.send(f"✅ Roles de {role_type_str} actualizados: {roles_str}")
        except Exception as e:
            await ctx.send("❌ Error al guardar la configuración.")
            print(f"Error guardando configuración: {e}")
            
    def _normalize_name(self, name: str) -> str:
        """Normaliza el nombre del comando o alias a minúsculas"""
        return name[1:].lower() if name.startswith('.') else name.lower()

    @commands.command(name='crear', aliases=['cmd'])
    async def create_command(self, ctx, name: str, *, response: str):
        """Crea un nuevo comando personalizado"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para crear comandos.")
            return

        guild_id = ctx.guild.id
        name = self._normalize_name(name)
        
        # Inicializar diccionarios del servidor si no existen
        if guild_id not in self.guild_commands:
            self.guild_commands[guild_id] = {}
        if guild_id not in self.guild_aliases:
            self.guild_aliases[guild_id] = {}
            
        # Verificar si el comando o alias ya existe
        if (name in self.guild_commands[guild_id] or 
            name in self.guild_aliases[guild_id]):
            await ctx.send(f"❌ El comando o alias `.{name}` ya existe.")
            return

        try:
            # Crear comando
            command = CustomCommand(name, response, guild_id, ctx.author.id)
            
            # Guardar en memoria
            self.guild_commands[guild_id][name] = command
            
            # Guardar en Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{name}")
            cmd_doc_ref.set(command.to_dict())
            
            await ctx.send(f"✅ Comando `.{name}` creado exitosamente.")
        except Exception as e:
            await ctx.send("❌ Error al crear el comando.")
            print(f"Error creando comando: {e}")

    @commands.command(name='editar')
    async def edit_command(self, ctx, name: str, *, new_response: str):
        """Edita un comando existente"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para editar comandos.")
            return

        guild_id = ctx.guild.id
        name = self._normalize_name(name)

        if guild_id not in self.guild_commands or name not in self.guild_commands[guild_id]:
            await ctx.send(f"❌ El comando `.{name}` no existe.")
            return

        try:
            # Actualizar comando en memoria
            command = self.guild_commands[guild_id][name]
            command.response = new_response
            command.last_modified = datetime.now()

            # Actualizar en Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{name}")
            cmd_doc_ref.update({
                "response": new_response,
                "last_modified": command.last_modified.isoformat()
            })

            await ctx.send(f"✅ Comando `.{name}` actualizado exitosamente.")
        except Exception as e:
            await ctx.send("❌ Error al actualizar el comando.")
            print(f"Error actualizando comando: {e}")

    @commands.command(name='eliminar')
    async def delete_command(self, ctx, name: str):
        """Elimina un comando existente"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para eliminar comandos.")
            return

        guild_id = ctx.guild.id
        name = name[1:] if name.startswith('.') else name

        if guild_id not in self.guild_commands or name not in self.guild_commands[guild_id]:
            await ctx.send(f"❌ El comando `.{name}` no existe.")
            return

        try:
            # Eliminar de Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{name}")
            cmd_doc_ref.delete()

            # Eliminar de memoria
            command = self.guild_commands[guild_id].pop(name)
            # Eliminar aliases asociados
            self.guild_aliases[guild_id] = {
                alias: cmd_name 
                for alias, cmd_name in self.guild_aliases[guild_id].items() 
                if cmd_name != name
            }

            await ctx.send(f"✅ Comando `.{name}` eliminado exitosamente.")
        except Exception as e:
            await ctx.send("❌ Error al eliminar el comando.")
            print(f"Error eliminando comando: {e}")

    @commands.command(name='alias')
    async def add_alias(self, ctx, command_name: str, alias: str):
        """Añade un alias a un comando existente"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para crear aliases.")
            return

        guild_id = ctx.guild.id
        command_name = self._normalize_name(command_name)
        alias = self._normalize_name(alias)

        # Verificar que el comando existe
        if guild_id not in self.guild_commands or command_name not in self.guild_commands[guild_id]:
            await ctx.send(f"❌ El comando `.{command_name}` no existe.")
            return

        # Verificar que el alias no existe ya como comando o como alias
        if guild_id in self.guild_commands and alias in self.guild_commands[guild_id]:
            await ctx.send(f"❌ Ya existe un comando llamado `.{alias}`.")
            return

        if guild_id in self.guild_aliases and alias in self.guild_aliases[guild_id]:
            await ctx.send(f"❌ El alias `.{alias}` ya está en uso.")
            return

        try:
            # Añadir alias al comando
            command = self.guild_commands[guild_id][command_name]
            command.aliases.add(alias)
            command.last_modified = datetime.now()

            # Actualizar en memoria
            if guild_id not in self.guild_aliases:
                self.guild_aliases[guild_id] = {}
            self.guild_aliases[guild_id][alias] = command_name

            # Actualizar en Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{command_name}")
            cmd_doc_ref.update({
                "aliases": list(command.aliases),
                "last_modified": command.last_modified.isoformat()
            })

            await ctx.send(f"✅ Alias `.{alias}` creado para el comando `.{command_name}`.")
        except Exception as e:
            await ctx.send("❌ Error al crear el alias.")
            print(f"Error creando alias: {e}")

    @commands.command(name='quitar_alias')
    async def remove_alias(self, ctx, alias: str):
        """Elimina un alias existente"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para eliminar aliases.")
            return

        guild_id = ctx.guild.id
        alias = self._normalize_name(alias)
        
        if guild_id not in self.guild_aliases or alias not in self.guild_aliases[guild_id]:
            await ctx.send(f"❌ El alias `.{alias}` no existe.")
            return

        try:
            # Obtener el comando original
            command_name = self.guild_aliases[guild_id][alias]
            command = self.guild_commands[guild_id][command_name]
            
            # Eliminar alias
            command.aliases.remove(alias)
            del self.guild_aliases[guild_id][alias]
            command.last_modified = datetime.now()

            # Actualizar en Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{command_name}")
            cmd_doc_ref.update({
                "aliases": list(command.aliases),
                "last_modified": command.last_modified.isoformat()
            })

            await ctx.send(f"✅ Alias `.{alias}` eliminado exitosamente.")
        except Exception as e:
            await ctx.send("❌ Error al eliminar el alias.")
            print(f"Error eliminando alias: {e}")

    @commands.command(name='lista')
    async def list_aliases(self, ctx, command_name: Optional[str] = None):
        """Lista los aliases de un comando o todos los aliases del servidor"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.guild_aliases or not self.guild_aliases[guild_id]:
            await ctx.send("❌ No hay aliases configurados en este servidor.")
            return

        if command_name:
            # Limpiar el nombre del comando si viene con punto
            command_name = command_name[1:] if command_name.startswith('.') else command_name
            
            # Verificar que el comando existe
            if command_name not in self.guild_commands[guild_id]:
                await ctx.send(f"❌ El comando `.{command_name}` no existe.")
                return
            
            # Obtener aliases del comando específico
            command = self.guild_commands[guild_id][command_name]
            if not command.aliases:
                await ctx.send(f"❌ El comando `.{command_name}` no tiene aliases.")
                return
            
            aliases_list = ", ".join(f"`.{alias}`" for alias in sorted(command.aliases))
            await ctx.send(f"Aliases para el comando `.{command_name}`:\n{aliases_list}")
        else:
            # Mostrar todos los aliases organizados por comando
            embed = discord.Embed(
                title="Aliases del Servidor",
                color=discord.Color.blue(),
                description="Lista de todos los aliases configurados"
            )
            
            # Organizar aliases por comando
            commands_with_aliases = {}
            for alias, cmd_name in self.guild_aliases[guild_id].items():
                if cmd_name not in commands_with_aliases:
                    commands_with_aliases[cmd_name] = []
                commands_with_aliases[cmd_name].append(alias)
            
            # Añadir cada comando y sus aliases al embed
            for cmd_name, aliases in sorted(commands_with_aliases.items()):
                aliases_str = ", ".join(f"`.{alias}`" for alias in sorted(aliases))
                embed.add_field(
                    name=f"Comando `.{cmd_name}`",
                    value=aliases_str,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
    @commands.command(name='comandos')
    async def list_commands(self, ctx):
        """Lista todos los comandos personalizados del servidor"""
        guild_id = ctx.guild.id
    
        if guild_id not in self.guild_commands or not self.guild_commands[guild_id]:
            await ctx.send("❌ No hay comandos personalizados configurados en este servidor.")
            return    
        # Crear un embed para mostrar los comandos
        embed = discord.Embed(
            title="Comandos Personalizados del Servidor",
            color=discord.Color.green(),
            description="Lista de todos los comandos configurados"
        )
        for name, command in sorted(self.guild_commands[guild_id].items()):
            aliases = ", ".join(f"`.{alias}`" for alias in sorted(command.aliases))
            embed.add_field(
                name=f"Comando `.{name}`",
                value=f"**Respuesta:** {command.response}\n**Aliases:** {aliases if aliases else 'Ninguno'}",
                inline=False
            )
            
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Detecta y ejecuta comandos personalizados"""
        if message.author.bot or not message.content.startswith('.'):
            return

        guild_id = message.guild.id
        if guild_id not in self.guild_commands:
            return

        command_name = self._normalize_name(message.content.split()[0])
        
        # Buscar comando directo o alias
        if command_name in self.guild_commands[guild_id]:
            await message.channel.send(self.guild_commands[guild_id][command_name].response)
        elif command_name in self.guild_aliases[guild_id]:
            original_name = self.guild_aliases[guild_id][command_name]
            await message.channel.send(self.guild_commands[guild_id][original_name].response)

async def setup(bot):
=======
from typing import Optional, Dict, Any, List, Set
from datetime import datetime
import discord
from discord.ext import commands

class GuildConfig:
    def __init__(self, guild_id: int, admin_roles: List[int] = None, mod_roles: List[int] = None):
        self.guild_id = guild_id
        self.admin_roles = admin_roles or []
        self.mod_roles = mod_roles or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "guild_id": self.guild_id,
            "admin_roles": self.admin_roles,
            "mod_roles": self.mod_roles
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GuildConfig':
        return cls(
            guild_id=data["guild_id"],
            admin_roles=data.get("admin_roles", []),
            mod_roles=data.get("mod_roles", [])
        )

class CustomCommand:
    def __init__(self, name: str, response: str, guild_id: int, created_by: int):
        self.name = name.lower()
        self.response = response
        self.guild_id = guild_id
        self.created_by = created_by
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
        self.aliases: Set[str] = set()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "response": self.response,
            "guild_id": self.guild_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "aliases": list(self.aliases)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomCommand':
        cmd = cls(
            name=data["name"],
            response=data["response"],
            guild_id=data["guild_id"],
            created_by=data["created_by"]
        )
        cmd.created_at = datetime.fromisoformat(data["created_at"])
        cmd.last_modified = datetime.fromisoformat(data["last_modified"])
        cmd.aliases = set(data.get("aliases", []))
        return cmd

class CommandManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db.db  # Acceder a la instancia de Firestore
        # Colecciones de Firestore
        self.commands_collection = self.db.collection('commands')
        self.guild_configs_collection = self.db.collection('guild_configs')
        # Cache en memoria
        self.guild_commands = {}  # {guild_id: {command_name: Command}}
        self.guild_aliases = {}   # {guild_id: {alias: command_name}}
        self.guild_configs = {}   # {guild_id: GuildConfig}
        # Cargar datos al iniciar
        self._load_data()
    
    def _load_data(self):
        """Carga comandos y configuraciones desde Firestore"""
        try:
            # Cargar configuraciones de servidor
            configs = self.guild_configs_collection.stream()
            for config_doc in configs:
                config_data = config_doc.to_dict()
                config = GuildConfig.from_dict(config_data)
                self.guild_configs[config.guild_id] = config
            
            # Cargar comandos y alias
            commands = self.commands_collection.stream()
            for cmd_doc in commands:
                cmd_data = cmd_doc.to_dict()
                command = CustomCommand.from_dict(cmd_data)
                guild_id = command.guild_id
                
                # Inicializar diccionarios si no existen
                if guild_id not in self.guild_commands:
                    self.guild_commands[guild_id] = {}
                if guild_id not in self.guild_aliases:
                    self.guild_aliases[guild_id] = {}
                
                # Agregar comando y sus alias
                self.guild_commands[guild_id][command.name] = command
                for alias in command.aliases:
                    self.guild_aliases[guild_id][alias] = command.name
                    
            print("✅ Comandos y configuraciones cargados exitosamente")
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")

    def has_permission(self, member: discord.Member) -> bool:
        """Verifica si el miembro tiene rol de admin o mod en su servidor"""
        guild_id = member.guild.id
        if guild_id not in self.guild_configs:
            return member.guild_permissions.administrator
        
        config = self.guild_configs[guild_id]
        member_role_ids = {role.id for role in member.roles}
        
        is_admin = any(role_id in member_role_ids for role_id in config.admin_roles)
        is_mod = any(role_id in member_role_ids for role_id in config.mod_roles)
        
        return is_admin or is_mod or member.guild_permissions.administrator

    @commands.command(name='configurar_roles', aliases=['croles'])
    @commands.has_permissions(administrator=True)
    async def configure_roles(self, ctx, role_type: str, *, role_mentions: str):
        """Configura roles de admin/mod para el servidor"""
        guild_id = ctx.guild.id
        
        role_ids = [role.id for role in ctx.message.role_mentions]
        
        if not role_ids:
            await ctx.send("❌ Debes mencionar al menos un rol.")
            return
        
        if guild_id not in self.guild_configs:
            self.guild_configs[guild_id] = GuildConfig(guild_id)
        
        config = self.guild_configs[guild_id]
        
        if role_type.lower() == 'admin':
            config.admin_roles = role_ids
            role_type_str = "administrador"
        elif role_type.lower() == 'mod':
            config.mod_roles = role_ids
            role_type_str = "moderador"
        else:
            await ctx.send("❌ El tipo de rol debe ser 'admin' o 'mod'.")
            return
        
        # Guardar en Firestore
        try:
            self.guild_configs_collection.document(str(guild_id)).set(config.to_dict())
            roles_str = ", ".join(f"<@&{role_id}>" for role_id in role_ids)
            await ctx.send(f"✅ Roles de {role_type_str} actualizados: {roles_str}")
        except Exception as e:
            await ctx.send("❌ Error al guardar la configuración.")
            print(f"Error guardando configuración: {e}")
            
    def _normalize_name(self, name: str) -> str:
        """Normaliza el nombre del comando o alias a minúsculas"""
        return name[1:].lower() if name.startswith('.') else name.lower()

    @commands.command(name='crear', aliases=['cmd'])
    async def create_command(self, ctx, name: str, *, response: str):
        """Crea un nuevo comando personalizado"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para crear comandos.")
            return

        guild_id = ctx.guild.id
        name = self._normalize_name(name)
        
        # Inicializar diccionarios del servidor si no existen
        if guild_id not in self.guild_commands:
            self.guild_commands[guild_id] = {}
        if guild_id not in self.guild_aliases:
            self.guild_aliases[guild_id] = {}
            
        # Verificar si el comando o alias ya existe
        if (name in self.guild_commands[guild_id] or 
            name in self.guild_aliases[guild_id]):
            await ctx.send(f"❌ El comando o alias `.{name}` ya existe.")
            return

        try:
            # Crear comando
            command = CustomCommand(name, response, guild_id, ctx.author.id)
            
            # Guardar en memoria
            self.guild_commands[guild_id][name] = command
            
            # Guardar en Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{name}")
            cmd_doc_ref.set(command.to_dict())
            
            await ctx.send(f"✅ Comando `.{name}` creado exitosamente.")
        except Exception as e:
            await ctx.send("❌ Error al crear el comando.")
            print(f"Error creando comando: {e}")

    @commands.command(name='editar')
    async def edit_command(self, ctx, name: str, *, new_response: str):
        """Edita un comando existente"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para editar comandos.")
            return

        guild_id = ctx.guild.id
        name = self._normalize_name(name)

        if guild_id not in self.guild_commands or name not in self.guild_commands[guild_id]:
            await ctx.send(f"❌ El comando `.{name}` no existe.")
            return

        try:
            # Actualizar comando en memoria
            command = self.guild_commands[guild_id][name]
            command.response = new_response
            command.last_modified = datetime.now()

            # Actualizar en Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{name}")
            cmd_doc_ref.update({
                "response": new_response,
                "last_modified": command.last_modified.isoformat()
            })

            await ctx.send(f"✅ Comando `.{name}` actualizado exitosamente.")
        except Exception as e:
            await ctx.send("❌ Error al actualizar el comando.")
            print(f"Error actualizando comando: {e}")

    @commands.command(name='eliminar')
    async def delete_command(self, ctx, name: str):
        """Elimina un comando existente"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para eliminar comandos.")
            return

        guild_id = ctx.guild.id
        name = name[1:] if name.startswith('.') else name

        if guild_id not in self.guild_commands or name not in self.guild_commands[guild_id]:
            await ctx.send(f"❌ El comando `.{name}` no existe.")
            return

        try:
            # Eliminar de Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{name}")
            cmd_doc_ref.delete()

            # Eliminar de memoria
            command = self.guild_commands[guild_id].pop(name)
            # Eliminar aliases asociados
            self.guild_aliases[guild_id] = {
                alias: cmd_name 
                for alias, cmd_name in self.guild_aliases[guild_id].items() 
                if cmd_name != name
            }

            await ctx.send(f"✅ Comando `.{name}` eliminado exitosamente.")
        except Exception as e:
            await ctx.send("❌ Error al eliminar el comando.")
            print(f"Error eliminando comando: {e}")

    @commands.command(name='alias')
    async def add_alias(self, ctx, command_name: str, alias: str):
        """Añade un alias a un comando existente"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para crear aliases.")
            return

        guild_id = ctx.guild.id
        command_name = self._normalize_name(command_name)
        alias = self._normalize_name(alias)

        # Verificar que el comando existe
        if guild_id not in self.guild_commands or command_name not in self.guild_commands[guild_id]:
            await ctx.send(f"❌ El comando `.{command_name}` no existe.")
            return

        # Verificar que el alias no existe ya como comando o como alias
        if guild_id in self.guild_commands and alias in self.guild_commands[guild_id]:
            await ctx.send(f"❌ Ya existe un comando llamado `.{alias}`.")
            return

        if guild_id in self.guild_aliases and alias in self.guild_aliases[guild_id]:
            await ctx.send(f"❌ El alias `.{alias}` ya está en uso.")
            return

        try:
            # Añadir alias al comando
            command = self.guild_commands[guild_id][command_name]
            command.aliases.add(alias)
            command.last_modified = datetime.now()

            # Actualizar en memoria
            if guild_id not in self.guild_aliases:
                self.guild_aliases[guild_id] = {}
            self.guild_aliases[guild_id][alias] = command_name

            # Actualizar en Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{command_name}")
            cmd_doc_ref.update({
                "aliases": list(command.aliases),
                "last_modified": command.last_modified.isoformat()
            })

            await ctx.send(f"✅ Alias `.{alias}` creado para el comando `.{command_name}`.")
        except Exception as e:
            await ctx.send("❌ Error al crear el alias.")
            print(f"Error creando alias: {e}")

    @commands.command(name='quitar_alias')
    async def remove_alias(self, ctx, alias: str):
        """Elimina un alias existente"""
        if not self.has_permission(ctx.author):
            await ctx.send("❌ No tienes permisos para eliminar aliases.")
            return

        guild_id = ctx.guild.id
        alias = self._normalize_name(alias)
        
        if guild_id not in self.guild_aliases or alias not in self.guild_aliases[guild_id]:
            await ctx.send(f"❌ El alias `.{alias}` no existe.")
            return

        try:
            # Obtener el comando original
            command_name = self.guild_aliases[guild_id][alias]
            command = self.guild_commands[guild_id][command_name]
            
            # Eliminar alias
            command.aliases.remove(alias)
            del self.guild_aliases[guild_id][alias]
            command.last_modified = datetime.now()

            # Actualizar en Firestore
            cmd_doc_ref = self.commands_collection.document(f"{guild_id}_{command_name}")
            cmd_doc_ref.update({
                "aliases": list(command.aliases),
                "last_modified": command.last_modified.isoformat()
            })

            await ctx.send(f"✅ Alias `.{alias}` eliminado exitosamente.")
        except Exception as e:
            await ctx.send("❌ Error al eliminar el alias.")
            print(f"Error eliminando alias: {e}")

    @commands.command(name='lista')
    async def list_aliases(self, ctx, command_name: Optional[str] = None):
        """Lista los aliases de un comando o todos los aliases del servidor"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.guild_aliases or not self.guild_aliases[guild_id]:
            await ctx.send("❌ No hay aliases configurados en este servidor.")
            return

        if command_name:
            # Limpiar el nombre del comando si viene con punto
            command_name = command_name[1:] if command_name.startswith('.') else command_name
            
            # Verificar que el comando existe
            if command_name not in self.guild_commands[guild_id]:
                await ctx.send(f"❌ El comando `.{command_name}` no existe.")
                return
            
            # Obtener aliases del comando específico
            command = self.guild_commands[guild_id][command_name]
            if not command.aliases:
                await ctx.send(f"❌ El comando `.{command_name}` no tiene aliases.")
                return
            
            aliases_list = ", ".join(f"`.{alias}`" for alias in sorted(command.aliases))
            await ctx.send(f"Aliases para el comando `.{command_name}`:\n{aliases_list}")
        else:
            # Mostrar todos los aliases organizados por comando
            embed = discord.Embed(
                title="Aliases del Servidor",
                color=discord.Color.blue(),
                description="Lista de todos los aliases configurados"
            )
            
            # Organizar aliases por comando
            commands_with_aliases = {}
            for alias, cmd_name in self.guild_aliases[guild_id].items():
                if cmd_name not in commands_with_aliases:
                    commands_with_aliases[cmd_name] = []
                commands_with_aliases[cmd_name].append(alias)
            
            # Añadir cada comando y sus aliases al embed
            for cmd_name, aliases in sorted(commands_with_aliases.items()):
                aliases_str = ", ".join(f"`.{alias}`" for alias in sorted(aliases))
                embed.add_field(
                    name=f"Comando `.{cmd_name}`",
                    value=aliases_str,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
    @commands.command(name='comandos')
    async def list_commands(self, ctx):
        """Lista todos los comandos personalizados del servidor"""
        guild_id = ctx.guild.id
    
        if guild_id not in self.guild_commands or not self.guild_commands[guild_id]:
            await ctx.send("❌ No hay comandos personalizados configurados en este servidor.")
            return    
        # Crear un embed para mostrar los comandos
        embed = discord.Embed(
            title="Comandos Personalizados del Servidor",
            color=discord.Color.green(),
            description="Lista de todos los comandos configurados"
        )
        for name, command in sorted(self.guild_commands[guild_id].items()):
            aliases = ", ".join(f"`.{alias}`" for alias in sorted(command.aliases))
            embed.add_field(
                name=f"Comando `.{name}`",
                value=f"**Respuesta:** {command.response}\n**Aliases:** {aliases if aliases else 'Ninguno'}",
                inline=False
            )
            
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Detecta y ejecuta comandos personalizados"""
        if message.author.bot or not message.content.startswith('.'):
            return

        guild_id = message.guild.id
        if guild_id not in self.guild_commands:
            return

        command_name = self._normalize_name(message.content.split()[0])
        
        # Buscar comando directo o alias
        if command_name in self.guild_commands[guild_id]:
            await message.channel.send(self.guild_commands[guild_id][command_name].response)
        elif command_name in self.guild_aliases[guild_id]:
            original_name = self.guild_aliases[guild_id][command_name]
            await message.channel.send(self.guild_commands[guild_id][original_name].response)

async def setup(bot):
>>>>>>> d64e546 (Improved admin command)
>>>>>>> 95e1e84 (Improved admin command)
    await bot.add_cog(CommandManager(bot))