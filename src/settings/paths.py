from pathlib import Path

PATHS: dict[str, Path] = dict(
    custom_tokens=None,
    export=Path('export'),
    icons=Path('media', 'icons'),
    images=Path('media', 'images'),
    inventory=None,
    keeps=Path('keeps'),
    media=Path('media'),
    rulesets=Path('src', 'rulesets'),
    scrape=Path('media', 'scrape'),
    settings=Path('settings.toml'),
    tokens=Path('media', 'tokens'),
    workbench=None
)
