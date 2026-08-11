# FCB Tracker - Setup

1. Add repository secrets (Settings -> Secrets):
   - `FOOTBALL_DATA_KEY` – la teva clau d'api-football
   - `MAIL_USER` – compte Gmail (email)
   - `MAIL_PASS` – App password de Gmail

2. Configure GitHub Pages to serve from the `site/` folder (or `main` branch `/site` folder) in repository settings.

3. Edit `data/settings.json` per ajustar `team_id`, `season`, `members` i `barca_request_url`.

4. Opcional: provar localment amb `uv` (recomanat) o un entorn virtual tradicional:

Usant `uv` (més ràpid, gestiona l'entorn i les dependències):

```bash
# instal·lar uv (opcional: pip o instal·lador oficial)
pip install uv
# o (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# sincronitza les dependències del projecte i crea .venv
uv sync --dev

# executar les tasques dins de l'entorn del projecte
uv run python actions/fetch_matches.py
uv run python actions/check_requests.py
uv run python actions/process_attendance.py
uv run python actions/send_reminders.py
```

Opció tradicional amb entorn virtual:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FOOTBALL_DATA_KEY=...
export MAIL_USER=...
export MAIL_PASS=...
python actions/fetch_matches.py
python actions/check_requests.py
python actions/process_attendance.py
python actions/send_reminders.py
```

Notes sobre GitHub Actions:

- Les workflows ara utilitzen l'acció oficial `astral-sh/setup-uv` per instal·lar `uv`, preparar Python i sincronitzar l'entorn. Això fa que els passos de CI coincideixin amb l'ús local de `uv`.
- Si vols reproduir el comportament de CI localment, instal·la `uv` i executa `uv sync --dev` abans d'executar els scripts amb `uv run`.
