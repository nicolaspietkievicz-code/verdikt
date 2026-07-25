# Carrusel IG 1080x1350: "Cambios de veredicto" con datos reales, estetica Verdikt.
#
# Antes era UNA imagen con seis filas apretadas. Ahora es un carrusel: caratula
# + una placa por activo + cierre. Cada cambio se lee solo, con el simbolo
# grande, el paso de un veredicto al otro y el score en una barra de 0 a 100.
#
# Portable: en Windows usa Consolas/Segoe; en GitHub Actions (Ubuntu) cae a las
# fuentes empacadas en ig/fonts. Expone generate_carousel() para que el
# orquestador (ig_daily.py) lo llame; corrido a mano escribe en ig/cambios/.
import math, json, os, urllib.request
from PIL import Image, ImageDraw

# Colores del theme.ts de la app
BG=(7,9,12); CARD=(16,21,29); BORDER=(37,43,55); TEXT=(230,233,238); DIM=(139,147,161)
GREEN=(47,191,113); GREEN_DIM=(30,96,66)
VCOL={"COMPRA":(76,175,125),"ACUMULAR":(127,184,154),"NEUTRAL":(201,162,39),
      "CAUTELA":(217,139,82),"EVITAR":(217,106,123)}

CHANGES_URL="https://app.verdikt.finance/verdict-changes"

# Instagram admite 10 imagenes por carrusel: caratula + 8 cambios + cierre.
MAX_CAMBIOS=8

S=2; W,H=1080*S,1350*S; PAD=64*S

CLASE={"stock":"Acción","crypto":"Cripto","cedear":"CEDEAR","etf":"ETF"}

# --- Fuentes portables --------------------------------------------------------
# Se prueban carpetas (bundle propio, Windows, DejaVu de Linux) y, dentro de
# cada rol, varios nombres candidatos. El primero que exista gana.
_FONT_DIRS=[
    os.path.join(os.path.dirname(os.path.abspath(__file__)),"ig","fonts"),
    r"C:\Windows\Fonts",
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/cascadia-code",
    "/usr/share/fonts",
]

from PIL import ImageFont

def _font(candidates, size):
    for name in candidates:
        for base in _FONT_DIRS:
            p=os.path.join(base,name)
            if os.path.exists(p):
                return ImageFont.truetype(p,size)
    return ImageFont.load_default()

# Atajos por rol, para no repetir la lista de candidatos en cada llamada.
def MONO(sz):   return _font(["CascadiaCode-Regular.ttf","consola.ttf","DejaVuSansMono.ttf"],sz*S)
def MONO_B(sz): return _font(["CascadiaCode-Bold.ttf","consolab.ttf","DejaVuSansMono-Bold.ttf"],sz*S)
def SANS(sz):   return _font(["Inter-Regular.ttf","segoeui.ttf","DejaVuSans.ttf"],sz*S)
def SANS_B(sz): return _font(["Inter-Bold.ttf","segoeuib.ttf","DejaVuSans-Bold.ttf"],sz*S)

def draw_v(dr,ox,oy,side,green=GREEN,dim=GREEN_DIM):
    def P(fx,fy): return (ox+side*fx,oy+side*fy)
    lt,bot,end=P(0.16,0.30),P(0.46,0.86),P(0.78,0.30)
    w=side*0.11
    def cap(p,col): dr.ellipse([p[0]-w/2,p[1]-w/2,p[0]+w/2,p[1]+w/2],fill=col)
    dr.line([lt,bot],fill=dim,width=int(round(w))); cap(lt,dim); cap(bot,dim)
    ang=math.atan2(end[1]-bot[1],end[0]-bot[0])
    hl,hw=side*0.22,side*0.15
    tip=(end[0]+hl*0.5*math.cos(ang),end[1]+hl*0.5*math.sin(ang))
    bc=(tip[0]-hl*math.cos(ang),tip[1]-hl*math.sin(ang))
    px,py=math.cos(ang+math.pi/2),math.sin(ang+math.pi/2)
    dr.line([bot,bc],fill=green,width=int(round(w))); cap(bot,green)
    dr.polygon([tip,(bc[0]+px*hw,bc[1]+py*hw),(bc[0]-px*hw,bc[1]-py*hw)],fill=green)

