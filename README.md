# Discord Bot - Moodle

Este es un bot de Discord desarrollado con `discord.py`, diseñado para jugadores de *Guild Wars 2* y administradores de servidores. Integra la API de *Guild Wars 2* (v2) para proporcionar precios en tiempo real, herramientas de moderación y un sistema de comandos personalizados.  

## Características

### Funcionalidades Originales (Guild Wars 2)
- **`/item <búsqueda>`**: Muestra precios actuales de ítems (ej. Ectos, precursorys) usando la API de GW2.
- **`/clovers`**: Calcula el precio actual de Mystic Clovers basado en materiales y mercado.
- **`/delivery`**: Revisa el contenido de tu Trading Post delivery box (requiere API key).
- **`/t3`, `/t4`, `/t5`, `/t6`**: Muestra precios de materiales T3 a T6.
- **`/materials`**: Muestra precios de Gift of Condensed Magic y Gift of Condensed Might.
- **`/gift`**: Precio fijo de GOMS (Gift of Magic), GOJMS (Gift of Jewelry Magic), y GOJW (Gift of Jade Weapon).
- **`/apikey add/remove/check`**: Gestiona tu API key de GW2 con permisos "account", "inventories", y "tradingpost".
- **`/hora`**: Muestra la hora actual en el servidor.
- **`/inventory <search>`**: Busca ítems en banco y almacenamiento de materiales de GW2 con paginación (`page`, `page_size`) y manejo de errores.
- **`.to [duración]`**: Permite a los usuarios aplicarse un auto-timeout (por defecto 60 segundos, máximo 10 minutos) con validaciones.
- **Sistema de Comandos Personalizados (`CommandManager`)**:
  - Crea, edita, elimina comandos con categorías, aliases y soporte futuro para acciones (ej. ban).
- **Gestión de Roles**: Configura roles de admin y mod con `.configurar_roles`, persistiendo en Firestore.

## Requisitos

- **Python**: Versión 3.8 o superior.
- **Bibliotecas**:
  - `discord.py==2.3.2` (para comandos slash y eventos)
  - `aiohttp==3.8.6` (para solicitudes asíncronas a APIs)
  - `google-cloud-firestore==2.13.1` (para integración con Firestore)
  - `python-dotenv==1.0.0` (para variables de entorno)
- **Credenciales**:
  - Token de bot de Discord (obténlo en [Discord Developer Portal](https://discord.com/developers/applications)).
  - Archivo JSON de credenciales de Firestore (descarga desde Google Cloud).
  - API key de Guild Wars 2 (opcional, obténla en [account.arena.net](https://account.arena.net/applications)).

## Instalación

1. **Clona el Repositorio**:
   ```bash
   git clone https://github.com/Kunzeu/Moodle.git
   cd Moodle
2. Instala las dependencias necesarias usando `pip install -r requirements.txt`.
3. Obtén una clave API de Guild Wars 2 en (https://wiki.guildwars2.com/wiki/API:2) o directamente en el código (asegúrate de mantenerla segura).
4. Ejecuta el bot usando `python index.py`.


2 ## Contact

Puedes contactar conmigo en Discord: [Kunzeu](https://discord.com/users/552563672162107431)
