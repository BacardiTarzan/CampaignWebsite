import os
import json
import random
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from database import engine, characters, classes, species, spells, character_spells, class_features, feature_options, character_choices
from sqlalchemy import select, update, insert, join, and_, delete
from pydantic import BaseModel
from typing import Optional, Dict, List

# 1. Load Secrets
load_dotenv()
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_ID = os.getenv("ADMIN_DISCORD_ID")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# --- MODELS (Keep all existing models) ---
class RollRequest(BaseModel):
    character_name: str

class CharacterSelection(BaseModel):
    chosen_set_index: int
    class_id: int
    species_id: int
    attributes: Dict[str, int]
    background: str
    alignment: str
    bio: str

class AdminAction(BaseModel):
    target_discord_id: str

class SpellLearnRequest(BaseModel):
    spell_id: int

class FeatureSelectRequest(BaseModel):
    feature_id: int
    option_id: int

class SpellCreate(BaseModel):
    name: str
    level: int
    school: str
    casting_time: str
    range: str
    components: str
    duration: str
    description: str
    classes_allowed: List[str]

class SpeciesCreate(BaseModel):
    name: str
    speed: int
    size: str
    description: str
    flavor_text: str 

class ClassCreate(BaseModel):
    name: str
    hit_die: int
    primary_ability: str
    spellcasting_ability: Optional[str] = None
    description: str
    flavor_text: str 

class SpellToggleRequest(BaseModel):
    spell_id: int
    prepared: bool

# --- MATH HELPERS (Keep existing) ---
def roll_4d6_drop_lowest():
    rolls = [random.randint(1, 6) for _ in range(4)]
    rolls.sort()
    return sum(rolls[1:])

def generate_stat_block():
    return [roll_4d6_drop_lowest() for _ in range(6)]

def generate_triple_set():
    return [generate_stat_block(), generate_stat_block(), generate_stat_block()]

# --- AUTH ROUTES (Keep existing) ---
@app.get("/login")
def login():
    return RedirectResponse(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify")

@app.get("/auth/callback")
async def auth_callback(code: str, request: Request):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post("https://discord.com/api/oauth2/token", data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI}, headers={"Content-Type": "application/x-www-form-urlencoded"})
        access_token = token_resp.json().get("access_token")
        if not access_token: return JSONResponse({"error": "Failed"}, status_code=400)
        user_resp = await client.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {access_token}"})
        user_data = user_resp.json()
    request.session["user"] = {"id": user_data["id"], "username": user_data["username"]}
    return RedirectResponse("/static/index.html")

@app.get("/auth/me")
def get_current_user(request: Request):
    user = request.session.get("user")
    if not user: return JSONResponse({"authenticated": False})
    return JSONResponse({"authenticated": True, "user": user, "is_admin": (str(user["id"]) == str(ADMIN_ID))})

@app.get("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/static/index.html")

# --- CHARACTER ROUTES (Keep existing) ---
@app.get("/my-character")
def get_my_character(request: Request):
    user = request.session.get("user")
    if not user: return JSONResponse({"found": False})

    with engine.connect() as conn:
        j = characters.join(classes, characters.c.class_id == classes.c.id, isouter=True) \
                      .join(species, characters.c.species_id == species.c.id, isouter=True)
        
        query = select(
            characters.c.character_name, characters.c.attributes, characters.c.level, characters.c.hp_max,
            characters.c.class_id,
            characters.c.background, characters.c.alignment, characters.c.bio,
            classes.c.name.label("class_name"), classes.c.hit_die, classes.c.spellcasting_ability,
            species.c.name.label("species_name"), species.c.speed
        ).select_from(j).where(characters.c.discord_id == user["id"])

        result = conn.execute(query).fetchone()
        
        if result and result.class_id is not None:
            char_data = dict(result._mapping)
            
            # Fetch Features
            feats_query = select(class_features).where(and_(class_features.c.class_id == char_data['class_id'], class_features.c.level_required <= char_data['level']))
            raw_features = [dict(r._mapping) for r in conn.execute(feats_query).fetchall()]
            features_list = []
            for f in raw_features:
                opts = [dict(r._mapping) for r in conn.execute(select(feature_options).where(feature_options.c.feature_id == f["id"])).fetchall()]
                choice = conn.execute(select(feature_options).join(character_choices, character_choices.c.option_id == feature_options.c.id).where(and_(character_choices.c.character_discord_id == user["id"], character_choices.c.feature_id == f["id"]))).fetchone()
                f["options"] = opts
                f["selected"] = dict(choice._mapping) if choice else None
                features_list.append(f)
            char_data['features'] = features_list

            # Fetch Spells WITH Prepared Status
            # Note: We join character_spells to spells, selecting the 'prepared' column from the link table
            spells_j = character_spells.join(spells, character_spells.c.spell_id == spells.c.id)
            spells_query = select(spells, character_spells.c.prepared).select_from(spells_j).where(character_spells.c.character_discord_id == user["id"])
            
            char_data['spells'] = [dict(row._mapping) for row in conn.execute(spells_query).fetchall()]

            return JSONResponse({"found": True, "data": char_data})
        else:
            return JSONResponse({"found": False})
        
