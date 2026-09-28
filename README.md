# DotA v6.81b AI

An enhanced, English AI edition of **Defense of the Ancients (DotA) v6.81b Allstars** for *Warcraft III: The Frozen Throne*. Play the classic 6.81b patch against computer-controlled opponents on **Easy**, **Normal**, or **Insane** difficulty — solo, co-op, or any mix of human and AI players across both teams.

The map is kept as a **fully version-controlled source tree** (`src/`) and packed into a playable `.w3x` with a small, self-contained build script — no proprietary editor required.

---

## Highlights

**AI opponents**
- Difficulty scaling for last-hitting, ganking, item builds, rune control and skill usage.

**Balance-neutral fixes** (gameplay numbers unchanged from 6.81b)
- **Item interactions corrected** — Maelstrom / Mjollnir and Diffusal Blade now stack correctly with other attack-modifier effects instead of silently overriding them, with illusions handled per real-game rules.
- **Skill fixes** — Poison-type effects now respect spell immunity; several effect radii/scales corrected.
- **Stability** — resource-leak fixes on hot code paths for smoother long games.

**Text & interface**
- Full **English** localization of menus, messages, and hero/skill/item text.
- **Tooltip pass** — added missing mana-cost lines and command-card tooltips, and cleaned up stray copy-paste artifacts across abilities and items.

**Presentation**
- Model, scale and skin corrections for a cleaner battlefield.

---

## Requirements

- **Warcraft III: The Frozen Throne**, patch **1.26a** recommended (works on the 1.2x line).
- To build the map from source: **Python 3.8+** on Linux x86-64 (a StormLib build is bundled in `tools/`).

---

## Building from source

```bash
python3 build.py            # builds "DotA v6.81b AI <version>.w3x" next to the repo
python3 build.py --verify   # builds twice and checks integrity (faithful/complete/deterministic/named)
python3 build.py src OUT.w3x   # build a source tree to a specific output path
```

The build is deterministic and self-contained: it archives everything in `src/` (ordered by `src/_filelist.txt`) into a fresh map archive and applies the map header from `src/_hm3w.bin`.

---

## Installing & playing

1. Build the map (above), or grab a prebuilt `.w3x` from the releases.
2. Copy `DotA v6.81b AI <version>.w3x` into your Warcraft III `Maps\` folder (e.g. `Maps\Download\`).
3. Host a **Custom Game**, select the map, add computer players to either team, and start.
4. Pick a game mode at the start (e.g. `-ap`, `-ar`, `-rd`, …) exactly as in standard DotA.

---

## Versioning

The single source of truth for the release version is the top-level **`VERSION`** file. The in-game name, loading title and map-selection header are all generated from it at build time. To cut a new release, edit `VERSION` and rebuild — nothing else.

---

## Repository layout

| path | contents |
|------|----------|
| `src/` | the complete map as an extracted source tree (every file version-controlled). |
| `src/_filelist.txt` | archive file order used when packing. |
| `src/_hm3w.bin` | the 512-byte map (lobby) header. |
| `build.py` | packs `src/` into a playable `.w3x`. |
| `tools/` | build helpers: `w3x.py` (MPQ read/write), `release.py` (version/name), bundled `libstorm.so`. |
| `VERSION` | the release version string. |

---

## Credits & disclaimer

Defense of the Ancients, its heroes, items and map design are the work of **IceFrog** and the **DotA Allstars** team; the AI foundation derives from the community DotA AI map line. This is a non-commercial, fan-made edition provided for offline play against computer opponents. Warcraft III is a trademark of Blizzard Entertainment. All original assets and trademarks belong to their respective owners.
