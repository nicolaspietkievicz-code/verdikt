# Publicar solo en el Instagram de Verdikt — configuración inicial

**Para qué es esto:** que la app publique sola el posteo diario de "cambios de
veredicto" en Instagram, sin que vos toques nada. Ya está todo el código armado
(genera la imagen con datos vivos y la publica por la vía oficial de Meta). Lo
único que falta es **darle permiso una sola vez**: conseguir dos valores
(`IG_USER_ID` y `IG_ACCESS_TOKEN`) y pegarlos como secretos del repo. Esta guía
es esa parte.

**Por qué no alcanza con usuario y contraseña:** Instagram no deja que un
programa "escriba tu clave y entre" (va contra sus reglas y es inseguro). La
forma oficial y segura es un **token**: un permiso acotado, que podés revocar
cuando quieras, y que nunca es tu contraseña.

Tiempo estimado: 20-30 min. Es tedioso pero es de una sola vez.

---

## Requisitos previos

1. **La cuenta `@verdikt.finance` tiene que ser Empresa o Creador** (no
   personal). En la app de Instagram: **Configuración → Tipo de cuenta y
   herramientas → Cambiar a cuenta profesional** → elegí **Empresa**.

2. **Una página de Facebook vinculada a esa cuenta.** Meta exige que la cuenta
   de IG cuelgue de una página de FB (aunque la página esté vacía). Si no
   tenés: creá una en facebook.com/pages/create (nombre "Verdikt"). Después,
   en la app de IG: **Configuración → Centro de cuentas** (o **Editar perfil →
   Página**) y vinculá la página.

> Si preferís, todo esto (cuenta profesional + vincular página) se hace también
> desde **business.facebook.com** (Meta Business Suite) en un solo lugar.

---

## Paso 1 — Crear una app en Meta for Developers

Es la "aplicación" bajo la cual corre el permiso.

1. Entrá a **developers.facebook.com** y logueate con tu Facebook.
2. Arriba a la derecha: **Mis apps → Crear app**.
3. Caso de uso: elegí **Otro** → tipo **Empresa (Business)**.
4. Ponele nombre (ej. "Verdikt Poster") y creala.
5. En el panel de la app, **Agregar productos** → agregá **Instagram** (o
   "Instagram Graph API"). Con eso alcanza; no hace falta publicarla ni pasar
   revisión para publicar en TU propia cuenta.

Anotá de **Configuración → Básica**: el **App ID** y el **App Secret** (vas a
necesitarlos para el token largo).

---

## Paso 2 — Conseguir el `IG_USER_ID`

Es el número interno de tu cuenta de Instagram.

1. En developers.facebook.com, entrá al **Explorador de la API Graph**
   (Herramientas → Graph API Explorer).
2. Arriba, en **Meta App**, elegí tu app.
3. Tocá **Generate Access Token** y aceptá los permisos (los del Paso 3).
4. En la barra de consulta escribí y ejecutá (GET):

   ```
   me/accounts?fields=instagram_business_account,name
   ```

   Te devuelve tus páginas; buscá la de Verdikt y copiá el número que aparece
   en `instagram_business_account.id`. **Ese es tu `IG_USER_ID`.**

---

## Paso 3 — Generar el token con los permisos correctos

En el mismo Graph API Explorer, al generar el token, marcá estos permisos:

- `instagram_basic`
- `instagram_content_publish`  ← el clave, es el que deja publicar
- `pages_show_list`
- `pages_read_engagement`
- `business_management`

El token que te da el Explorador es **corto (dura ~1-2 horas)**. Sirve para
probar, pero para el bot necesitás uno que dure. Dos opciones:

### Opción A (simple): token de larga duración (60 días)

Pegá esto en el navegador reemplazando los valores (usa el token CORTO como
`fb_exchange_token`):

```
https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=TU_APP_ID&client_secret=TU_APP_SECRET&fb_exchange_token=TOKEN_CORTO
```

Te devuelve un `access_token` que dura ~60 días. **Ese es tu `IG_ACCESS_TOKEN`.**
Contra: hay que renovarlo cada ~2 meses (te aviso cuando se acerque; se rehace
este mismo paso).

### Opción B (recomendada, no vence): token de Usuario del Sistema

Más pasos, pero el token **no expira** — ideal para un bot.

1. Entrá a **business.facebook.com → Configuración del negocio**.
2. **Usuarios → Usuarios del sistema → Agregar** (creá uno, ej. "verdikt-bot",
   rol Admin).
3. Asignale activos: la **página** de Verdikt (con permiso de administrar) y la
   **app** del Paso 1.
4. Tocá **Generar nuevo token** → elegí tu app → marcá los mismos permisos del
   Paso 3 → generá. **Ese token no vence** = tu `IG_ACCESS_TOKEN`.

---

## Paso 4 — Cargar los secretos en el repo

1. Andá al repo en GitHub: **github.com/nicolaspietkievicz-code/verdikt**.
2. **Settings → Secrets and variables → Actions → New repository secret**.
3. Creá dos:
   - `IG_USER_ID` = el número del Paso 2.
   - `IG_ACCESS_TOKEN` = el token del Paso 3.

Quedan encriptados; ni siquiera se ven en los logs.

---

## Paso 5 — Probar

1. En el repo: **Actions → "Instagram diario de Verdikt" → Run workflow**.
2. Dejá **dry-run = true** la primera vez: genera la imagen y muestra qué
   publicaría, sin publicar. Revisá que el token y el user id figuren como
   "seteado".
3. Después corré de nuevo con **dry-run = false**: publica de verdad. Andá al
   Instagram y fijate que apareció el posteo.

Listo. De ahí en más publica **solo, todos los días a las 19:20 (hora
Argentina)** cuando haya cambios de veredicto. Los días sin cambios no postea.

---

## Notas

- **Qué se publica:** por ahora, el posteo de "cambios de veredicto" (imagen +
  texto + hashtags), con datos vivos de `app.verdikt.finance`. Se pueden sumar
  otros tipos (Top de hoy, ánimo del mercado, educativos) — el motor de
  publicación ya está, solo falta el generador de cada uno.
- **Seguridad:** el token es revocable. Si alguna vez querés cortar todo,
  borralo del Usuario del Sistema (o cambiá la contraseña de FB) y listo.
- **Costo:** cero. Todo corre en GitHub Actions (gratis en este repo público).
