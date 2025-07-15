import threading
import time
import random
import requests
from flask import Flask

# ======================
# CONFIGURACIÓN
# ======================
API_SOLANA_NEW_TOKENS = "https://public-api.birdeye.so/public/token/new-list"
CAPITAL_INICIAL = 1000.00   # Capital demo inicial en USDC
COMPRA_POR_TOKEN = 50.00    # Monto simulado por operación

# Configuración TP/SL
TAKE_PROFIT_PCT = 0.02    # +2%
STOP_LOSS_PCT = -0.015    # -1.5%

# ======================
# VARIABLES GLOBALES
# ======================
capital_actual = CAPITAL_INICIAL
total_operaciones = 0
ultimo_resultado = "Sin operaciones todavía"
lock = threading.Lock()

# ======================
# SERVIDOR WEB PARA VISUALIZAR ESTADO
# ======================
app = Flask(__name__)

@app.route('/')
def status():
    return f"""
    ✅ Bot demo Solana en Render<br>
    💰 Capital actual: {capital_actual:.2f} USDC<br>
    📊 Operaciones realizadas: {total_operaciones}<br>
    🔄 Última operación: {ultimo_resultado}<br>
    """

# ======================
# FUNCIONES DEL BOT
# ======================

def obtener_tokens_nuevos():
    """Consulta la API de BirdEye para nuevos tokens en Solana."""
    headers = {"x-chain": "solana"}
    try:
        resp = requests.get(API_SOLANA_NEW_TOKENS, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("data", [])
        else:
            print(f"❌ Error API BirdEye: {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error consultando API: {e}")
        return []

def filtrar_tokens_validos(tokens):
    """Filtra tokens con liquidez y volumen mínimo para evitar scams."""
    filtrados = []
    for token in tokens:
        liquidez = token.get("liquidity", {}).get("usd", 0)
        volumen = token.get("v24hUSD", 0)
        if liquidez > 10000 and volumen > 5000:  # mínimo 10k USD liquidez y 5k USD volumen
            filtrados.append(token)
    return filtrados

def simular_trade(token):
    """Simula compra/venta con TP y SL para el token."""
    global capital_actual, total_operaciones, ultimo_resultado

    nombre = token.get("name", "Desconocido")
    precio_entrada = random.uniform(0.5, 2.0)  # simular precio inicial
    monto = COMPRA_POR_TOKEN

    # Objetivos
    tp = precio_entrada * (1 + TAKE_PROFIT_PCT)
    sl = precio_entrada * (1 + STOP_LOSS_PCT)

    print(f"✅ [DEMO] Comprado {nombre} en {precio_entrada:.4f} USDC")

    # Simular movimiento aleatorio del precio
    precio_final = precio_entrada * random.uniform(0.97, 1.03)

    # Resultado según TP/SL
    if precio_final >= tp:
        ganancia = monto * TAKE_PROFIT_PCT
        resultado = f"✅ Take Profit alcanzado en {nombre} | +{ganancia:.2f} USDC"
        capital_actual += ganancia
    elif precio_final <= sl:
        perdida = monto * abs(STOP_LOSS_PCT)
        resultado = f"❌ Stop Loss en {nombre} | -{perdida:.2f} USDC"
        capital_actual -= perdida
    else:
        # Si no llegó ni a TP ni SL, cerrar neutro
        resultado = f"🔄 Cierre neutro en {nombre} | 0 USDC"

    # Actualizar estado
    with lock:
        global total_operaciones, ultimo_resultado
        total_operaciones += 1
        ultimo_resultado = resultado

    print(resultado)

def ciclo_bot():
    """Loop principal del bot (cada 1 min)."""
    global capital_actual
    while True:
        print("\n🔄 Buscando tokens nuevos en Solana...")
        tokens = obtener_tokens_nuevos()
        tokens_validos = filtrar_tokens_validos(tokens)

        if tokens_validos:
            token_elegido = random.choice(tokens_validos)
            simular_trade(token_elegido)
        else:
            print("⚠️ No se encontraron tokens válidos esta vez")

        print(f"💰 Capital actual: {capital_actual:.2f} USDC")
        time.sleep(60)  # espera 1 minuto para la próxima búsqueda

# ======================
# ARRANQUE DEL BOT
# ======================
if __name__ == '__main__':
    hilo_bot = threading.Thread(target=ciclo_bot, daemon=True)
    hilo_bot.start()
    app.run(host="0.0.0.0", port=5000)