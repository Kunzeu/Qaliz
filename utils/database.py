import os
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import aiohttp

load_dotenv()

class DatabaseManager:
    def __init__(self):
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
        
        if not firebase_admin._apps:
            self.cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(self.cred)
        
        self.db = firestore.client()
        self.apiKeys = self.db.collection('api_keys')
        self.reminders = self.db.collection('reminders')

    async def connect(self):
        try:
            doc_ref = self.db.collection('test').document('ping')
            doc_ref.set({'message': 'ping'})
            print('✅ Conectado a Firebase Firestore')
            return True
        except Exception as error:
            print('❌ Error de conexión Firestore:', str(error))
            return False
    
    async def setApiKey(self, userId, apiKey):
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
        try:
            reminder_ref = self.reminders.document(str(userId))
            reminder_ref.set(reminderData)
            print(f"✅ Recordatorio guardado para usuario {userId}")
            return True
        except Exception as error:
            print(f"❌ Error guardando recordatorio: {str(error)}")
            return False
    
    async def getReminder(self, userId):
        try:
            doc_ref = self.reminders.document(str(userId))
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as error:
            print(f"❌ Error obteniendo recordatorio: {str(error)}")
            return None
    
    async def deleteReminder(self, userId):
        try:
            doc_ref = self.reminders.document(str(userId))
            doc_ref.delete()
            print(f"✅ Recordatorio eliminado para usuario {userId}")
            return True
        except Exception as error:
            print(f"❌ Error eliminando recordatorio: {str(error)}")
            return False
    
    async def get_all_reminders(self):
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

dbManager = DatabaseManager()