# grocrun-flyers

**EN** — Weekly archive of public grocery flyer prices (Flipp) for the GrocRun app. Runs every Monday and Thursday on GitHub Actions, free because this repo is public. Only flyer prices are stored here: no app code, no personal data. Region: optional hidden secret `POSTAL`, else a public downtown Montreal postal code.

File: `archive_seed.json.gz` → `{"v": "<timestamp>", "rows": [[merchant, name, price, pct, validFrom, validTo, priceText], ...]}`

Raw link: `https://raw.githubusercontent.com/ghostaiproject/grocrun-flyers/main/archive_seed.json.gz`

---

**FR** — Archive hebdomadaire des prix des circulaires d'épicerie publiques (Flipp) pour l'app GrocRun. Roule chaque lundi et jeudi sur GitHub Actions, gratuit parce que le dépôt est public. Seulement les prix des circulaires sont ici : aucun code de l'app, aucune donnée personnelle. Région : secret caché optionnel `POSTAL`, sinon un code postal public du centre-ville de Montréal.

Fichier : `archive_seed.json.gz` (même format que ci-dessus).
