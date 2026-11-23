# I Was a Teenage Exocolonist — Esperanto

A community Esperanto localisation of **I Was a Teenage Exocolonist** using the game's official mod support.

## Current scope

Two batches translate 68 interface strings in `Data/Exocolonist - localization.tsv`: 40 main-menu, settings and gallery strings, plus 28 inventory labels, card-selection and exploration messages. Other strings remain English. Human language review and full UI testing remain pending; this is not a complete localisation or a Workshop release.

The existing `ID`, `EN`, and `Example or notes` columns are retained. Esperanto replaces selected values in `EN`; no new language column has been added. The translated main menu has been observed in-game, with a font-weight mismatch on Esperanto letters. Full UI testing remains pending.

An optional [Windows companion font patcher](tools/README.md) addresses the standard bold font's fallback configuration. Players must run it separately; enabling or downloading this translation mod does not apply the font fix. It currently supports one verified game build. The maintainer reported that the fix appears to work in-game on 23 November 2026; other font styles and screens still need testing.

## Local testing

The repository folder doubles as the local mod at `Documents/Exocolonist/Mods/Esperanto` (your Documents folder may be redirected to OneDrive).

Following the developer's [Exocolonist Workshop Guide](https://steamcommunity.com/sharedfiles/filedetails/?id=3727950488):

1. Back up your savegames before testing mods.
2. Start the game, enable **Esperanto** in the mods menu, then restart it.
3. If another mod replaces the same data file, put Esperanto above it in the mod order for this test.

The guide explains that mods replace whole files. Untranslated rows in this one actively edited localisation file are therefore retained. Do not copy the complete original story into this repository.

### First-batch smoke test

- Check the main menu for `daŭrigi`, `nova ludo` and `ŝargi` where those actions are available.
- Open settings and check `agordoj`, `ĝenerala`, `grafiko`, `sono` and `regiloj`.
- Check `ĉefa menuo`, `antaŭa`, `ŝaltita` and `kreditaĵoj` for correct Esperanto diacritics and clipping. This batch exercises **ĉ, ĝ, ĵ, ŝ, ŭ**; **ĥ** still needs a later rendering check.
- Inspect save/load menus and the gallery. Check the long folder-opening label for clipping without deleting any save data.
- Check that untranslated text still displays normally and no missing-text errors appear.
- Record the game build, resolution, UI scale, mod order and screenshots in the PR, including any loading or layout issues.

### Second-batch checks

Open the memories and inventory screens and check `Memoroj`, `Ekipaĵo` and `Kolektaĵoj`. Verify the card count, equipped count and grouped-item count display real numbers in place of `{1}` and `{2}`. Check the equipped-pet filter, long inventory hints and equipment restrictions for clarity and clipping. Where available, check the return-home confirmation and card-selection prompt. This batch has not yet been tested in-game.

## Contributing and roadmap

Read [CONTRIBUTING.md](CONTRIBUTING.md) and use [GLOSSARY.md](GLOSSARY.md) for terminology decisions. Small translation batches go through pull requests and human review.

Planned stages: UI/system text; cards, skills and jobs; an intro story slice; incremental character/story translation; complete localisation; Steam Workshop release. After the first batch works in-game, add lightweight structural validation and GitHub Actions before substantial story work.

Keep pristine reference files under ignored `local/upstream/` or `upstream/`. Original game content and derivative translations are not granted an MIT/GPL licence by this project. Any future licence for project tooling should be scoped separately.
