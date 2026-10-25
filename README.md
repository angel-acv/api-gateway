# Taller: Descubrimiento y registro en caliente con YARP

# CREADORES: Angel coavas y Juan Ligardo

Gateway en .NET (YARP) + microservicios de Ventas e Inventario en Python. Todo se ejecuta desde cmd.

## Estructura

```
gateway/                 API Gateway (Program.cs, appsettings.json)
servicios/servicio.py    Microservicio Ventas / Inventario
pruebas.py               Edita appsettings.json y lanza las peticiones
iniciar_gateway.bat      Arranca el Gateway (http://localhost:5000)
iniciar_servicio.bat     Arranca un servicio: <ventas|inventario> <puerto>
```

## Requisitos

- Python 3 (no necesita librerias externas)
- .NET SDK (el proyecto apunta a `net10.0`; cambia `TargetFramework` en `gateway/Gateway.csproj` si tu runtime es otro)

## Preparacion (antes de la Prueba 1)

Abre **una consola (cmd) por cada comando**, en la carpeta del proyecto:

| Consola | Comando |
|---|---|
| 1 | `iniciar_gateway.bat` |
| 2 | `iniciar_servicio.bat ventas 5001` |
| 3 | `iniciar_servicio.bat ventas 5002` |
| 4 | `python pruebas.py` (consola libre para las pruebas) |

Deja el `appsettings.json` en su estado inicial (2 instancias, sin inventario):

```
python pruebas.py reset
```

Mantén visible la consola 1 (Gateway): ahi aparecen los mensajes `[HOT-RELOAD]` para el informe.

## Prueba 1: estado base (2 instancias)

```
python pruebas.py base
```

Esperado: 4 peticiones, 2 al puerto 5001 y 2 al 5002.

## Prueba 2: escalado horizontal en caliente (instancia 5005)

1. Abre una consola nueva y levanta la tercera instancia: `iniciar_servicio.bat ventas 5005`
2. Sin apagar el Gateway, en la consola de pruebas:
   ```
   python pruebas.py escalar
   ```
   Esto agrega `instancia_terciaria` al `cluster_ventas`, guarda el archivo y lanza 6 peticiones.
3. En la consola del Gateway debe aparecer `[HOT-RELOAD] ... Configuracion recargada` con las tres instancias.
4. Espera unos 5 segundos (el health check activo debe marcar la nueva instancia como sana) y repite:
   ```
   python pruebas.py ventas 6
   ```

Esperado: 2 peticiones a cada puerto (5001, 5002 y 5005).
Si justo despues de guardar el reparto sale desigual, es normal: el health check de la instancia nueva aun no corrio.

## Prueba 3: nuevo microservicio (Inventario 5003)

1. Abre una consola nueva: `iniciar_servicio.bat inventario 5003`
2. Sin apagar el Gateway:
   ```
   python pruebas.py inventario
   ```
   Esto agrega `ruta_inventario` y `cluster_inventario` (con health checks activo y pasivo) y consulta `/inventario/lista`.

Esperado: `HTTP 200 servicio=inventario puerto=5003` y un nuevo `[HOT-RELOAD]` en el Gateway con la ruta y el cluster de inventario.

Tambien puedes probar con cURL: `curl http://localhost:5000/inventario/lista`

## Prueba 4: resiliencia combinada

1. Cierra la consola de la instancia 5005 (Ctrl+C).
2. Espera unos 5 segundos (intervalo del health check activo).
3. Ejecuta:
   ```
   python pruebas.py ventas 6
   curl http://localhost:5000/inventario/lista
   ```

Esperado: Ventas reparte solo entre 5001 y 5002 (sin errores) e Inventario sigue respondiendo.

## Comandos de `pruebas.py`

| Comando | Accion |
|---|---|
| `base` | 4 peticiones a `/ventas` |
| `escalar` | Agrega la instancia 5005 en `appsettings.json` y lanza 6 peticiones |
| `inventario` | Agrega ruta y cluster de Inventario y hace 1 peticion |
| `ventas [n]` | `n` peticiones a `/ventas` (por defecto 6) |
| `reset` | Restaura `appsettings.json` inicial |

## Evidencias para el informe

- Consola del Gateway con los mensajes `[HOT-RELOAD]` (tras `escalar` y tras `inventario`).
- Salida de `python pruebas.py ventas 6` con el reparto entre las 3 instancias.
- Salida de `python pruebas.py inventario` (o cURL/Postman a `/inventario/...`).
- Consola del Gateway/pruebas tras detener el 5005 (Prueba 4).

## Notas

- El mensaje `[HOT-RELOAD]` puede salir duplicado: Windows notifica dos veces el cambio del archivo. No afecta nada.
- Tambien puedes editar `gateway/appsettings.json` a mano con tu editor en lugar de usar `pruebas.py`; YARP lo recarga al guardar.
