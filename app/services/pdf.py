"""Render a character sheet PDF via WeasyPrint."""
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from ..config import settings


def _get_jinja_env():
    return Environment(loader=FileSystemLoader(settings.templates_dir))


def _modifier(score: int) -> str:
    mod = (score - 10) // 2
    return f"+{mod}" if mod >= 0 else str(mod)


def render_character_pdf(char_dict: dict, class_obj=None, species_obj=None, background_obj=None) -> bytes:
    env = _get_jinja_env()
    template = env.get_template("character_sheet.html")

    attrs = char_dict.get("base_attributes") or {}
    asi = char_dict.get("background_asi") or {}

    def total(key):
        return (attrs.get(key) or 0) + (asi.get(key) or 0)

    stats = {
        "str": total("str"), "dex": total("dex"), "con": total("con"),
        "int": total("int"), "wis": total("wis"), "cha": total("cha"),
    }
    modifiers = {k: _modifier(v) for k, v in stats.items()}

    prof_bonus = "+2"
    hp = char_dict.get("hp_max") or "—"
    ac = "—"
    speed = char_dict.get("speed") or "30"

    # Derive AC from equipped armor
    for eq in char_dict.get("equipment", []):
        if eq.get("equipped") and eq.get("name") and "armor" in eq["name"].lower():
            pass  # Simplified; full AC calc can be added in Phase 2

    context = {
        "char": char_dict,
        "stats": stats,
        "modifiers": modifiers,
        "prof_bonus": prof_bonus,
        "hp": hp,
        "ac": ac,
        "speed": speed,
        "class_obj": class_obj,
        "species_obj": species_obj,
        "background_obj": background_obj,
        "static_dir": Path(settings.static_dir).as_uri(),
    }

    html_str = template.render(**context)
    css_path = Path(settings.static_dir) / "style.css"
    extra_css = CSS(filename=str(css_path)) if css_path.exists() else None

    base_url = Path(settings.static_dir).as_uri() + "/"
    pdf_bytes = HTML(string=html_str, base_url=base_url).write_pdf(
        stylesheets=[extra_css] if extra_css else []
    )
    return pdf_bytes


def render_character_html(char_dict: dict, class_obj=None, species_obj=None, background_obj=None) -> str:
    env = _get_jinja_env()
    template = env.get_template("character_sheet.html")

    attrs = char_dict.get("base_attributes") or {}
    asi = char_dict.get("background_asi") or {}

    def total(key):
        return (attrs.get(key) or 0) + (asi.get(key) or 0)

    stats = {
        "str": total("str"), "dex": total("dex"), "con": total("con"),
        "int": total("int"), "wis": total("wis"), "cha": total("cha"),
    }
    modifiers = {k: _modifier(v) for k, v in stats.items()}

    context = {
        "char": char_dict,
        "stats": stats,
        "modifiers": modifiers,
        "prof_bonus": "+2",
        "hp": char_dict.get("hp_max") or "—",
        "ac": "—",
        "speed": char_dict.get("speed") or "30",
        "class_obj": class_obj,
        "species_obj": species_obj,
        "background_obj": background_obj,
        "static_dir": "/static",
    }
    return template.render(**context)
