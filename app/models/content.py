from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class LorePage(Base):
    __tablename__ = "lore_pages"
    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    content_md = Column(Text, nullable=False)
    player_visible = Column(Boolean, default=False, nullable=False)
    category = Column(String, default="world", nullable=False)


class Species(Base):
    __tablename__ = "species"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    creature_type = Column(String, default="Humanoid")
    size_options = Column(JSON)          # ["Medium"] or ["Medium", "Small"]
    speed = Column(Integer, default=30)
    traits = Column(JSON)                # [{"name": "...", "description": "..."}]
    lineages = Column(JSON)              # [{"name": "...", "description": "...", "level3_spell"?: "...", "level5_spell"?: "..."}]
    source = Column(String, default="PHB 2024")
    is_homebrew = Column(Boolean, default=False)


class DnDClass(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    hit_die = Column(Integer, nullable=False)
    primary_abilities = Column(JSON)     # ["Strength", "Dexterity"]
    saving_throws = Column(JSON)
    armor_proficiencies = Column(JSON)
    weapon_proficiencies = Column(JSON)
    skill_choices = Column(Integer, default=2)
    skill_options = Column(JSON)
    tool_proficiencies = Column(JSON, nullable=True)    # e.g. ["Thieves' Tools"] or ["3 Musical Instruments of your choice"]
    spellcasting_type = Column(String, nullable=True)   # "full", "half", "pact"
    spellcasting_ability = Column(String, nullable=True)
    equipment_options = Column(JSON)    # [{"label":"A","items":[...]},{"label":"B","gold":75}]
    features = Column(JSON)             # [{"name":"...","level":1,"description":"...","choice_required":false,"choice_key":null,"options":[]}]
    source = Column(String, default="PHB 2024")
    is_homebrew = Column(Boolean, default=False)

    subclasses = relationship("Subclass", back_populates="dnd_class")


class Subclass(Base):
    __tablename__ = "subclasses"
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    name = Column(String, nullable=False)
    unlock_level = Column(Integer, default=3)
    description = Column(Text)
    features = Column(JSON)             # [{"name":"...","level":3,"description":"..."}]
    source = Column(String, default="PHB 2024")
    is_homebrew = Column(Boolean, default=False)

    dnd_class = relationship("DnDClass", back_populates="subclasses")


class Background(Base):
    __tablename__ = "backgrounds"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    ability_score_options = Column(JSON)  # ["Intelligence", "Wisdom", "Charisma"]
    origin_feat_name = Column(String)
    skill_proficiencies = Column(JSON)
    tool_proficiency = Column(String, nullable=True)
    language_count = Column(Integer, default=0)
    equipment_options = Column(JSON)    # [{"label":"A","items":[...]},{"label":"B","gold":50}]
    description = Column(Text)
    source = Column(String, default="PHB 2024")
    is_homebrew = Column(Boolean, default=False)


class Feat(Base):
    __tablename__ = "feats"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)  # "origin","general","fighting_style","epic_boon"
    prerequisites = Column(JSON, nullable=True)
    description = Column(Text)
    source = Column(String, default="PHB 2024")
    is_homebrew = Column(Boolean, default=False)


class Spell(Base):
    __tablename__ = "spells"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    level = Column(Integer, nullable=False)
    school = Column(String)
    casting_time = Column(String)
    spell_range = Column(String)
    components = Column(String)
    duration = Column(String)
    concentration = Column(Boolean, default=False)
    ritual = Column(Boolean, default=False)
    classes = Column(JSON)              # ["Sorcerer", "Wizard"]
    description = Column(Text)
    source = Column(String, default="PHB 2024")
    is_homebrew = Column(Boolean, default=False)


class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"
    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    term = Column(String, nullable=False)
    category = Column(String, nullable=False)   # weapon_property|mastery|skill|action|condition|combat
    short_description = Column(Text, nullable=False)
    full_description = Column(Text, nullable=False)
    ability = Column(String, nullable=True)      # only used by skills
    source = Column(String, default="PHB 2024")


class Equipment(Base):
    __tablename__ = "equipment"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    item_type = Column(String)          # "weapon","armor","shield","gear","tool","focus","pack"
    category = Column(String, nullable=True)  # "Simple Melee","Martial Ranged","Light","Medium","Heavy"
    cost = Column(String, nullable=True)
    weight = Column(String, nullable=True)
    # Weapon fields
    damage = Column(String, nullable=True)
    damage_type = Column(String, nullable=True)
    properties = Column(JSON, nullable=True)
    mastery_property = Column(String, nullable=True)
    # Armor fields
    ac_formula = Column(String, nullable=True)  # "11 + Dex","13 + Dex (max 2)","16"
    strength_req = Column(Integer, nullable=True)
    stealth_disadvantage = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    source = Column(String, default="PHB 2024")
    is_homebrew = Column(Boolean, default=False)
