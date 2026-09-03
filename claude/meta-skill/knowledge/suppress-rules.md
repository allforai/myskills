# Suppress rules

Apply after Step 1 classification. A match means do not emit that node class.

| When | Suppress | Keep / instead |
|---|---|---|
| `architecture_pattern = library-sdk` | `demo-forge` | language-native tests only |
| `architecture_pattern = cli` | `demo-forge` | `--help` smoke |
| `architecture_pattern = embedded-firmware` | `demo-forge` | `pio test` / manual device |
| `architecture_pattern` starts with `bot-` and no companion HTTP API | `demo-forge` | mock-provider tests |
| `deployment_platform = vercel` or `deno-deploy` | `infra-design` | document platform as infra |
| `offline_first = true` (Flutter+Drift, Godot no HTTP) | `demo-forge`, `runtime-smoke-verify` | local persistence / no server |
| Game client module | curl / HTTP integration as the client verifier | engine/runtime tests |
| `architecture_pattern = game-mod` | do **not** treat as library-sdk | demo-forge stays (live game) |
| PICO-8, standalone LÖVE2D, GBStudio, Twine/Ren'Py web, HTML5-only HaxeFlixel | `monetization-design`, `retention-hook-design`, `meta-game-design` | note platform has no IAP/push |
| Roblox | generic `monetization-design` and launch-prep IAP | Roblox economy optional node; keep retention |
| `implement` / `tune` / verify-only goals on a game | game-design node injection | consume existing approved artifacts |
| All-approved `approval-records.json` and goals are not create/rebuild | regenerate game-design nodes | skip |

Serverless HTTP functions: do **not** suppress `demo-forge`.
