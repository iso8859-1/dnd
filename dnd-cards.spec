# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files

textual_datas, textual_binaries, textual_hiddenimports = collect_all("textual")
pydantic_datas, pydantic_binaries, pydantic_hiddenimports = collect_all("pydantic")
reportlab_datas = collect_data_files("reportlab")

a = Analysis(
    ["main.py"],
    pathex=["src"],
    binaries=textual_binaries + pydantic_binaries,
    datas=[
        ("src/dnd_cards/assets", "dnd_cards/assets"),
        ("data", "data"),
    ] + textual_datas + pydantic_datas + reportlab_datas,
    hiddenimports=[
        "dnd_cards",
        "dnd_cards.cli",
        "dnd_cards.tui",
        "dnd_cards.composer",
        "dnd_cards.renderer",
        "dnd_cards.loader",
        "dnd_cards.scanner",
        "dnd_cards.models",
        "dnd_cards.config",
        "dnd_cards.errors",
        "dnd_cards.assets",
        "typer",
        "click",
        "rich",
        "yaml",
        "pydantic",
        "jinja2",
        "reportlab",
        "textual",
    ] + textual_hiddenimports + pydantic_hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="dnd-cards",
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    runtime_tmpdir=None,
)
