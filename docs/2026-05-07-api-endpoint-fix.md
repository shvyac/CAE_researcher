# 2026-05-07 — API Endpoint Investigation & Fix

## Problem

`cae_systems.json` (cron-enriched live data with news items) was never loaded
by the React app. The table always showed stale bundled data with no news badges.

## Investigation

### Symptom
`https://dream.shvtech.com/cae/` returned 200 OK but no news items appeared.

### Root cause (three-layer mismatch)

| Layer | Wrong | Correct |
|---|---|---|
| GitHub Actions deploy target | `/var/www/mysite/user/themes/cae-theme/dist/` | `/var/www/mysite/cae/` |
| Cron script output path | `/var/www/mysite/user/themes/cae-theme/dist/cae_systems.json` | `/var/www/mysite/cae/cae_systems.json` |
| React fetch URL | `/user/themes/cae-theme/dist/cae_systems.json` (Grav-routed → 403) | `./cae_systems.json` (nginx-served → 200) |

### Nginx config (key finding)

```nginx
# /etc/nginx/sites-available/mysite
location ^~ /cae/ {
    index index.html;
    try_files $uri $uri/ =404;
}
```

`root` is `/var/www/mysite`, so nginx serves `/cae/` from `/var/www/mysite/cae/`.
The React app files had been manually placed there (`cae/` directory, owned by shvyac,
last modified Apr 30). GitHub Actions was deploying to the theme directory instead,
so all updates since Apr 30 were going to the wrong place.

`/user/themes/cae-theme/dist/` is also exposed via a separate nginx location block
but the fetch URL had used Grav-routed absolute paths that returned 403.

## Fixes Applied

### 1. `src/components/CAETable.tsx`
```diff
- fetch('/user/themes/cae-theme/dist/cae_systems.json')
+ fetch('./cae_systems.json')
```
Relative URL resolves to `/cae/cae_systems.json` → served from `/var/www/mysite/cae/`.

### 2. `.github/workflows/deploy.yml`
```diff
- /var/www/mysite/user/themes/cae-theme/dist/
+ /var/www/mysite/cae/
```
Applied to: mkdir, rsync deploy, bootstrap rsync.

### 3. `scripts/fetch_cae_news.py`
```diff
- DEPLOYED_JSON = Path("/var/www/mysite/user/themes/cae-theme/dist/cae_systems.json")
+ DEPLOYED_JSON = Path("/var/www/mysite/cae/cae_systems.json")
```

### 4. Server (manual, one-time)
```bash
# Copy existing enriched JSON to correct location
cp /var/www/mysite/user/themes/cae-theme/dist/cae_systems.json /var/www/mysite/cae/cae_systems.json

# Patch cron script in-place
sed -i 's|.../user/themes/cae-theme/dist/cae_systems.json|/var/www/mysite/cae/cae_systems.json|' ~/scripts/fetch_cae_news.py
```

## Result

News badges confirmed loading on live site. LS-DYNA, Radioss, PAM-CRASH,
MSC Nastran and others show 4–5 news items each.

## Branch

`claude/investigate-api-endpoint-qHJgK` — ready to merge to `main`.
