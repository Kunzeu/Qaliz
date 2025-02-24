import os
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        # Configuración de Firebase usando variables de entorno
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

    # El resto del código permanece exactamente igual
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
            doc_ref = self.apiKeys.document(str(userId))
            doc_ref.set({
                'api_key': apiKey,
                'updated_at': datetime.now()
            })
            print(f"✅ API Key {'añadida' if not doc_ref.get().exists else 'actualizada'} para usuario {userId}")
            return True
        except Exception as error:
            print('❌ Error guardando API key:', str(error))
            return False
    
    async def getApiKey(self, userId):
        try:
            doc_ref = self.apiKeys.document(str(userId))
            doc = doc_ref.get()
            print(f"🔍 Buscando API key para usuario {userId}: {'Encontrada' if doc.exists else 'No encontrada'}")
            return doc.to_dict().get('api_key') if doc.exists else None
        except Exception as error:
            print('❌ Error obteniendo API key:', str(error))
            return None
    
    async def deleteApiKey(self, userId):
        try:
            doc_ref = self.apiKeys.document(str(userId))
            doc_ref.delete()
            print(f"✅ API Key eliminada para usuario {userId}")
            return True
        except Exception as error:
            print('❌ Error eliminando API key:', str(error))
            return False
    
    async def hasApiKey(self, userId):
        try:
            doc_ref = self.apiKeys.document(str(userId))
            doc = doc_ref.get()
            return doc.exists
        except Exception as error:
            print('❌ Error verificando API key:', str(error))
            return False
    
    async def setReminder(self, userId, reminderData):
        try:
            reminder_ref = self.reminders.document(str(userId))
            reminder_ref.set(reminderData)
            
            doc = reminder_ref.get()
            if doc.exists:
                print(f"✅ Recordatorio guardado correctamente para {userId}: {doc.to_dict()}")
            else:
                print(f"❌ El recordatorio no se guardó correctamente para {userId}")
            
            return True
        except Exception as error:
            print(f"❌ Error guardando el recordatorio: {str(error)}")
            return False
    
    async def getReminder(self, userId):
        try:
            doc_ref = self.reminders.document(str(userId))
            doc = doc_ref.get()
            if doc.exists:
                print(f"🔍 Recordatorio encontrado para {userId}: {doc.to_dict()}")
                return doc.to_dict()
            else:
                print(f"❌ No se encontró un recordatorio para {userId}")
                return None
        except Exception as error:
            print(f"❌ Error obteniendo el recordatorio: {str(error)}")
            return None
    
    async def deleteReminder(self, userId):
        try:
            doc_ref = self.reminders.document(str(userId))
            doc_ref.delete()
            print(f"✅ Recordatorio eliminado para {userId}")
            return True
        except Exception as error:
            print(f"❌ Error al eliminar el recordatorio: {str(error)}")
            return False
    
    async def checkRemindersCollection(self):
        try:
            docs = self.reminders.stream()
            for doc in docs:
                print(f"Documento encontrado en reminders: {doc.id} => {doc.to_dict()}")
        except Exception as error:
            print(f"❌ Error al verificar colección reminders: {str(error)}")
    
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

# Instancia global del manejador de base de datos
dbManager = DatabaseManager()