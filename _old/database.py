import os
import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, JSON, Boolean, Text, ForeignKey

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./campaign.db")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

metadata = MetaData()

# 1. Characters
characters = Table(
    "characters",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("discord_id", String, unique=True, index=True),
    Column("character_name", String),
    Column("background", String, nullable=True),
    Column("alignment", String, nullable=True),
    Column("bio", Text, nullable=True),
    Column("stat_pool", JSON),
    Column("chosen_set", Integer, nullable=True),
    Column("is_locked", Boolean, default=True),
    Column("species_id", Integer, nullable=True),
    Column("class_id", Integer, nullable=True),
    Column("attributes", JSON, nullable=True),
    Column("level", Integer, default=1),
    Column("hp_max", Integer, default=10),
)

# 2. Classes
classes = Table(
    "classes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True),
    Column("hit_die", Integer), 
    Column("primary_ability", String),
    Column("description", Text),
    Column("flavor_text", Text, nullable=True),
    Column("spellcasting_ability", String, nullable=True)
)

# 3. Species
species = Table(
    "species",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True),
    Column("speed", Integer),
    Column("size", String),
    Column("description", Text),
    Column("flavor_text", Text, nullable=True)
)

# 4. Spells
spells = Table(
    "spells",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True),
    Column("level", Integer),
    Column("school", String),
    Column("casting_time", String),
    Column("range", String),
    Column("components", String),
    Column("duration", String),
    Column("description", Text),
    Column("classes_allowed", JSON)
)

# 5. Character Known Spells (UPDATED)
character_spells = Table(
    "character_spells",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("character_discord_id", String, ForeignKey("characters.discord_id")),
    Column("spell_id", Integer, ForeignKey("spells.id")),
    Column("prepared", Boolean, default=False) # <--- NEW: Tracks memorized spells
)

# 6. Class Features
class_features = Table(
    "class_features",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("class_id", Integer, ForeignKey("classes.id")),
    Column("level_required", Integer),
    Column("name", String),
    Column("description", Text)
)

# 7. Feature Options
feature_options = Table(
    "feature_options",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("feature_id", Integer, ForeignKey("class_features.id")),
    Column("name", String),
    Column("description", Text)
)

# 8. Character Choices
character_choices = Table(
    "character_choices",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("character_discord_id", String, ForeignKey("characters.discord_id")),
    Column("feature_id", Integer, ForeignKey("class_features.id")),
    Column("option_id", Integer, ForeignKey("feature_options.id"))
)

engine = create_engine(DATABASE_URL)
metadata.create_all(engine)