@app.post("/prepare-spell")
def prepare_spell(request: Request, payload: SpellToggleRequest):
    user = request.session.get("user")
    if not user: raise HTTPException(401)
    
    with engine.connect() as conn:
        # Update the specific row
        conn.execute(update(character_spells).where(and_(
            character_spells.c.character_discord_id == user["id"],
            character_spells.c.spell_id == payload.spell_id
        )).values(prepared=payload.prepared))
        conn.commit()
    return {"status": "success"}

@app.post("/select-feature")
def select_feature(request: Request, payload: FeatureSelectRequest):
    user = request.session.get("user")
    if not user: raise HTTPException(401)
    with engine.connect() as conn:
        conn.execute(delete(character_choices).where(and_(character_choices.c.character_discord_id == user["id"], character_choices.c.feature_id == payload.feature_id)))
        conn.execute(insert(character_choices).values(character_discord_id=user["id"], feature_id=payload.feature_id, option_id=payload.option_id))
        conn.commit()
    return {"status": "success"}

@app.get("/available-spells")
def get_available_spells(request: Request):
    user = request.session.get("user")
    if not user: return JSONResponse([])
    with engine.connect() as conn:
        char = conn.execute(select(characters, classes.c.name.label("class_name")).join(classes, characters.c.class_id == classes.c.id).where(characters.c.discord_id == user["id"])).fetchone()
        if not char: return JSONResponse([])
        max_spell_level = (char.level + 1) // 2 
        all_spells = conn.execute(select(spells)).fetchall()
        valid_spells = []
        for s in all_spells:
            if s.level <= max_spell_level and char.class_name in s.classes_allowed:
                valid_spells.append(dict(s._mapping))
        return JSONResponse(valid_spells)

@app.post("/learn-spell")
def learn_spell(request: Request, payload: SpellLearnRequest):
    user = request.session.get("user")
    if not user: raise HTTPException(401)
    with engine.connect() as conn:
        exists = conn.execute(select(character_spells).where(and_(character_spells.c.character_discord_id == user["id"], character_spells.c.spell_id == payload.spell_id))).fetchone()
        if not exists:
            conn.execute(insert(character_spells).values(character_discord_id=user["id"], spell_id=payload.spell_id))
            conn.commit()
    return {"status": "success"}

@app.post("/forget-spell")
def forget_spell(request: Request, payload: SpellLearnRequest):
    user = request.session.get("user")
    if not user: raise HTTPException(401)
    with engine.connect() as conn:
        conn.execute(delete(character_spells).where(and_(character_spells.c.character_discord_id == user["id"], character_spells.c.spell_id == payload.spell_id)))
        conn.commit()
    return {"status": "success"}

@app.get("/options/class-details/{class_id}")
def get_class_details(class_id: int):
    with engine.connect() as conn:
        cls = conn.execute(select(classes).where(classes.c.id == class_id)).fetchone()
        if not cls: raise HTTPException(404, "Class not found")
        
        feats_query = select(class_features).where(and_(class_features.c.class_id == class_id, class_features.c.level_required == 1))
        raw_feats = [dict(r._mapping) for r in conn.execute(feats_query).fetchall()]
        features_data = []
        for f in raw_feats:
            opts = [dict(r._mapping) for r in conn.execute(select(feature_options).where(feature_options.c.feature_id == f["id"])).fetchall()]
            f["options"] = opts
            features_data.append(f)

        spells_data = []
        if cls.spellcasting_ability:
            all_spells = conn.execute(select(spells).where(spells.c.level <= 1)).fetchall()
            for s in all_spells:
                if cls.name in s.classes_allowed:
                    spells_data.append(dict(s._mapping))

        return {"features": features_data, "spells": spells_data, "spellcasting_ability": cls.spellcasting_ability}

