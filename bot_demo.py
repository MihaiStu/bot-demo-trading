import threading
import time
import requests
from flask import Flask

# =======================
# CONFIGURACIÓN
# =======================
API_SOLANA_NEW_TOKENS = "https://public-api.birdeye.so/public/token/new-list"
HEADERS = {"accept": "application/json"}

# Simulación de capital inicial (1000 USDC en demo)
CAPITAL_INICIAL = 1000.0
capital_disponible = CAPITAL_INICIAL


# =======================
# FUNCIONES DEL BOT
# =======================

def detectar_tokens_nuevos():
    """
    Consulta la API de BirdEye para obtener tokens nuevos en Solana.
    """
    try:
        response = requests.get(API_SOLANA_NEW_TOKENS, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            print(f"❌ Error API BirdEye: {response.status_code}")
    except Exception as e:
        print(f"❌ Error en la consulta API: {e}")
    return []


def filtrar_tokens_validos(tokens):
    """
    Filtra tokens que tengan liquidez y volumen aceptable.
    """
    filtrados = []
    for token in tokens:
        liquidez = token.get("liquidity", {}).get("usd", 0)
        volumen = token.get("v24hUSD", 0)

        if liquidez and volumen and liquidez > 10000 and volumen > 5000:
            filtrados.append({
                "nombre": token.get("name", "Desconocido"),
                "simbolo": token.get("symbol", "?"),
                "liquidez": liquidez,
                "volumen24h": volumen
            })
    return filtrados


def simular_compra_y_venta(token):
    """
    Simula la compra y venta del token con lógica básica.
    """
    global capital_disponible

    # Invertimos solo 50 USDC en cada token como prueba
    inversion = min(50, capital_disponible)
    if inversion <= 0:
        print("⚠ Sin capital disponible para operar")
        return

    print(f"✅ Comprando {token['simbolo']} ({token['nombre']}) con {inversion} USDC...")

    # Simulación de precio
    precio_entrada = 1.0
    take_profit = precio_entrada * 1.05  # 5% de beneficio
    stop_loss = precio_entrada * 0.97    # 3% de pérdida

    # Simular resultado aleatorio (éxito 60%)
    import random
    resultado = random.random()
    if resultado < 0.6:
        capital_disponible += inversion * 0.05  # +5%
        print(f"💰 Vendido {token['simbolo']} con +5% beneficio ✅ Capital: {capital_disponible:.2f}")
    else:
        capital_disponible -= inversion * 0.03  # -3%
        print(f"❌ Vendido {token['simbolo']} con -3% pérdida ❗ Capital: {capital_disponible:.2f}")


def run_bot():
    """
    Bucle principal del bot.
    """
    global capital_disponible

    print("🤖 Bot Solana DEMO iniciado con capital:", capital_disponible, "USDC")

    while True:
        print("🔍 Consultando nuevos tokens...")
        tokens = detectar_tokens_nuevos()
        if tokens:
            validos = filtrar_tokens_validos(tokens)
            if validos:
                print(f"✅ {len(validos)} tokens válidos detectados.")
                for token in validos[:3]:  # Solo los 3 primeros para no saturar
                    simular_compra_y_venta(token)
            else:
                print("⚠ No hay tokens con liquidez/volumen suficiente.")
        else:
            print("❌ No se obtuvieron tokens nuevos.")

        print("⏳ Esperando 1 minuto para la siguiente consulta...")
        time.sleep(60)


# =======================
# SERVIDOR WEB PARA RENDER
# =======================

app = Flask(_name_)

@app.route('/')
def home():
    return f"✅ Bot demo Solana corriendo en Render | Capital actual: {capital_disponible:.2f} USDC"


# =======================
# EJECUCIÓN PRINCIPAL
# =======================
if _name_ == "_main_":
    # Hilo en segundo plano para el bot
    threading.Thread(target=run_bot, daemon=True).start()

    # Mantener el puerto abierto para Render
    app.run(host="0.0.0.0", port=5000)