def _fetch_changes():
    return json.load(urllib.request.urlopen(CHANGES_URL,timeout=30))

def _fecha_corta(dd):
    mes={"01":"ene","02":"feb","03":"mar","04":"abr","05":"may","06":"jun",
         "07":"jul","08":"ago","09":"sep","10":"oct","11":"nov","12":"dic"}
    return f"{int(dd[8:10])} {mes.get(dd[5:7],'')} {dd[:4]}" if len(dd)==10 else dd

# --- Piezas comunes -----------------------------------------------------------
def _lienzo():
    """Fondo comun a todas las placas del carrusel: cuadricula + header de marca.
    Es el mismo de las placas evergreen, para que el feed se vea de una pieza."""
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    cell=42*S; grid=(24,28,36)
    for x in range(0,W,cell): d.line([(x,0),(x,H)],fill=grid,width=1)
    for y in range(0,H,cell): d.line([(0,y),(W,y)],fill=grid,width=1)

    mono_b=MONO_B(44); ts=84*S; tx=ty=PAD
    d.rounded_rectangle([tx,ty,tx+ts,ty+ts],radius=ts*0.22,fill=CARD,outline=BORDER,width=2)
    draw_v(d,tx+ts*0.14,ty+ts*0.14,ts*0.72)
    wx,wy=tx+ts+28*S,ty+ts/2-30*S
    for c in "VERDIKT":
        d.text((wx,wy),c,font=mono_b,fill=TEXT); wx+=d.textlength(c,font=mono_b)+6*S
    d.text((wx,wy),"_",font=mono_b,fill=GREEN)
    return img,d

def _pie(d,linea="Un veredicto claro, de 0 a 100. Actualizado todos los días."):
    d.text((PAD,H-150*S),linea,font=SANS(28),fill=DIM)
    d.text((PAD,H-96*S),"app.verdikt.finance",font=MONO(30),fill=GREEN)

def _guardar(img,out_path):
    img=img.resize((1080,1350),Image.LANCZOS)
    os.makedirs(os.path.dirname(out_path) or ".",exist_ok=True)
    img.save(out_path,optimize=True)
    return out_path

def _chips(d,y,simbolos,max_w):
    """Los tickers del dia como fichas. Envuelve solo: si no entran todos, la
    ultima ficha dice cuantos quedaron afuera en vez de cortar a la mitad."""
    f=MONO(28); x=PAD; alto=52*S
    for i,s in enumerate(simbolos):
        w=d.textlength(s,font=f)+36*S
        if x+w>PAD+max_w:
            resto=len(simbolos)-i
            if resto:
                t=f"+{resto}"
                d.text((x+18*S,y+11*S),t,font=f,fill=DIM)
            break
        d.rounded_rectangle([x,y,x+w,y+alto],radius=10*S,fill=CARD,outline=BORDER,width=2)
        d.text((x+18*S,y+11*S),s,font=f,fill=TEXT)
        x+=w+14*S
    return y+alto

