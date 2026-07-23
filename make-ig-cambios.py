# Posteo IG 1080x1350: "Cambios de veredicto" con datos reales, estetica Verdikt.
#
# Portable: en Windows usa Consolas/Segoe; en GitHub Actions (Ubuntu) cae a
# DejaVu (el workflow instala fonts-dejavu-core). Expone generate() para que el
# orquestador (ig_daily.py) lo llame; corrido a mano escribe ig/cambios.png.
import math, json, os, urllib.request
from PIL import Image, ImageDraw, ImageFont

# Colores del theme.ts de la app
BG=(7,9,12); CARD=(16,21,29); BORDER=(37,43,55); TEXT=(230,233,238); DIM=(139,147,161)
GREEN=(47,191,113); GREEN_DIM=(30,96,66)
VCOL={"COMPRA":(76,175,125),"ACUMULAR":(127,184,154),"NEUTRAL":(201,162,39),
      "CAUTELA":(217,139,82),"EVITAR":(217,106,123)}

CHANGES_URL="https://app.verdikt.finance/verdict-changes"

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

def _font(candidates, size):
    for name in candidates:
        for base in _FONT_DIRS:
            p=os.path.join(base,name)
            if os.path.exists(p):
                return ImageFont.truetype(p,size)
    return ImageFont.load_default()

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

def generate(out_path="ig/cambios.png", data=None):
    """Dibuja el posteo de cambios de veredicto. Devuelve dict con la data usada
    (para el caption). Si `data` viene dado, no vuelve a pegarle al backend."""
    if data is None:
        data=_fetch_changes()

    S=2; W,H=1080*S,1350*S
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)

    cell=42*S; grid=(24,28,36)
    for x in range(0,W,cell): d.line([(x,0),(x,H)],fill=grid,width=1)
    for y in range(0,H,cell): d.line([(0,y),(W,y)],fill=grid,width=1)

    # Fuentes empacadas primero (ig/fonts): local y CI rinden IDENTICO. Los
    # nombres de sistema quedan de red de seguridad por si faltara el bundle.
    mono_b=_font(["CascadiaCode-Bold.ttf","consolab.ttf","DejaVuSansMono-Bold.ttf"],44*S)
    mono  =_font(["CascadiaCode-Regular.ttf","consola.ttf","DejaVuSansMono.ttf"],30*S)
    mono_sm=_font(["CascadiaCode-Regular.ttf","consola.ttf","DejaVuSansMono.ttf"],24*S)
    title_f=_font(["Inter-Bold.ttf","segoeuib.ttf","DejaVuSans-Bold.ttf"],60*S)
    sans  =_font(["Inter-Regular.ttf","segoeui.ttf","DejaVuSans.ttf"],28*S)

    # Header: tile con la V + VERDIKT_
    ts=84*S; tx,ty=64*S,64*S
    d.rounded_rectangle([tx,ty,tx+ts,ty+ts],radius=ts*0.22,fill=CARD,outline=BORDER,width=2)
    draw_v(d,tx+ts*0.14,ty+ts*0.14,ts*0.72)
    wx=tx+ts+28*S; wy=ty+ts/2-30*S
    for c in "VERDIKT":
        d.text((wx,wy),c,font=mono_b,fill=TEXT); wx+=d.textlength(c,font=mono_b)+6*S
    d.text((wx,wy),"_",font=mono_b,fill=GREEN)

    items=data.get("items",[])[:6]
    dd=data.get("date","")
    mes={"01":"ene","02":"feb","03":"mar","04":"abr","05":"may","06":"jun","07":"jul","08":"ago","09":"sep","10":"oct","11":"nov","12":"dic"}
    ftxt=f"{int(dd[8:10])} {mes.get(dd[5:7],'')} {dd[:4]}" if len(dd)==10 else dd

    d.text((64*S,210*S),"Hoy cambiaron de veredicto",font=title_f,fill=TEXT)
    d.text((64*S,296*S),f"{len(data.get('items',[]))} activos · {ftxt}",font=sans,fill=DIM)

    cx0,cy0,cx1=64*S,380*S,W-64*S
    row_h=118*S
    cy1=cy0+40*S+row_h*max(len(items),1)+24*S
    d.rounded_rectangle([cx0,cy0,cx1,cy1],radius=16*S,fill=CARD,outline=BORDER,width=2)
    y=cy0+32*S
    for it in items:
        sym=it["symbol"]; prev=it["prev_verdict"]; new=it["verdict"]; sc=it["score"]
        d.text((cx0+36*S,y),sym,font=mono_b,fill=TEXT)
        d.text((cx0+36*S,y+52*S),it.get("name","")[:22],font=mono_sm,fill=DIM)
        px_=cx0+340*S
        d.text((px_,y+12*S),prev,font=mono,fill=VCOL.get(prev,DIM))
        aw=d.textlength(prev,font=mono)
        d.text((px_+aw+18*S,y+12*S),"→",font=mono,fill=DIM)
        d.text((px_+aw+52*S,y+12*S),new,font=mono,fill=VCOL.get(new,DIM))
        st=str(sc); sw=d.textlength(st,font=mono_b)
        d.text((cx1-36*S-sw,y+8*S),st,font=mono_b,fill=VCOL.get(new,TEXT))
        y+=row_h
        if it is not items[-1]:
            d.line([(cx0+36*S,y-14*S),(cx1-36*S,y-14*S)],fill=BORDER,width=1)

    d.text((64*S,H-150*S),"Un veredicto claro, de 0 a 100. Actualizado todos los días.",font=sans,fill=DIM)
    d.text((64*S,H-96*S),"app.verdikt.finance",font=mono,fill=GREEN)

    img=img.resize((1080,1350),Image.LANCZOS)
    os.makedirs(os.path.dirname(out_path) or ".",exist_ok=True)
    img.save(out_path,optimize=True)
    return data

if __name__=="__main__":
    generate()
    print("ok")
