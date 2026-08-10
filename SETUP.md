# FCB Tracker - Setup

1. Add repository secrets (Settings -> Secrets):
   - `FOOTBALL_DATA_KEY` – la teva clau d'api-football
   - `MAIL_USER` – compte Gmail (email)
   - `MAIL_PASS` – App password de Gmail

2. Configure GitHub Pages to serve from the `site/` folder (or `main` branch `/site` folder) in repository settings.

3. Edit `data/settings.json` per ajustar `team_id`, `season`, `members` i `barca_request_url`.

4. Opcional: provar localment amb un entorn virtual i les variables d'entorn:

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
