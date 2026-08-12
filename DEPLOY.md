# Desplegament a GitHub Pages

Aquesta pàgina és una web estàtica i es pot publicar directament a GitHub Pages sense cap compilació.

## Opció 1: desplegar des de la branca principal

1. Pensa la web com una pàgina estàtica a la carpeta arrel del repositori.
2. Confirma que hi ha aquests fitxers:
   - `index.html`
   - `styles.css`
   - `app.js`
   - `data/matches.json`
   - `data/fcb.json`
3. A GitHub, obre el repositori.
4. Ves a Settings > Pages.
5. En Source, selecciona `Deploy from a branch`.
6. Tria la branca `main` o `master` i la carpeta `/root`.
7. Guarda.
8. GitHub Pages generarà una URL del tipus:
   `https://<usuari>.github.io/<repositori>/`

## Opció 2: desplegar des de la carpeta docs

Si prefereixes tenir la web en una carpeta `docs`:

1. Mou `index.html`, `styles.css`, `app.js` i les dades a `docs/`.
2. A Settings > Pages, selecciona `Deploy from a branch`.
3. Tria la branca principal i la carpeta `/docs`.
4. Guarda.

## Verificació local

Per provar-ho localment:

```bash
python3 -m http.server 8000
```

I després obre:

```text
http://localhost:8000
```

## Nota

La pàgina carrega les dades des de `./data/matches.json`, per això funciona correctament quan es publica a GitHub Pages sense necessitat de backend.
