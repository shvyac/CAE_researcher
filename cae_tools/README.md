# cae_tools

CAE System List project — starter files for dream.shvtech.com (GRAV CMS on Sakura.ne.jp)

## Structure

```
cae_tools/
├── check_sakura_spec.sh          # Server spec inspector — run on dream.shvtech.com
├── src/
│   ├── types/
│   │   └── cae.ts                # TypeScript interfaces (CAESystem, CAEDomain, etc.)
│   └── data/
│       ├── caeSystems.json       # Initial CAE system data (15 tools)
│       └── caeTargets.json       # Cron fetch targets (vendor news URLs)
└── README.md
```

## Server info (dream.shvtech.com)

| Item | Value |
|---|---|
| OS | Ubuntu 24.04.4 LTS |
| GRAV root | `/var/www/mysite/` |
| PHP | 8.3.6 (curl, mbstring, json ✓) |
| Node | v18.19.1 |
| Python | 3.12.3 |
| Crontab | available |

## Next steps

1. Scaffold React + Vite + TypeScript project (Phase B2)
2. Set up GitHub Actions deploy to `/var/www/mysite/` (Phase B1)
3. Write `fetch_cae_news.php` cron script (Phase B3)

## Data files location on GRAV

```
/var/www/mysite/user/data/cae_systems.json   ← runtime data (updated by cron)
/var/www/mysite/user/pages/cae-list/         ← GRAV page
/var/www/mysite/assets/                      ← built JS/CSS from Vite
```

## Crontab schedule (to set up on dream.shvtech.com)

```bash
0 6 * * 1   php ~/cron/fetch_cae_news.php >> ~/cron/cron.log 2>&1
5 6 * * 1   php ~/cron/update_data.php    >> ~/cron/cron.log 2>&1
0 2 * * 0   bash ~/cron/cleanup.sh        >> ~/cron/cron.log 2>&1
```
