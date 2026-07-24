"""Pista de 20s para scene2.html. Sintetizada de cero, sin samples ni licencias.

Escrita contra las marcas de la escena, no al revés:
  0.00  apertura (entra el ticker)
  2.10  arranca el ritmo (se dibuja el grafico)
  5.95  primer tick: cada razon que entra tiene su golpecito
  9.60  riser hacia el cierre del conteo
 10.75  el numero aterriza en 71  -> impacto
 11.55  estampa el veredicto
 13.70  giro: "por que no 100" (el ritmo se abre, entra un tono mas oscuro)
 17.20  cierre de marca
"""
import array
import math
import random
import wave

SR = 44100
DUR = 20.0
N = int(SR * DUR)
BPM = 112.0
BEAT = 60.0 / BPM

# Marcas de la escena (tienen que coincidir con scene2.html)
A2, A3, A4, A5, A6 = 2.10, 5.60, 11.00, 13.70, 17.20
T_FILA, FILAS = 0.80, 6
T_CIERRA = A3 + 0.35 + FILAS * T_FILA          # 10.75

buf = [0.0] * N
random.seed(11)


def add(t0, dur, fn, amp=1.0):
    i0 = int(t0 * SR)
    for i in range(int(dur * SR)):
        j = i0 + i
        if 0 <= j < N:
            buf[j] += amp * fn(i / SR)


def tri(f, t):
    x = (f * t) % 1.0
    return 4 * abs(x - 0.5) - 1


def kick(t):
    f = 45 + 75 * math.exp(-t * 22)
    return math.sin(2 * math.pi * f * t) * math.exp(-t * 7.5)


def hat(t):
    return (random.random() * 2 - 1) * math.exp(-t * 95)


def tick(t):
    """Golpecito corto y agudo para cada razon que entra."""
    return (math.sin(2 * math.pi * 1180 * t) * .6 +
            (random.random() * 2 - 1) * .4) * math.exp(-t * 42)


def nota(f, decay=7.0):
    return lambda t: tri(f, t) * math.exp(-t * decay) * min(1.0, t * 300)


def bajo(f):
    def g(t):
        env = min(1.0, t * 60) * math.exp(-t * 0.5)
        return (math.sin(2 * math.pi * f * t) * .72 + tri(f, t) * .28) * env
    return g


def riser(largo):
    def g(t):
        x = t / largo
        barrido = math.sin(2 * math.pi * (170 + 950 * x * x) * t)
        return ((random.random() * 2 - 1) * .55 + barrido * .45) * x * x
    return g


def impacto(t):
    cuerpo = math.sin(2 * math.pi * (58 + 40 * math.exp(-t * 16)) * t) * math.exp(-t * 3.0)
    crack = (random.random() * 2 - 1) * math.exp(-t * 24)
    return cuerpo * .85 + crack * .28


# ── Ritmo: entra con el grafico, respira en el giro del acto 5 ───────────────
t = A2
i = 0
while t < A6:
    hueco = (A4 + 0.6) <= t < (A5 + 0.5)     # aire mientras se lee el veredicto
    calmo = t >= A5
    if not hueco and (not calmo or i % 2 == 0):
        add(t, .5, kick, .90)
    if not hueco:
        add(t + BEAT / 2, .10, hat, .055 if calmo else .075)
    t += BEAT
    i += 1

# ── Bajo: A menor con giro a F y G; en el acto 5 baja a un tono mas oscuro ───
RAIZ = [55.00, 55.00, 43.65, 49.00]          # A1 A1 F1 G1
OSCURO = [43.65, 41.20, 43.65, 36.71]        # F1 E1 F1 D1
k = 0
t = A2
while t < A6:
    tabla = OSCURO if t >= A5 else RAIZ
    add(t, BEAT * 4.2, bajo(tabla[k % 4]), .46)
    t += BEAT * 4
    k += 1

# ── Arpegio ─────────────────────────────────────────────────────────────────
PENT = [220.00, 261.63, 329.63, 392.00, 329.63, 261.63]
paso = BEAT / 2
t = A2 + BEAT
i = 0
while t < A6:
    vol = .16
    if (A4 + 0.6) <= t < (A5 + 0.5):
        vol = .04
    elif t >= A5:
        vol = .10
    add(t, paso * 1.6, nota(PENT[i % len(PENT)]), vol)
    t += paso
    i += 1

# ── Golpes sincronizados con la imagen ──────────────────────────────────────
add(0.00, 1.2, impacto, .58)                       # apertura
for i in range(FILAS):                             # una razon, un tick
    add(A3 + 0.35 + i * T_FILA, .25, tick, .30)
add(T_CIERRA - 1.15, 1.15, riser(1.15), .32)       # subida al cierre del conteo
add(T_CIERRA, 2.4, impacto, 1.00)                  # el 71 aterriza
add(A4 + 0.55, 1.4, impacto, .42)                  # estampa del veredicto
add(A5, 1.6, impacto, .50)                         # giro al "por que no 100"
add(A6, 2.4, impacto, .62)                         # cierre

# Acorde sostenido en el cierre
for f in (220.00, 329.63, 440.00):
    add(A6, 2.8, lambda t, f=f: math.sin(2 * math.pi * f * t) * math.exp(-t * 1.3), .095)

# ── Master ──────────────────────────────────────────────────────────────────
pico = max(abs(x) for x in buf) or 1.0
g = 0.92 / pico
out = array.array('h')
fin_fade = int(.95 * SR)
for i, x in enumerate(buf):
    x = math.tanh(x * g * 1.25) / math.tanh(1.25)
    if i < int(.05 * SR):
        x *= i / (.05 * SR)
    resto = N - i
    if resto < fin_fade:
        x *= resto / fin_fade
    v = int(max(-1.0, min(1.0, x)) * 32000)
    out.append(v); out.append(v)

with wave.open('track.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(out.tobytes())

print(f"track.wav listo: {DUR}s · {BPM:g} BPM · impacto del score en {T_CIERRA}s")
