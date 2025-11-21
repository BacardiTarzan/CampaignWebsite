import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, JSON, Boolean, Text

DATABASE_URL = "sqlite:///./campaign.db"

metadata = MetaData()

# 1. The Character Table
characters = Table(
    "characters",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("discord_id", String, unique=True, index=True),
    Column("character_name", String),
    Column("stat_pool", JSON),
    Column("chosen_set", Integer, nullable=True),
    Column("is_locked", Boolean, default=True),
    Column("species_id", Integer, nullable=True),
    Column("class_id", Integer, nullable=True),
    Column("attributes", JSON, nullable=True)
)

# 2. The Classes Table 
classes = Table(
    "classes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True),
    Column("hit_die", Integer), 
    Column("primary_ability", String),
    Column("description", Text)
)

# 3. The Species Table 
species = Table(
    "species",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True),
    Column("speed", Integer),
    Column("size", String),
    Column("description", Text)
)

engine = create_engine(DATABASE_URL)
metadata.create_all(engine)