import requests
import time
import csv
from datetime import datetime, timedelta

# ================= CONFIGURACIÓN =================
CAPITAL_INICIAL = 1000.0
INVERSION_POR_TOKEN = 100.0

LIQUIDEZ_MINIMA = 5000       # USD
VOLUMEN_MINIMO = 10000       # USD
FDV_MAXIMO = 2_000_000       # USD

TAKE_PROFIT = 0.20           # +20%
STOP_LOSS = -0.10            # -10%
MAX_DIAS_HOLD = 3            # Cerrar después de 3 días

API_URL = "https://public-api.birdeye.so/public/token/new-list"
HEADERS = {"x-chain": "solana"}

# ================= VARIABLES DE ESTADO =================
capital = CAPITAL_INICIAL
operaciones_abiertas = []  # [{token, precio_entrada, fecha_entrada}]
historial = []

# ================= FUNCIONES =================
def obtener_tokens_nuevos():
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=10).json()
        if "data" in res and "items" in res["data"]:
            return res["data"]["items"]
        else:
            return []
    except Exception as e:
        print(f"❌ Error consultando API: {e}")
        return []

def filtrar_token(token):
    liquidez = token.get("liquidity", {}).get("usd", 0)
    volumen = token.get("volume_24h", {}).get("usd", 0)
    fdv = token.get("fdv", 0)

    if liquidez >= LIQUIDEZ_MINIMA and volumen >= VOLUMEN_MINIMO and fdv <= FDV_MAXIMO:
        return True
    return False

def simular_precio_actual(precio_inicial):
    # Simulación de cambio de precio (±5% cada ciclo)
    import random
    cambio = random.uniform(-0.05, 0.05)
    return precio_inicial * (1 + cambio)

def comprar_token(token):
    global capital
    if capital < INVERSION_POR_TOKEN:
        print("⚠ No hay capital suficiente para comprar más tokens.")
        return

    nombre = token.get("name", "Desconocido")
    simbolo = token.get("symbol", "?")
    precio_entrada = token.get("price", 1.0) or 1.0
    fecha_entrada = datetime.now()

    capital -= INVERSION_POR_TOKEN

    operaciones_abiertas.append({
        "token": f"{nombre} ({simbolo})",
        "precio_entrada": precio_entrada,
        "fecha_entrada": fecha_entrada,
        "invertido": INVERSION_POR_TOKEN
    })

    print(f"✅ COMPRA DEMO: {nombre} por {INVERSION_POR_TOKEN}€ a {precio_entrada} USD")

def revisar_operaciones():
    global capital, operaciones_abiertas, historial

    nuevas_op = []
    for op in operaciones_abiertas:
        precio_actual = simular_precio_actual(op["precio_entrada"])
        variacion = (precio_actual - op["precio_entrada"]) / op["precio_entrada"]

        # Decidir vender
        dias_hold = (datetime.now() - op["fecha_entrada"]).days
        vender = False

        if variacion >= TAKE_PROFIT:
            vender = True
            resultado = op["invertido"] * (1 + TAKE_PROFIT)
            motivo = "Take Profit ✅"
        elif variacion <= STOP_LOSS:
            vender = True
            resultado = op["invertido"] * (1 + STOP_LOSS)
            motivo = "Stop Loss ❌"
        elif dias_hold >= MAX_DIAS_HOLD:
            vender = True
            resultado = op["invertido"]  # neutro
            motivo = "Cierre por tiempo ⏳"
        else:
            nuevas_op.append(op)
            continue

        capital += resultado
        beneficio = resultado - op["invertido"]

        historial.append({
            "token": op["token"],
            "fecha_entrada": op["fecha_entrada"].strftime("%Y-%m-%d %H:%M"),
            "fecha_salida": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "beneficio": round(beneficio, 2),
            "capital_total": round(capital, 2),
            "motivo": motivo
        })

        print(f"💰 VENTA: {op['token']} | {motivo} | Beneficio: {beneficio:.2f}€ | Capital total: {capital:.2f}€")

    operaciones_abiertas = nuevas_op
    guardar_historial()

def guardar_historial():
    with open("trading_log.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["token", "fecha_entrada", "fecha_salida", "beneficio", "capital_total", "motivo"])
        writer.writeheader()
        writer.writerows(historial)

def ciclo_bot():
    global capital
    print(f"\n=== CICLO BOT | Capital disponible: {capital:.2f}€ ===")

    # Revisar operaciones abiertas
    if operaciones_abiertas:
        revisar_operaciones()

    # Detectar tokens nuevos
    tokens = obtener_tokens_nuevos()
    print(f"🔍 Tokens detectados: {len(tokens)}")

    for token in tokens:
        if filtrar_token(token):
            comprar_token(token)

# ================= LOOP PRINCIPAL =================
if __name__ == "__main__":
    print("🚀 Iniciando BOT DEMO DE TRADING...")

    while True:
        ciclo_bot()
        time.sleep(60)  # espera 1 minuto por ciclo (para demo)