# --- Placas del carrusel ------------------------------------------------------
def portada(data,items,out_path):
    """Caratula: cuantos cambiaron, cuando, y cuales. Es la unica que se ve en
    el feed sin deslizar, asi que dice el que de una. `items` son los que
    entraron al carrusel: el numero grande tiene que ser el que el que desliza
    va a encontrar, no el total, o la caratula promete de mas."""
    total=len(data.get("items",[]))
    img,d=_lienzo()

    d.text((PAD,300*S),"HOY CAMBIARON DE VEREDICTO",font=MONO(28),fill=GREEN)

    n=str(len(items))
    fn=SANS_B(210)
    d.text((PAD,360*S),n,font=fn,fill=TEXT)
    nw=d.textlength(n,font=fn)
    d.text((PAD+nw+28*S,490*S),"activos",font=SANS_B(56),fill=TEXT)

    d.text((PAD,600*S),"cambiaron de veredicto",font=SANS_B(56),fill=TEXT)
    sub=_fecha_corta(data.get("date",""))
    if total>len(items):
        sub+=f"  ·  los {len(items)} de mayor movimiento, de {total}"
    d.text((PAD,680*S),sub,font=MONO(30),fill=DIM)

    d.line([(PAD,760*S),(W-PAD,760*S)],fill=BORDER,width=2)
    _chips(d,800*S,[it["symbol"] for it in items],W-2*PAD)

    # Invitacion a deslizar: sin esto la caratula parece un posteo suelto.
    f=MONO_B(32)
    d.text((PAD,H-300*S),"DESLIZÁ",font=f,fill=DIM)
    d.text((PAD+d.textlength("DESLIZÁ",font=f)+20*S,H-300*S),"→",font=f,fill=GREEN)

    _pie(d,"Uno por uno, con el score de 0 a 100.")
    return _guardar(img,out_path)

def _barra(d,y,score,prev_score,color):
    """Barra de 0 a 100 con el score de hoy lleno y una marca donde estaba ayer:
    el movimiento se ve sin tener que leer los numeros."""
    x0,x1=PAD+40*S,W-PAD-40*S; alto=18*S
    d.rounded_rectangle([x0,y,x1,y+alto],radius=alto/2,fill=(24,29,38),outline=BORDER,width=2)
    ancho=(x1-x0)*max(0,min(100,score))/100
    if ancho>alto:
        d.rounded_rectangle([x0,y,x0+ancho,y+alto],radius=alto/2,fill=color)
    if prev_score is not None:
        mx=x0+(x1-x0)*max(0,min(100,prev_score))/100
        d.line([(mx,y-14*S),(mx,y+alto+14*S)],fill=DIM,width=3)
        t="ayer"; f=MONO(20)
        tw=d.textlength(t,font=f)
        d.text((min(max(mx-tw/2,x0),x1-tw),y+alto+22*S),t,font=f,fill=DIM)
    f=MONO(22)
    d.text((x0,y-42*S),"0",font=f,fill=DIM)
    tw=d.textlength("100",font=f)
    d.text((x1-tw,y-42*S),"100",font=f,fill=DIM)

def cambio(it,idx,total,out_path):
    """Una placa por activo: simbolo grande, de que veredicto a cual, y el score."""
    img,d=_lienzo()
    new=it["verdict"]; prev=it["prev_verdict"]; col=VCOL.get(new,TEXT)

    # Contador arriba a la derecha, alineado con el wordmark del header.
    f=MONO(28); t=f"{idx:02d} / {total:02d}"
    d.text((W-PAD-d.textlength(t,font=f),PAD+26*S),t,font=f,fill=DIM)

    # El simbolo va lo mas grande posible sin salirse: hay tickers de 3 letras
    # y otros de 7, y a cuerpo fijo los largos se comian el margen.
    fsym=MONO_B(110)
    for pt in (110,96,84,72):
        fsym=MONO_B(pt)
        if d.textlength(it["symbol"],font=fsym)<=W-2*PAD:
            break
    d.text((PAD,260*S),it["symbol"],font=fsym,fill=TEXT)

    nombre=it.get("name","")[:26]
    clase=CLASE.get(it.get("asset_class",""),"")
    # Cuando el nombre es el ticker (SAP, GM) no se repite: queda solo la clase.
    sub=" · ".join(x for x in (nombre if nombre.upper()!=it["symbol"] else "",clase) if x)
    d.text((PAD,410*S),sub,font=SANS(32),fill=DIM)

    cy0,cy1=520*S,950*S
    d.rounded_rectangle([PAD,cy0,W-PAD,cy1],radius=16*S,fill=CARD,outline=BORDER,width=2)

    # De -> a. La flecha va centrada entre los dos veredictos, no pegada al texto.
    fv=MONO_B(52); fp=MONO_B(52)
    d.text((PAD+40*S,cy0+70*S),prev,font=fp,fill=VCOL.get(prev,DIM))
    aw=d.textlength(prev,font=fp)
    ax=PAD+40*S+aw+30*S
    d.text((ax,cy0+70*S),"→",font=fv,fill=DIM)
    d.text((ax+d.textlength("→",font=fv)+30*S,cy0+70*S),new,font=fv,fill=col)

    # Score de hoy, grande y del color del veredicto nuevo.
    fs=SANS_B(90); st=str(it["score"])
    sw=d.textlength(st,font=fs)
    d.text((W-PAD-40*S-sw-d.textlength("/100",font=MONO(30))-10*S,cy0+40*S),st,font=fs,fill=col)
    d.text((W-PAD-40*S-d.textlength("/100",font=MONO(30)),cy0+90*S),"/100",font=MONO(30),fill=DIM)

    _barra(d,cy0+280*S,it["score"],it.get("prev_score"),col)

    # La lectura en castellano de lo que muestra la barra: el que solo mira la
    # placa de paso se lleva igual el dato.
    prev_sc=it.get("prev_score")
    if prev_sc is not None:
        delta=it["score"]-prev_sc
        verbo="subió" if delta>0 else "bajó" if delta<0 else "quedó igual"
        txt=(f"El score {verbo} {abs(delta)} puntos desde ayer"
             if delta else "El score quedó igual que ayer")
        d.text((PAD,cy1+70*S),txt,font=SANS(32),fill=DIM)

    _pie(d)
    return _guardar(img,out_path)