@app.post("/roll-stats/")
def roll_stats(request: Request, roll_req: RollRequest):
    user = request.session.get("user")
    if not user: raise HTTPException(401)
    discord_id = user["id"]
    with engine.connect() as conn:
        res = conn.execute(select(characters).where(characters.c.discord_id == discord_id)).fetchone()
        if res and res.is_locked:
             return {"message": "Stats already generated.", "pool": res.stat_pool, "locked": True}
        
        pool = generate_triple_set()
        if res: conn.execute(update(characters).where(characters.c.discord_id == discord_id).values(stat_pool=pool, is_locked=True, character_name=roll_req.character_name))
        else: conn.execute(insert(characters).values(discord_id=discord_id, character_name=roll_req.character_name, stat_pool=pool, is_locked=True))
        conn.commit()
        return {"pool": pool}

@app.post("/confirm-selection/")
def confirm_selection(request: Request, selection: CharacterSelection):
    user = request.session.get("user")
    if not user: raise HTTPException(401)
    with engine.connect() as conn:
        class_info = conn.execute(select(classes).where(classes.c.id == selection.class_id)).fetchone()
        con_score = selection.attributes.get("Constitution", 10)
        con_mod = (con_score - 10) // 2
        hp = class_info.hit_die + con_mod
        
        conn.execute(update(characters).where(characters.c.discord_id == user["id"]).values(
            chosen_set=selection.chosen_set_index, class_id=selection.class_id, species_id=selection.species_id, 
            attributes=selection.attributes, is_locked=True, level=1, hp_max=hp,
            background=selection.background, alignment=selection.alignment, bio=selection.bio
        ))
        conn.commit()
    return {"status": "success"}

# --- OPTIONS ROUTES FOR FRONTEND  ---
@app.get("/options/classes")
def get_classes():
    with engine.connect() as conn: return [dict(r._mapping) for r in conn.execute(select(classes)).fetchall()]

@app.get("/options/species")
def get_species():
    with engine.connect() as conn: return [dict(r._mapping) for r in conn.execute(select(species)).fetchall()]

@app.get("/options/species/{id}")
def get_single_species(id: int):
    with engine.connect() as conn:
        res = conn.execute(select(species).where(species.c.id == id)).fetchone()
        if not res: raise HTTPException(404)
        return dict(res._mapping)

@app.get("/options/class/{id}")
def get_single_class(id: int):
    with engine.connect() as conn:
        res = conn.execute(select(classes).where(classes.c.id == id)).fetchone()
        if not res: raise HTTPException(404)
        return dict(res._mapping)

# --- ADMIN ROUTES ---
@app.post("/admin/add-spell")
def add_spell(request: Request, spell: SpellCreate):
    user = request.session.get("user")
    if not user or str(user["id"]) != str(ADMIN_ID): raise HTTPException(403)
    with engine.connect() as conn:
        if conn.execute(select(spells).where(spells.c.name == spell.name)).fetchone(): return JSONResponse({"status": "error", "message": "Exists!"})
        conn.execute(insert(spells).values(name=spell.name, level=spell.level, school=spell.school, casting_time=spell.casting_time, range=spell.range, components=spell.components, duration=spell.duration, description=spell.description, classes_allowed=spell.classes_allowed))
        conn.commit()
    return {"status": "success", "message": f"Added {spell.name}"}

@app.post("/admin/add-species")
def add_species(request: Request, sp: SpeciesCreate):
    user = request.session.get("user")
    if not user or str(user["id"]) != str(ADMIN_ID): raise HTTPException(403)
    with engine.connect() as conn:
        if conn.execute(select(species).where(species.c.name == sp.name)).fetchone(): return JSONResponse({"status": "error", "message": "Exists!"})
        conn.execute(insert(species).values(name=sp.name, speed=sp.speed, size=sp.size, description=sp.description, flavor_text=sp.flavor_text))
        conn.commit()
    return {"status": "success", "message": f"Added {sp.name}"}

