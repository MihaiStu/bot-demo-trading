import requests
import time
import json
import random

# === CONFIGURACIÓN ===
CAPITAL_INICIAL = 1000.0        # Capital demo
CAPITAL_DISPONIBLE = CAPITAL_INICIAL
CAPITAL_POR_TRADE = 50.0        # Cada operación usa 50 USD
MIN_LIQUIDEZ = 10000            # Liquidez mínima USD
MIN_VOLUMEN = 5000              # Volumen mínimo 24h USD
TAKE_PROFIT = 1.03              # +3% TP
STOP_LOSS = 0.98                # -2% SL
API_URL = "https://api.dexscreener.com/latest/dex/pairs/solana"

HISTORIAL_FILE = "historial_operaciones.json"

# === FUNCIONES AUXILIARES ===

def obtener_tokens_solana():
    """Obtiene tokens activos en Solana desde Dexscreener"""
    try:
        resp = requests.get(API_URL, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("pairs", [])
        else:
            print(f"❌ Error al obtener tokens ({resp.status_code})")
            return []
    except Exception as e:
        print(f"❌ Error de conexión con API: {e}")
        return []

def filtrar_tokens_validos(tokens):
    """Filtra tokens con liquidez y volumen suficientes"""
    filtrados = []
    for t in tokens:
        liquidity = t.get("liquidity", {}).get("usd", 0)
        volumen24h = t.get("volume", {}).get("h24", 0)
        if liquidity and volumen24h and liquidity >= MIN_LIQUIDEZ and volumen24h >= MIN_VOLUMEN:
            filtrados.append({
                "nombre": t.get("baseToken", {}).get("name", "Desconocido"),
                "simbolo": t.get("baseToken", {}).get("symbol", "???"),
                "precio": float(t.get("priceUsd", 0)),
                "liquidez": liquidity,
                "volumen24h": volumen24h
            })
    return filtrados

def simular_compra(token):
    """Simula compra de un token"""
    global CAPITAL_DISPONIBLE
    if CAPITAL_DISPONIBLE < CAPITAL_POR_TRADE:
        print("⚠️ No hay suficiente capital para nueva compra")
        return None

    cantidad = CAPITAL_POR_TRADE / token["precio"]
    CAPITAL_DISPONIBLE -= CAPITAL_POR_TRADE

    print(f"✅ COMPRA {token['simbolo']} - {cantidad:.4f} unidades a {token['precio']:.6f} USD")

    return {
        "token": token["simbolo"],
        "precio_compra": token["precio"],
        "cantidad": cantidad,
        "capital_invertido": CAPITAL_POR_TRADE,
        "status": "abierta"
    }

def simular_movimiento_precio(precio):
    """Simula fluctuación del mercado"""
    variacion = random.uniform(-0.025, 0.035)  # -2.5% a +3.5%
    return precio * (1 + variacion)

def evaluar_trade(trade):
    """Evalúa TP/SL"""
    nuevo_precio = simular_movimiento_precio(trade["precio_compra"])
    if nuevo_precio >= trade["precio_compra"] * TAKE_PROFIT:
        ganancia = trade["capital_invertido"] * 0.03
        return "cerrada", ganancia
    elif nuevo_precio <= trade["precio_compra"] * STOP_LOSS:
        perdida = -trade["capital_invertido"] * 0.02
        return "cerrada", perdida
    else:
        return "abierta", 0.0

def guardar_historial(historial):
    with open(HISTORIAL_FILE, "w") as f:
        json.dump(historial, f, indent=4)

# === FUNCIÓN PRINCIPAL ===

def main():
    global CAPITAL_DISPONIBLE
    operaciones_abiertas = []
    historial = []

    print("🚀 BOT DEMO SOLANA INICIADO")
    print(f"Capital inicial: {CAPITAL_DISPONIBLE} USD")

    while True:
        print("\n🔄 Buscando tokens válidos en Solana...")
        tokens = obtener_tokens_solana()
        tokens_validos = filtrar_tokens_validos(tokens)

        if not tokens_validos:
            print("⚠️ No hay tokens nuevos válidos. Reintentando en 30s...")
            time.sleep(30)
            continue

        # Selecciona un token aleatorio de los filtrados
        token = random.choice(tokens_validos)
        trade = simular_compra(token)
        if trade:
            operaciones_abiertas.append(trade)

        # Revisión de operaciones abiertas
        nuevas_abiertas = []
        for op in operaciones_abiertas:
            status, resultado = evaluar_trade(op)
            if status == "cerrada":
                CAPITAL_DISPONIBLE += op["capital_invertido"] + resultado
                print(f"💰 Operación {op['token']} cerrada. Resultado: {resultado:.2f} USD | Capital: {CAPITAL_DISPONIBLE:.2f} USD")
                historial.append({
                    "token": op["token"],
                    "resultado": resultado,
                    "capital_restante": CAPITAL_DISPONIBLE
                })
                guardar_historial(historial)
            else:
                nuevas_abiertas.append(op)

        operaciones_abiertas = nuevas_abiertas

        print(f"📊 Capital actual: {CAPITAL_DISPONIBLE:.2f} USD | Operaciones abiertas: {len(operaciones_abiertas)}")

        time.sleep(30)  # Espera 30s antes de la siguiente búsqueda


if __name__ == "__main__":
    main()