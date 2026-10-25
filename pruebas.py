"""Pruebas del taller. Uso:  python pruebas.py <comando> [n]

  base        Prueba 1: 4 peticiones a /ventas (2 instancias)
  escalar     Prueba 2: agrega instancia_terciaria (5005) a appsettings.json y lanza 6 peticiones
  inventario  Prueba 3: agrega ruta_inventario + cluster_inventario y consulta /inventario
  ventas [n]  n peticiones a /ventas (por defecto 6)
  reset       Restaura appsettings.json inicial (2 instancias, sin inventario)
"""
import copy
import json
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

GATEWAY = "http://localhost:5000"
CONFIG = Path(__file__).parent / "gateway" / "appsettings.json"

HEALTH = {
    "Active": {"Enabled": "true", "Interval": "00:00:05", "Timeout": "00:00:02", "Path": "/health"},
    "Passive": {"Enabled": "true", "ReactivationInterval": "00:00:10"},
}


def cargar():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def guardar(cfg):
    CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"appsettings.json guardado ({time.strftime('%H:%M:%S')}) -> el Gateway debe mostrar [HOT-RELOAD]")
    time.sleep(2)  # tiempo para que YARP aplique y el health check inicial corra


def peticiones(ruta, n):
    cuenta = Counter()
    for i in range(1, n + 1):
        try:
            with urllib.request.urlopen(f"{GATEWAY}{ruta}", timeout=5) as r:
                cuerpo = json.loads(r.read())
                puerto = cuerpo["puerto"]
                print(f"  #{i}: HTTP {r.status} servicio={cuerpo['servicio']} puerto={puerto}")
                cuenta[puerto] += 1
        except Exception as e:
            print(f"  #{i}: ERROR {e}")
    print("  Distribucion:", dict(cuenta))


def escalar():
    cfg = cargar()
    dest = cfg["ReverseProxy"]["Clusters"]["cluster_ventas"]["Destinations"]
    dest["instancia_terciaria"] = {"Address": "http://localhost:5005/"}
    guardar(cfg)


def inventario():
    cfg = cargar()
    rp = cfg["ReverseProxy"]
    rp["Routes"]["ruta_inventario"] = {
        "ClusterId": "cluster_inventario",
        "Match": {"Path": "/inventario/{**catch-all}"},
    }
    rp["Clusters"]["cluster_inventario"] = {
        "LoadBalancingPolicy": "RoundRobin",
        "HealthCheck": copy.deepcopy(HEALTH),
        "Destinations": {"instancia_inventario_1": {"Address": "http://localhost:5003/"}},
    }
    guardar(cfg)


def reset():
    cfg = cargar()
    rp = cfg["ReverseProxy"]
    rp["Routes"].pop("ruta_inventario", None)
    rp["Clusters"].pop("cluster_inventario", None)
    rp["Clusters"]["cluster_ventas"]["Destinations"].pop("instancia_terciaria", None)
    guardar(cfg)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    if cmd == "base":
        peticiones("/ventas/lista", 4)
    elif cmd == "escalar":
        escalar()
        peticiones("/ventas/lista", 6)
    elif cmd == "inventario":
        inventario()
        peticiones("/inventario/lista", 1)
    elif cmd == "ventas":
        peticiones("/ventas/lista", n)
    elif cmd == "reset":
        reset()
    else:
        print(__doc__)


main()