def cierre(out_path):
    """Ultima placa: que hace la app, para el que llego deslizando hasta el final."""
    img,d=_lienzo()
    d.text((PAD,300*S),"¿Comprar, acumular",font=SANS_B(64),fill=TEXT)
    d.text((PAD,380*S),"o evitar?",font=SANS_B(64),fill=GREEN)
    d.text((PAD,500*S),"Un veredicto claro, de 0 a 100, para",font=SANS(34),fill=DIM)
    d.text((PAD,552*S),"acciones, CEDEARs y cripto.",font=SANS(34),fill=DIM)

    ts=200*S; tx=PAD; ty=700*S
    d.rounded_rectangle([tx,ty,tx+ts,ty+ts],radius=ts*0.22,fill=CARD,outline=BORDER,width=2)
    draw_v(d,tx+ts*0.14,ty+ts*0.14,ts*0.72)

    d.text((PAD,H-330*S),"Buscá cualquier activo en la app,",font=SANS(32),fill=DIM)
    d.text((PAD,H-282*S),"gratis y sin registro.",font=SANS(32),fill=DIM)
    _pie(d,"El score no es una recomendación de inversión.")
    return _guardar(img,out_path)

# --- API para el orquestador ---------------------------------------------------
def generate_carousel(out_dir="ig/cambios", data=None, max_items=MAX_CAMBIOS):
    """Dibuja el carrusel entero y devuelve (rutas, items_usados). Las rutas van
    en el orden en que se publican: portada, un cambio por placa, cierre."""
    if data is None:
        data=_fetch_changes()
    # Cuando hay mas cambios que placas, los que entran son los que mas se
    # movieron. El backend ya los devuelve en ese orden, pero se ordena igual:
    # la caratula dice "de mayor movimiento" y eso tiene que ser cierto aunque
    # el endpoint algun dia cambie de criterio.
    items=sorted(data.get("items",[]),
                 key=lambda it: abs(it.get("score",0)-it.get("prev_score",0)),
                 reverse=True)[:max_items]
    os.makedirs(out_dir,exist_ok=True)

    rutas=[portada(data,items,os.path.join(out_dir,"01-portada.png"))]
    for i,it in enumerate(items,start=1):
        rutas.append(cambio(it,i,len(items),
                            os.path.join(out_dir,f"{i+1:02d}-{it['symbol']}.png")))
    rutas.append(cierre(os.path.join(out_dir,f"{len(items)+2:02d}-cierre.png")))
    return rutas,items

if __name__=="__main__":
    rutas,_=generate_carousel()
    for r in rutas: print("ok:",r)
