print("   -> Importing os/datetime in database.py...")
import os
from datetime import datetime, timedelta

print("   -> Importing firebase_admin in database.py...")
import firebase_admin
from firebase_admin import credentials, firestore

print("   -> Importing dotenv/aiohttp in database.py...")
from dotenv import load_dotenv
import aiohttp

print("   -> Database imports successful!")

load_dotenv()

class DatabaseManager:
    def __init__(self):
        # Check if required Firebase environment variables are present
        required_vars = [
            'FIREBASE_TYPE', 'FIREBASE_PROJECT_ID', 'FIREBASE_PRIVATE_KEY_ID',
            'FIREBASE_PRIVATE_KEY', 'FIREBASE_CLIENT_EMAIL', 'FIREBASE_CLIENT_ID',
            'FIREBASE_AUTH_URI', 'FIREBASE_TOKEN_URI',
            'FIREBASE_AUTH_PROVIDER_X509_CERT_URL', 'FIREBASE_CLIENT_X509_CERT_URL',
            'FIREBASE_UNIVERSE_DOMAIN'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing Firebase environment variables: {', '.join(missing_vars)}")
            print("❌ Database initialization skipped. Set these variables in Render dashboard.")
            self.db = None
            self.apiKeys = None
            self.reminders = None
            self.blacklist = None
            self.roulettes = None
            self.events = None
            self.logAutoupload = None
            return
        
        firebase_config = {
            "type": os.getenv('FIREBASE_TYPE'),
            "project_id": os.getenv('FIREBASE_PROJECT_ID'),
            "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n') if os.getenv('FIREBASE_PRIVATE_KEY') else None,
            "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
            "client_id": os.getenv('FIREBASE_CLIENT_ID'),
            "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
            "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
            "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
            "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
            "universe_domain": os.getenv('FIREBASE_UNIVERSE_DOMAIN')
        }
        
        try:
            if not firebase_admin._apps:
                self.cred = credentials.Certificate(firebase_config)
                firebase_admin.initialize_app(self.cred)
            
            self.db = firestore.client()
            self.apiKeys = self.db.collection('api_keys')
            self.reminders = self.db.collection('reminders')
            self.blacklist = self.db.collection('blacklist')
            self.roulettes = self.db.collection('roulettes')
            self.events = self.db.collection('events')
            self.logAutoupload = self.db.collection('log_autoupload')
            print("✅ Firebase initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing Firebase: {e}")
            self.db = None
            self.apiKeys = None
            self.reminders = None
            self.blacklist = None
            self.roulettes = None
            self.events = None
            self.logAutoupload = None

    async def connect(self):
        if self.db is None:
            print('❌ Database not initialized (missing environment variables)')
            return False
        try:
            doc_ref = self.db.collection('test').document('ping')
            doc_ref.set({'message': 'ping'})
            print('✅ Conectado a Firebase Firestore')
            return True
        except Exception as error:
            print('❌ Error de conexión Firestore:', str(error))
            return False
    
    async def setApiKey(self, userId, apiKey):
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            # Validar la clave API y obtener el nombre de la cuenta
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.guildwars2.com/v2/account?access_token={apiKey}") as response:
                    if response.status != 200:
                        print(f"❌ API key inválida para usuario {userId}")
                        return False
                    account_data = await response.json()
                    account_name = account_data.get('name', 'Unknown')

            doc_ref = self.apiKeys.document(str(userId))
            doc = doc_ref.get()
            api_keys = doc.to_dict().get('keys', []) if doc.exists else []
            
            # Añadir la nueva clave como un diccionario
            new_key = {
                'api_key': apiKey,
                'account_name': account_name,
                'updated_at': datetime.now(),
                'active': True if not api_keys else False
            }
            api_keys.append(new_key)
            
            doc_ref.set({'keys': api_keys})
            print(f"✅ API Key añadida para usuario {userId}, cuenta {account_name}")
            return True
        except Exception as error:
            print('❌ Error guardando API key:', str(error))
            return False
    
    async def getApiKey(self, userId):
        if self.db is None:
            print('❌ Database not initialized')
            return None
        try:
            doc_ref = self.apiKeys.document(str(userId))
            doc = doc_ref.get()
            if not doc.exists:
                return None
                
            api_keys = doc.to_dict().get('keys', [])
            for key_data in api_keys:
                if key_data.get('active', False):
                    return key_data.get('api_key')
            return None
        except Exception as error:
            print('❌ Error obteniendo API key:', str(error))
            return None
    
    async def deleteApiKey(self, userId, index=None):
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            doc_ref = self.apiKeys.document(str(userId))
            doc = doc_ref.get()
            if not doc.exists:
                return False
                
            api_keys = doc.to_dict().get('keys', [])
            if not api_keys:
                return False
                
            if index is not None:
                if 0 <= index < len(api_keys):
                    del api_keys[index]
                else:
                    return False
            else:
                api_keys.clear()
                
            if api_keys:
                doc_ref.set({'keys': api_keys})
            else:
                doc_ref.delete()
            print(f"✅ API Key eliminada para usuario {userId}")
            return True
        except Exception as error:
            print('❌ Error eliminando API key:', str(error))
            return False
    
    async def setActiveApiKey(self, userId, index):
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            doc_ref = self.apiKeys.document(str(userId))
            doc = doc_ref.get()
            if not doc.exists:
                return False
                
            api_keys = doc.to_dict().get('keys', [])
            if not (0 <= index < len(api_keys)):
                return False
                
            for i in range(len(api_keys)):
                api_keys[i]['active'] = (i == index)
            
            doc_ref.set({'keys': api_keys})
            print(f"✅ API Key en índice {index} activada para usuario {userId}")
            return True
        except Exception as error:
            print('❌ Error activando API key:', str(error))
            return False
    
    async def getApiKeysList(self, userId):
        if self.db is None:
            print('❌ Database not initialized')
            return []
        try:
            doc_ref = self.apiKeys.document(str(userId))
            doc = doc_ref.get()
            if not doc.exists:
                return []
            
            # Asegurar compatibilidad con claves antiguas
            api_keys = doc.to_dict().get('keys', [])
            for key_data in api_keys:
                if 'account_name' not in key_data:
                    key_data['account_name'] = 'Unknown (Legacy)'
                if 'updated_at' not in key_data:
                    key_data['updated_at'] = datetime.now()
                if 'active' not in key_data:
                    key_data['active'] = False
            
            return api_keys
        except Exception as error:
            print('❌ Error obteniendo lista de API keys:', str(error))
            return []

    async def setReminder(self, userId, reminderData):
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            reminder_ref = self.reminders.document(str(userId))
            reminder_ref.set(reminderData)
            print(f"✅ Recordatorio guardado para usuario {userId}")
            return True
        except Exception as error:
            print(f"❌ Error guardando recordatorio: {str(error)}")
            return False
    
    async def getReminder(self, userId):
        if self.db is None:
            print('❌ Database not initialized')
            return None
        try:
            doc_ref = self.reminders.document(str(userId))
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as error:
            print(f"❌ Error obteniendo recordatorio: {str(error)}")
            return None
    
    async def deleteReminder(self, userId):
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            doc_ref = self.reminders.document(str(userId))
            doc_ref.delete()
            print(f"✅ Recordatorio eliminado para usuario {userId}")
            return True
        except Exception as error:
            print(f"❌ Error eliminando recordatorio: {str(error)}")
            return False
    
    async def get_all_reminders(self):
        if self.db is None:
            print('❌ Database not initialized')
            return []
        try:
            reminders_list = []
            docs = self.reminders.stream()
            
            for doc in docs:
                reminder_data = doc.to_dict()
                reminder_data['userId'] = doc.id
                reminders_list.append(reminder_data)
            
            print(f"✅ Se obtuvieron {len(reminders_list)} recordatorios")
            return reminders_list
        except Exception as error:
            print(f"❌ Error obteniendo todos los recordatorios: {str(error)}")
            return []

    async def addToBlacklist(self, userId, reason="No reason"):
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            self.blacklist.document(str(userId)).set({
                'reason': reason,
                'timestamp': datetime.now()
            })
            print(f"✅ Usuario {userId} añadido a la blacklist")
            return True
        except Exception as error:
            print(f"❌ Error añadiendo a blacklist: {str(error)}")
            return False

    async def removeFromBlacklist(self, userId):
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            self.blacklist.document(str(userId)).delete()
            print(f"✅ Usuario {userId} eliminado de la blacklist")
            return True
        except Exception as error:
            print(f"❌ Error eliminando de blacklist: {str(error)}")
            return False

    async def isBlacklisted(self, userId):
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            doc = self.blacklist.document(str(userId)).get()
            return doc.exists
        except Exception as error:
            print(f"❌ Error comprobando blacklist: {str(error)}")
            return False

    async def saveRoulette(self, channel_id, data):
        """Crea o actualiza una ruleta (merge). Solo se escriben las claves presentes en `data` (excepto channel_id y updated_at)."""
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            payload = {'channel_id': int(channel_id), 'updated_at': datetime.now()}
            if 'guild_id' in data:
                payload['guild_id'] = int(data['guild_id'])
            if 'creator_id' in data:
                payload['creator_id'] = int(data['creator_id'])
            if 'msg_id' in data:
                payload['msg_id'] = int(data['msg_id'])
            if 'active' in data:
                payload['active'] = bool(data['active'])
            if 'participants' in data:
                payload['participants'] = [int(uid) for uid in data['participants']]
            if 'winner_count' in data:
                payload['winner_count'] = int(data['winner_count'])
            self.roulettes.document(str(channel_id)).set(payload, merge=True)
            return True
        except Exception as error:
            print(f"❌ Error guardando ruleta {channel_id}: {str(error)}")
            return False

    async def addRouletteParticipant(self, channel_id, user_id):
        """Añade un participante a la ruleta usando ArrayUnion (atómico, evita duplicados)."""
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            self.roulettes.document(str(channel_id)).update({
                'participants': firestore.ArrayUnion([int(user_id)]),
                'updated_at': datetime.now(),
            })
            return True
        except Exception as error:
            print(f"❌ Error añadiendo participante {user_id} a ruleta {channel_id}: {str(error)}")
            return False

    async def deleteRoulette(self, channel_id):
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            self.roulettes.document(str(channel_id)).delete()
            return True
        except Exception as error:
            print(f"❌ Error eliminando ruleta {channel_id}: {str(error)}")
            return False

    async def getActiveRoulettes(self):
        """Devuelve todas las ruletas activas (lista de dicts)."""
        if self.db is None:
            print('❌ Database not initialized')
            return []
        try:
            results = []
            docs = self.roulettes.where('active', '==', True).stream()
            for doc in docs:
                data = doc.to_dict() or {}
                data['channel_id'] = int(doc.id)
                results.append(data)
            return results
        except Exception as error:
            print(f"❌ Error obteniendo ruletas activas: {str(error)}")
            return []

    # ─────────────────────────────────────────────────────────
    #  Events
    # ─────────────────────────────────────────────────────────

    async def saveEvent(self, event_data: dict) -> bool:
        """Guarda un nuevo evento en Firestore."""
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            doc_id = str(event_data.get("doc_id", event_data.get("message_id", "")))
            payload = {
                "guild_id":   int(event_data.get("guild_id", 0)),
                "channel_id": int(event_data.get("channel_id", 0)),
                "message_id": int(event_data.get("message_id", 0)),
                "creator_id": int(event_data.get("creator_id", 0)),
                "title":      str(event_data.get("title", "")),
                "start_ts":   int(event_data.get("start_ts", 0)),
                "end_ts":     int(event_data.get("end_ts", 0)),
                "status":     str(event_data.get("status", "open")),
                "roles":      event_data.get("roles", []),
                "created_at": event_data.get("created_at", datetime.now()),
            }
            self.events.document(doc_id).set(payload)
            print(f"✅ Evento guardado: {doc_id}")
            return True
        except Exception as e:
            print(f"❌ Error guardando evento: {e}")
            return False

    async def getEvent(self, doc_id: str) -> dict | None:
        """Obtiene un evento por su ID (= message_id)."""
        if self.db is None:
            print('❌ Database not initialized')
            return None
        try:
            doc = self.events.document(str(doc_id)).get()
            if not doc.exists:
                return None
            data = doc.to_dict()
            data["doc_id"] = doc.id
            return data
        except Exception as e:
            print(f"❌ Error obteniendo evento {doc_id}: {e}")
            return None

    async def updateEventRoles(self, doc_id: str, roles: list) -> bool:
        """Actualiza la lista de roles (con participantes) de un evento."""
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            self.events.document(str(doc_id)).update({"roles": roles})
            return True
        except Exception as e:
            print(f"❌ Error actualizando roles del evento {doc_id}: {e}")
            return False

    async def updateEventStatus(self, doc_id: str, status: str) -> bool:
        """Actualiza el estado de un evento (open / closed / cancelled)."""
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            self.events.document(str(doc_id)).update({"status": status})
            return True
        except Exception as e:
            print(f"❌ Error actualizando estado del evento {doc_id}: {e}")
            return False

    async def getOpenEvents(self) -> list:
        """Devuelve todos los eventos con status='open'."""
        if self.db is None:
            print('❌ Database not initialized')
            return []
        try:
            results = []
            for doc in self.events.where("status", "==", "open").stream():
                data = doc.to_dict() or {}
                data["doc_id"] = doc.id
                results.append(data)
            return results
        except Exception as e:
            print(f"❌ Error obteniendo eventos abiertos: {e}")
            return []

    async def getGuildEvents(self, guild_id: str) -> list:
        """Devuelve todos los eventos de un servidor."""
        if self.db is None:
            print('❌ Database not initialized')
            return []
        try:
            results = []
            for doc in self.events.where("guild_id", "==", int(guild_id)).stream():
                data = doc.to_dict() or {}
                data["doc_id"] = doc.id
                results.append(data)
            return results
        except Exception as e:
            print(f"❌ Error obteniendo eventos del servidor {guild_id}: {e}")
            return []

    async def getLogAutouploadConfig(self, guild_id: str) -> dict:
        if self.db is None:
            print('❌ Database not initialized')
            return {"enabled": False, "channel_id": None, "only_success": True}
        try:
            doc = self.logAutoupload.document(str(guild_id)).get()
            if not doc.exists:
                return {"enabled": False, "channel_id": None, "only_success": True}
            data = doc.to_dict() or {}
            return {
                "enabled": bool(data.get("enabled", False)),
                "channel_id": data.get("channel_id"),
                "only_success": bool(data.get("only_success", True)),
            }
        except Exception as e:
            print(f"❌ Error leyendo config autoupload {guild_id}: {e}")
            return {"enabled": False, "channel_id": None, "only_success": True}

    async def setLogAutouploadConfig(self, guild_id: str, config: dict) -> bool:
        if self.db is None:
            print('❌ Database not initialized')
            return False
        try:
            payload = {
                "enabled": bool(config.get("enabled", False)),
                "only_success": bool(config.get("only_success", True)),
                "updated_at": datetime.now(),
            }
            if config.get("channel_id") is not None:
                payload["channel_id"] = int(config["channel_id"])
            self.logAutoupload.document(str(guild_id)).set(payload, merge=True)
            return True
        except Exception as e:
            print(f"❌ Error guardando config autoupload {guild_id}: {e}")
            return False

    async def getEnabledLogAutouploadGuilds(self) -> list[dict]:
        if self.db is None:
            print('❌ Database not initialized')
            return []
        try:
            results = []
            for doc in self.logAutoupload.where("enabled", "==", True).stream():
                data = doc.to_dict() or {}
                data["guild_id"] = doc.id
                if data.get("channel_id"):
                    results.append(data)
            return results
        except Exception as e:
            print(f"❌ Error listando guilds autoupload: {e}")
            return []

    # ─────────────────────────────────────────────────────────

try:
    dbManager = DatabaseManager()
except Exception as e:
    print(f"FATAL ERROR INITIALIZING DATABASE: {e}")
    import traceback
    traceback.print_exc()
    import sys
    sys.stdout.flush()
    dbManager = None


