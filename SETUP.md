# Setup — Dashboard Central Recoleta 4

## Pasos para publicar (una sola vez)

### 1. Crear el repositorio en GitHub

1. Ir a https://github.com/new
2. Nombre del repo: `central-dashboard`
3. Visibilidad: **Public** ✅ ← necesario para GitHub Pages gratis  
   *(el dashboard estará protegido por contraseña — nadie puede verlo sin la clave)*
4. NO marcar "Add README" ni ningún otro archivo
5. Clic en **Create repository**

---

### 2. Subir el código

Abrir una terminal (CMD o PowerShell) en la carpeta del repo y ejecutar:

```bash
cd "C:\Users\franc\Documents\Claude\Proyectos\Central\Analisis\Analisis CPYE\repo"

git config --global user.email "francisco.carosella@gmail.com"
git config --global user.name  "francisco75"

git branch -m main
git add -A
git commit -m "Dashboard inicial"
git remote add origin https://github.com/francisco75/central-dashboard.git
git push -u origin main
```

Cuando pida usuario/contraseña de GitHub, ingresar tus credenciales.  
*(Si tenés 2FA activado, usar un Personal Access Token en lugar de la contraseña)*

---

### 3. Configurar los 3 Secrets (credenciales seguras)

1. Ir a: https://github.com/francisco75/central-dashboard/settings/secrets/actions
2. Clic en **New repository secret** para cada uno:

| Nombre | Valor |
|--------|-------|
| `DATALIVE_USER` | `principal.centralrecoleta4` |
| `DATALIVE_PASS` | *(contraseña de Datalive)* |
| `DASHBOARD_PASSWORD` | `Central2025` |

---

### 4. Activar GitHub Pages

1. Ir a: https://github.com/francisco75/central-dashboard/settings/pages
2. **Source**: "GitHub Actions" ← seleccionar esta opción
3. Guardar

---

### 5. Correr el workflow manualmente (primera vez)

1. Ir a: https://github.com/francisco75/central-dashboard/actions
2. Clic en "📊 Actualización Diaria Dashboard"
3. Clic en **Run workflow** → **Run workflow**
4. Esperar ~3 minutos

---

### 6. URL del dashboard

Después del primer deploy:

```
https://francisco75.github.io/central-dashboard/
```

Abrir en el navegador → pedir contraseña → ingresar `Central2025`

---

## Cómo funciona la actualización automática

```
Todos los días Lun–Sáb a las 23:00 hs (hora Argentina):

1. GitHub despierta el workflow en sus servidores
2. El script entra a Datalive con tus credenciales (guardadas como Secrets)
3. Descarga ventas del mes en curso por producto
4. Actualiza el dashboard HTML con los datos nuevos
5. Encripta el HTML con staticrypt (contraseña: Central2025)
6. Publica el HTML encriptado en la URL de GitHub Pages
7. Listo — tu máquina no estuvo encendida en ningún momento
```

## ¿Qué es privado y qué no?

| Qué | ¿Privado? |
|-----|-----------|
| Contraseña Datalive | ✅ Solo en GitHub Secrets |
| Datos de ventas en el código fuente del repo | ❌ Visible en GitHub |
| Dashboard en la URL pública | ✅ Requiere contraseña |

*Si querés que los datos del código fuente también sean privados, podemos agregar Cloudflare Pages + Cloudflare Access (gratis, requiere crear cuenta en cloudflare.com).*
