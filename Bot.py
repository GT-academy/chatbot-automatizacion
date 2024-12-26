import telebot
import sqlite3
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Token del bot
API_TOKEN = '...'
bot = telebot.TeleBot(API_TOKEN)

# Diccionario de categorías y productos
catalogo = {
    "Camisas": ["Camisa Polo - $20", "Camisa Casual - $25", "Camisa Formal - $30"],
    "Pantalones": ["Pantalón de Vestir - $35", "Jeans - $40"],
    "Accesorios": ["Sombrero - $15", "Bufanda - $12", "Gafas de Sol - $18"]
}

# Base de datos
def setup_database():
    conn = sqlite3.connect('tienda_ropa.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id_cliente INTEGER PRIMARY KEY,
        nombre TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER,
        productos TEXT,
        cantidad INTEGER,
        total REAL,
        estado TEXT
    )
    """)
    conn.commit()
    conn.close()

setup_database()

# Función para confirmar el pedido
def confirm_order(message, product, quantity, total):
    confirmation = message.text.lower()
    valid_yes = ["sí", "si", "s"]
    valid_no = ["no"]

    if confirmation in valid_yes:
        conn = sqlite3.connect('tienda_ropa.db')
        cursor = conn.cursor()

        # Registrar cliente
        cursor.execute("INSERT OR IGNORE INTO clientes (id_cliente, nombre) VALUES (?, ?)",
                    (message.chat.id, message.chat.first_name))

        # Registrar pedido
        cursor.execute("INSERT INTO pedidos (id_cliente, productos, cantidad, total, estado) VALUES (?, ?, ?, ?, ?)",
                    (message.chat.id, product, quantity, total, "Pendiente"))
        conn.commit()
        conn.close()

        # Enviar certificado de pedido
        bot.send_message(
            message.chat.id,
            f"✅ ¡Pedido confirmado! Gracias por tu compra.\n\n"
            f"📝 Certificado de pedido:\n"
            f"- Producto: {product}\n"
            f"- Cantidad: {quantity}\n"
            f"- Total: ${total}\n\n"
            f"💳 Por favor, realiza el pago al siguiente número de cuenta:\n"
            f"Cuenta bancaria: 1234-5678-9101-1121\n\n"
            f"Después del pago, un asesor se pondrá en contacto contigo para coordinar la entrega.\n\n"
            f"🟢 Para regresar al menú principal, escribe /menu."
        )
    elif confirmation in valid_no:
        bot.send_message(message.chat.id, "❌ Pedido cancelado.\n\nPara regresar al menú principal, escribe /menu.")
    else:
        bot.send_message(message.chat.id, "⚠️ Por favor, responde con 'sí' o 'no'.")
        bot.register_next_step_handler(message, confirm_order, product, quantity, total)

# Función para enviar el menú principal
def send_menu(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("/catalogo"), KeyboardButton("/mis_pedidos"))
    markup.add(KeyboardButton("🔙 Volver al menú principal"))
    bot.send_message(
        message.chat.id,
        "📋 Menú principal. Selecciona una opción:",
        reply_markup=markup
    )

# Manejador para el comando /start
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "¡Bienvenido a Ropa Trendy! 👚👖 Aquí puedes consultar nuestro catálogo, realizar pedidos y más.\n\n"
        "🛒 Comandos disponibles:\n"
        "/catalogo - Ver productos disponibles\n"
        "/mis_pedidos - Consultar tu historial de pedidos\n"
        "/menu - Volver al menú principal",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton("/catalogo"),
            KeyboardButton("/mis_pedidos")
        )
    )

# Manejador para el comando /catalogo
@bot.message_handler(commands=['catalogo'])
def send_catalogo(message):
    categories = "\n".join([f"- {cat}" for cat in catalogo.keys()])
    bot.send_message(message.chat.id, f"📂 Categorías disponibles:\n{categories}\n\nSelecciona una categoría escribiéndola.\n\nPara regresar al menú, escribe /menu.")
    bot.register_next_step_handler(message, show_products)

# Función para mostrar productos en una categoría
def show_products(message):
    category = message.text.capitalize()
    if category in catalogo:
        products = "\n".join([f"{i+1}. {prod}" for i, prod in enumerate(catalogo[category])])
        bot.send_message(message.chat.id, f"📜 Productos en {category}:\n{products}\n\nEscribe el número del producto que deseas comprar o escribe /menu para regresar al menú principal.")
        bot.register_next_step_handler(message, select_product, category)
    else:
        bot.send_message(message.chat.id, "❌ Categoría no encontrada. Por favor, intenta de nuevo con una categoría válida o escribe /menu para regresar al menú.")
        bot.register_next_step_handler(message, show_products)

# Función para seleccionar un producto
def select_product(message, category):
    if message.text.lower() == "/menu":
        send_menu(message)
        return
    try:
        product_index = int(message.text) - 1
        if 0 <= product_index < len(catalogo[category]):
            product = catalogo[category][product_index]
            bot.send_message(message.chat.id, f"✔️ Seleccionaste: {product}\n¿Cuántas unidades deseas?")
            bot.register_next_step_handler(message, confirm_quantity, product)
        else:
            bot.send_message(message.chat.id, "❌ Número inválido. Por favor, selecciona un número de la lista o escribe /menu para regresar al menú principal.")
            bot.register_next_step_handler(message, select_product, category)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Por favor, ingresa un número válido o escribe /menu para regresar al menú principal.")
        bot.register_next_step_handler(message, select_product, category)

# Función para confirmar cantidad
def confirm_quantity(message, product):
    if message.text.lower() == "/menu":
        send_menu(message)
        return
    try:
        quantity = int(message.text)  # Convertir a número entero
        price = int(product.split("$")[-1])  # Extraer precio del producto
        total = price * quantity  # Calcular el total
        bot.send_message(
            message.chat.id,
            f"🛍️ Pedido: {product} x{quantity}\nTotal: ${total}\n\n¿Confirmar pedido? (Responde 'sí' o 'no')"
        )
        bot.register_next_step_handler(message, confirm_order, product, quantity, total)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Por favor, ingresa una cantidad válida o escribe /menu para regresar al menú principal.")
        bot.register_next_step_handler(message, confirm_quantity, product)

# Historial de pedidos
@bot.message_handler(commands=['mis_pedidos'])
def show_orders(message):
    conn = sqlite3.connect('tienda_ropa.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE id_cliente=?", (message.chat.id,))
    orders = cursor.fetchall()
    conn.close()
    
    if orders:
        orders_text = "\n".join([f"Pedido {order[0]}: {order[2]} x{order[3]} - ${order[4]}" for order in orders])
        bot.send_message(message.chat.id, f"📋 Tus pedidos:\n{orders_text}")
    else:
        bot.send_message(message.chat.id, "❌ No tienes pedidos registrados.")
    
    # Crear el botón para regresar al menú principal
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🔙 Volver al menú principal"))
    
    # Enviar el mensaje con el botón
    bot.send_message(
        message.chat.id, 
        "¿Deseas regresar al menú principal? Escribe /menu para volver.",
        reply_markup=markup
    )

# Manejador para cuando el usuario presione el botón "Volver al menú principal"
@bot.message_handler(func=lambda message: message.text == "🔙 Volver al menú principal")
def go_to_main_menu(message):
    send_menu(message)

# Ejecutar el bot
bot.polling()
