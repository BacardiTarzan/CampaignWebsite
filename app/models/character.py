from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON, func
from sqlalchemy.orm import relationship
from ..database import Base


class Character(Base):
    __tablename__ = "characters"
    id = Column(Integer, primary_key=True)
    created_by_display_name = Column(String, nullable=False)
    character_name = Column(String, nullable=False)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=True)
    background_id = Column(Integer, ForeignKey("backgrounds.id"), nullable=True)
    alignment = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    base_attributes = Column(JSON, nullable=True)  # {"str":15,"dex":14,"con":13,"int":12,"wis":10,"cha":8}
    background_asi = Column(JSON, nullable=True)   # {"str":2,"wis":1} or {"int":1,"wis":1,"cha":1}
    hp_max = Column(Integer, nullable=True)
    hp_current = Column(Integer, nullable=True)
    speed = Column(Integer, nullable=True)
    equipment_choice = Column(JSON, nullable=True)  # {"class": "A", "background": "A"}
    tool_proficiency_choice = Column(String, nullable=True)  # resolved tool when background offers a choice
    species_lineage = Column(String, nullable=True)          # e.g. "Drow", "Wood Elf", "Black" (dragon)
    species_size_choice = Column(String, nullable=True)      # "Medium" or "Small" when species offers a choice
    spell_slots_used = Column(JSON, nullable=True)           # {"1": 2, "2": 0} slots expended per level
    owner_email = Column(String, nullable=True)
    stat_roll_locked = Column(Boolean, default=False)
    wizard_step = Column(Integer, default=1)
    is_complete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    species = relationship("Species")
    background = relationship("Background")
    character_classes = relationship("CharacterClass", back_populates="character", cascade="all, delete-orphan")
    stat_roll_sets = relationship("StatRollSet", back_populates="character", cascade="all, delete-orphan")
    choices = relationship("CharacterChoice", back_populates="character", cascade="all, delete-orphan")
    feats = relationship("CharacterFeat", back_populates="character", cascade="all, delete-orphan")
    spells = relationship("CharacterSpell", back_populates="character", cascade="all, delete-orphan")
    equipment = relationship("CharacterEquipment", back_populates="character", cascade="all, delete-orphan")
    skill_proficiencies = relationship("SkillProficiency", back_populates="character", cascade="all, delete-orphan")
    tool_proficiencies = relationship("ToolProficiency", back_populates="character", cascade="all, delete-orphan")
    language_proficiencies = relationship("LanguageProficiency", back_populates="character", cascade="all, delete-orphan")
    weapon_mastery_unlocks = relationship("WeaponMasteryUnlock", back_populates="character", cascade="all, delete-orphan")


class CharacterClass(Base):
    __tablename__ = "character_classes"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    level = Column(Integer, default=1)
    subclass_id = Column(Integer, ForeignKey("subclasses.id"), nullable=True)
    hit_dice_remaining = Column(Integer, default=1)

    character = relationship("Character", back_populates="character_classes")
    dnd_class = relationship("DnDClass")
    subclass = relationship("Subclass")


class StatRollSet(Base):
    __tablename__ = "stat_roll_sets"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    rolls = Column(JSON)       # [15, 14, 13, 12, 10, 8]
    is_manual = Column(Boolean, default=False)
    selected = Column(Boolean, default=False)

    character = relationship("Character", back_populates="stat_roll_sets")


class CharacterChoice(Base):
    __tablename__ = "character_choices"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    feature_key = Column(String, nullable=False)  # "fighting_style","divine_order","weapon_mastery_1"
    choice_value = Column(JSON)                   # "Archery" or ["Archery","Defense"]

    character = relationship("Character", back_populates="choices")


class CharacterFeat(Base):
    __tablename__ = "character_feats"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    feat_id = Column(Integer, ForeignKey("feats.id"), nullable=False)
    source = Column(String)   # "background","species","asi"

    character = relationship("Character", back_populates="feats")
    feat = relationship("Feat")


class CharacterSpell(Base):
    __tablename__ = "character_spells"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    spell_id = Column(Integer, ForeignKey("spells.id"), nullable=False)
    prepared = Column(Boolean, default=True)
    source_class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    source = Column(String, nullable=True)   # "class" | "species"
    notes = Column(Text, nullable=True)      # special casting rules (e.g. limited no-slot casts)

    character = relationship("Character", back_populates="spells")
    spell = relationship("Spell")
    source_class = relationship("DnDClass")


class CharacterEquipment(Base):
    __tablename__ = "character_equipment"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    custom_name = Column(String, nullable=True)
    quantity = Column(Integer, default=1)
    equipped = Column(Boolean, default=False)

    character = relationship("Character", back_populates="equipment")
    equipment_item = relationship("Equipment")


class SkillProficiency(Base):
    __tablename__ = "skill_proficiencies"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    source = Column(String)   # "class","background","species","feat"
    expertise = Column(Boolean, default=False)

    character = relationship("Character", back_populates="skill_proficiencies")


class ToolProficiency(Base):
    __tablename__ = "tool_proficiencies"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    tool_name = Column(String, nullable=False)
    source = Column(String)

    character = relationship("Character", back_populates="tool_proficiencies")


class LanguageProficiency(Base):
    __tablename__ = "language_proficiencies"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    language_name = Column(String, nullable=False)
    source = Column(String)

    character = relationship("Character", back_populates="language_proficiencies")


class WeaponMasteryUnlock(Base):
    __tablename__ = "weapon_mastery_unlocks"
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    weapon_name = Column(String, nullable=False)

    character = relationship("Character", back_populates="weapon_mastery_unlocks")