@app.post("/admin/add-class")
def add_class(request: Request, cl: ClassCreate):
    user = request.session.get("user")
    if not user or str(user["id"]) != str(ADMIN_ID): raise HTTPException(403)
    with engine.connect() as conn:
        if conn.execute(select(classes).where(classes.c.name == cl.name)).fetchone(): return JSONResponse({"status": "error", "message": "Exists!"})
        conn.execute(insert(classes).values(name=cl.name, hit_die=cl.hit_die, primary_ability=cl.primary_ability, spellcasting_ability=cl.spellcasting_ability, description=cl.description, flavor_text=cl.flavor_text))
        conn.commit()
    return {"status": "success", "message": f"Added {cl.name}"}

@app.get("/admin/list-spells")
def list_all_spells(request: Request):
    user = request.session.get("user")
    if not user or str(user["id"]) != str(ADMIN_ID): raise HTTPException(403)
    with engine.connect() as conn: return [dict(r._mapping) for r in conn.execute(select(spells).order_by(spells.c.level, spells.c.name)).fetchall()]

@app.post("/admin/level-up")
def level_up_player(request: Request, action: AdminAction):
    user = request.session.get("user")
    if not user or str(user["id"]) != str(ADMIN_ID): raise HTTPException(403)
    with engine.connect() as conn:
        char = conn.execute(select(characters, classes.c.hit_die).join(classes, characters.c.class_id == classes.c.id).where(characters.c.discord_id == action.target_discord_id)).fetchone()
        if char:
            con_mod = (char.attributes["Constitution"] - 10) // 2
            hp_gain = (char.hit_die // 2) + 1 + con_mod
            if hp_gain < 1: hp_gain = 1
            new_level = char.level + 1
            new_hp = char.hp_max + hp_gain
            conn.execute(update(characters).where(characters.c.discord_id == action.target_discord_id).values(level=new_level, hp_max=new_hp))
            conn.commit()
            return {"status": "success", "new_level": new_level}
    return {"status": "error"}

@app.post("/admin/unlock-player")
def unlock_player(request: Request, action: AdminAction):
    user = request.session.get("user")
    if not user or str(user["id"]) != str(ADMIN_ID): raise HTTPException(403)
    with engine.connect() as conn:
        conn.execute(update(characters).where(characters.c.discord_id == action.target_discord_id).values(is_locked=False, chosen_set=None, class_id=None, species_id=None, attributes=None, level=1, background=None, alignment=None, bio=None))
        conn.execute(delete(character_spells).where(character_spells.c.character_discord_id == action.target_discord_id))
        conn.execute(delete(character_choices).where(character_choices.c.character_discord_id == action.target_discord_id))
        conn.commit()
    return {"status": "success"}

@app.post("/admin/delete-player")
def delete_player(request: Request, action: AdminAction):
    user = request.session.get("user")
    if not user or str(user["id"]) != str(ADMIN_ID): raise HTTPException(403)
    with engine.connect() as conn:
        conn.execute(delete(character_spells).where(character_spells.c.character_discord_id == action.target_discord_id))
        conn.execute(delete(character_choices).where(character_choices.c.character_discord_id == action.target_discord_id))
        conn.execute(delete(characters).where(characters.c.discord_id == action.target_discord_id))
        conn.commit()
    return {"status": "success"}

@app.get("/admin/dashboard")
def admin_dashboard(request: Request):
    user = request.session.get("user")
    if not user or str(user["id"]) != str(ADMIN_ID): raise HTTPException(403)
    with engine.connect() as conn:
        j = characters.join(classes, characters.c.class_id == classes.c.id, isouter=True).join(species, characters.c.species_id == species.c.id, isouter=True)
        query = select(characters.c.discord_id, characters.c.character_name, characters.c.level, characters.c.stat_pool, characters.c.chosen_set, characters.c.is_locked, characters.c.attributes, classes.c.name.label("class_name"), species.c.name.label("species_name")).select_from(j)
        return [dict(r._mapping) for r in conn.execute(query).fetchall()]

# --- STARTUP SEEDING ---
@app.on_event("startup")
async def startup_event():
    with engine.connect() as conn:
        # Check if we need to seed
        if not conn.execute(select(classes)).fetchall():
            print("Database empty. Seeding from srd_data.json...")
            try:
                with open("srd_data.json", "r") as f:
                    data = json.load(f)
                    
                    # Seed Classes
                    if "classes" in data:
                        conn.execute(insert(classes), data["classes"])
                    
                    # Seed Species
                    if "species" in data:
                        conn.execute(insert(species), data["species"])
            except FileNotFoundError:
                print("srd_data.json not found! Skipping seed.")
            
            # Seed Spells (Keeping some hardcoded default logic in case JSON is small, or you can move these to JSON too)
            # For now, let's keep the basic hardcoded spells/features as fallback or foundational data
            # ... (Your existing hardcoded spells/features logic here if you want mixed seeding) ...
            # But cleanest is to move ALL to JSON eventually. 
            # For now, I will preserve the hardcoded spells/features logic from previous version as fallback 
            # since they are not in the JSON sample above yet.
            
            spell_list = [
                {"name": "Light", "level": 0, "school": "Evocation", "casting_time": "1 Action", "range": "Touch", "components": "V, M", "duration": "1 Hour", "description": "Object shines like a torch.", "classes_allowed": ["Bard", "Cleric", "Wizard"]},
                {"name": "Mage Hand", "level": 0, "school": "Conjuration", "casting_time": "1 Action", "range": "30 feet", "components": "V, S", "duration": "1 Minute", "description": "Spectral hand moves objects.", "classes_allowed": ["Bard", "Wizard"]},
                {"name": "Fire Bolt", "level": 0, "school": "Evocation", "casting_time": "1 Action", "range": "120 feet", "components": "V, S", "duration": "Instant", "description": "1d10 Fire damage.", "classes_allowed": ["Wizard"]},
                {"name": "Cure Wounds", "level": 1, "school": "Evocation", "casting_time": "1 Action", "range": "Touch", "components": "V, S", "duration": "Instant", "description": "Heals 1d8 + Mod.", "classes_allowed": ["Bard", "Cleric", "Ranger"]},
                {"name": "Magic Missile", "level": 1, "school": "Evocation", "casting_time": "1 Action", "range": "120 feet", "components": "V, S", "duration": "Instant", "description": "3 darts deal 1d4+1 force each.", "classes_allowed": ["Wizard"]},
                {"name": "Shield", "level": 1, "school": "Abjuration", "casting_time": "Reaction", "range": "Self", "components": "V, S", "duration": "1 Round", "description": "+5 AC vs attacks.", "classes_allowed": ["Wizard"]},
            ]
            conn.execute(insert(spells), spell_list)

            cls_map = {r.name: r.id for r in conn.execute(select(classes)).fetchall()}
            # Hardcoding features for now as they rely on IDs which is tricky in JSON without logic
            # Ideally, JSON should have "class_name" instead of ID and we map it here.
            if "Fighter" in cls_map:
                conn.execute(insert(class_features).values(class_id=cls_map["Fighter"], level_required=1, name="Fighting Style", description="Choose a specialization."))
                fs_id = conn.execute(select(class_features).where(class_features.c.name == "Fighting Style")).fetchone().id
                opts = [
                    {"feature_id": fs_id, "name": "Archery", "description": "+2 bonus to attack rolls made with ranged weapons."},
                    {"feature_id": fs_id, "name": "Defense", "description": "+1 bonus to AC while wearing armor."},
                    {"feature_id": fs_id, "name": "Dueling", "description": "+2 damage with single-handed melee weapons."},
                    {"feature_id": fs_id, "name": "Great Weapon Fighting", "description": "Reroll 1 or 2 on damage dice with two-handed weapons."}
                ]
                conn.execute(insert(feature_options), opts)
                
                feat_list = [
                    {"class_id": cls_map["Fighter"], "level_required": 1, "name": "Second Wind", "description": "Regain 1d10+Lvl HP once per rest."},
                    {"class_id": cls_map["Fighter"], "level_required": 2, "name": "Action Surge", "description": "Take one additional action."}
                ]
                conn.execute(insert(class_features), feat_list)
            
            if "Cleric" in cls_map:
                conn.execute(insert(class_features).values(class_id=cls_map["Cleric"], level_required=1, name="Divine Domain", description="Choose your deity's focus."))
                conn.execute(insert(class_features).values(class_id=cls_map["Cleric"], level_required=2, name="Channel Divinity", description="Turn Undead or Domain effect."))
            
            if "Wizard" in cls_map:
                conn.execute(insert(class_features).values(class_id=cls_map["Wizard"], level_required=1, name="Arcane Recovery", description="Regain some spell slots on short rest."))

        conn.commit()