import os
import random
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from database import engine, characters, classes, species
from sqlalchemy import select, update, insert, join
from pydantic import BaseModel
from typing import Optional, Dict

# 1. Load Secrets
load_dotenv()
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
# ... rest of code ...
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_ID = os.getenv("ADMIN_DISCORD_ID")

app = FastAPI()

# 2. Add Session Middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# --- MATH HELPERS ---
def roll_4d6_drop_lowest():
    rolls = [random.randint(1, 6) for _ in range(4)]
    rolls.sort()
    return sum(rolls[1:])

def generate_stat_block():
    return [roll_4d6_drop_lowest() for _ in range(6)]

def generate_triple_set():
    return [generate_stat_block(), generate_stat_block(), generate_stat_block()]

# --- MODELS ---
class RollRequest(BaseModel):
    character_name: str

class CharacterSelection(BaseModel):
    chosen_set_index: int
    class_id: int
    species_id: int
    attributes: Dict[str, int]

class AdminAction(BaseModel):
    target_discord_id: str

# --- AUTH ROUTES ---

@app.get("/login")
def login():
    """Redirects user to Discord for approval"""
    discord_login_url = (
        f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify"
    )
    return RedirectResponse(discord_login_url)

@app.get("/auth/callback")
async def auth_callback(code: str, request: Request):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return JSONResponse({"error": "Failed to get access token"}, status_code=400)

        user_resp = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = user_resp.json()
    
    request.session["user"] = {
        "id": user_data["id"],
        "username": user_data["username"]
    }
    
    return RedirectResponse("/static/index.html")

@app.get("/auth/me")
def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"authenticated": False})
    
    # Check if this user matches the Admin ID in .env
    is_admin = (str(user["id"]) == str(ADMIN_ID))
    
    return JSONResponse({
        "authenticated": True, 
        "user": user,
        "is_admin": is_admin # <--- Send this to frontend
    })

@app.get("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/static/index.html")

# --- VIEW ROUTE (Character Sheet) ---
@app.get("/my-character")
def get_my_character(request: Request):
    """
    Returns the logged-in user's character data (if it exists),
    joined with Class and Species names.
    """
    user = request.session.get("user")
    if not user:
        return JSONResponse({"found": False})

    with engine.connect() as conn:
        # Join Characters -> Classes and Characters -> Species
        j = characters.join(classes, characters.c.class_id == classes.c.id, isouter=True) \
                      .join(species, characters.c.species_id == species.c.id, isouter=True)
        
        query = select(
            characters.c.character_name,
            characters.c.attributes,
            classes.c.name.label("class_name"),
            classes.c.hit_die,
            species.c.name.label("species_name"),
            species.c.speed,
            species.c.size
        ).select_from(j).where(characters.c.discord_id == user["id"])

        result = conn.execute(query).fetchone()
        
        if result:
            return JSONResponse({"found": True, "data": dict(result._mapping)})
        else:
            return JSONResponse({"found": False})

# --- GAME ROUTES (Creation) ---

@app.post("/roll-stats/")
def roll_stats(request: Request, roll_req: RollRequest):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    discord_id = user["id"]

    with engine.connect() as conn:
        query = select(characters).where(characters.c.discord_id == discord_id)
        result = conn.execute(query).fetchone()

        if result:
            if result.is_locked:
                return {"message": "Stats already generated.", "pool": result.stat_pool, "locked": True}
            else:
                new_pool = generate_triple_set()
                stmt = update(characters).where(characters.c.discord_id == discord_id).values(
                    stat_pool=new_pool, 
                    is_locked=True,
                    character_name=roll_req.character_name
                )
                conn.execute(stmt)
                conn.commit()
                return {"message": "Reroll granted!", "pool": new_pool}
        else:
            pool = generate_triple_set()
            stmt = characters.insert().values(
                discord_id=discord_id, 
                character_name=roll_req.character_name, 
                stat_pool=pool, 
                is_locked=True
            )
            conn.execute(stmt)
            conn.commit()
            return {"message": "Welcome!", "pool": pool}

@app.post("/confirm-selection/")
def confirm_selection(request: Request, selection: CharacterSelection):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    discord_id = user["id"]

    with engine.connect() as conn:
        stmt = update(characters).where(
            characters.c.discord_id == discord_id
        ).values(
            chosen_set=selection.chosen_set_index,
            class_id=selection.class_id,
            species_id=selection.species_id,
            attributes=selection.attributes,
            is_locked=True
        )
        conn.execute(stmt)
        conn.commit()
        return {"status": "success", "message": "Character saved successfully!"}

@app.get("/options/classes")
def get_classes():
    with engine.connect() as conn:
        result = conn.execute(select(classes)).fetchall()
        return [dict(row._mapping) for row in result]

@app.get("/options/species")
def get_species():
    with engine.connect() as conn:
        result = conn.execute(select(species)).fetchall()
        return [dict(row._mapping) for row in result]

# --- ADMIN ROUTES ---

@app.get("/admin/dashboard")
def admin_dashboard(request: Request): # Add request
    # Security Check
    user = request.session.get("user")
    if not user or str(user["id"]) != str(ADMIN_ID):
        raise HTTPException(status_code=403, detail="Admins only!")

    with engine.connect() as conn:
        j = characters.join(classes, characters.c.class_id == classes.c.id, isouter=True) \
                      .join(species, characters.c.species_id == species.c.id, isouter=True)
        
        query = select(
            characters.c.discord_id,
            characters.c.character_name,
            characters.c.stat_pool,
            characters.c.chosen_set,
            characters.c.is_locked,
            characters.c.attributes,
            classes.c.name.label("class_name"),
            species.c.name.label("species_name")
        ).select_from(j)
        
        results = conn.execute(query).fetchall()
        return [dict(row._mapping) for row in results]

@app.post("/admin/unlock-player")
def unlock_player(request: Request, action: AdminAction): # Add request
    # Security Check
    user = request.session.get("user")
    if not user or str(user["id"]) != str(ADMIN_ID):
        raise HTTPException(status_code=403, detail="Admins only!")

    with engine.connect() as conn:
        stmt = update(characters).where(
            characters.c.discord_id == action.target_discord_id
        ).values(
            is_locked=False,
            chosen_set=None,
            class_id=None,
            species_id=None,
            attributes=None
        )
        conn.execute(stmt)
        conn.commit()
        return {"status": "success", "message": f"Player {action.target_discord_id} unlocked."}

# --- STARTUP SEEDING ---
@app.on_event("startup")
async def startup_event():
    with engine.connect() as conn:
        # Seed Classes
        if not conn.execute(select(classes)).fetchall():
            print("Seeding Classes...")
            class_list = [
                {"name": "Barbarian", "hit_die": 12, "primary_ability": "Strength", "description": "A fierce warrior."},
                {"name": "Bard", "hit_die": 8, "primary_ability": "Charisma", "description": "An inspiring magician."},
                {"name": "Cleric", "hit_die": 8, "primary_ability": "Wisdom", "description": "A priestly champion."},
                {"name": "Druid", "hit_die": 8, "primary_ability": "Wisdom", "description": "A priest of the Old Faith."},
                {"name": "Fighter", "hit_die": 10, "primary_ability": "Strength/Dexterity", "description": "A master of martial combat."},
                {"name": "Monk", "hit_die": 8, "primary_ability": "Dexterity/Wisdom", "description": "A master of martial arts."},
                {"name": "Paladin", "hit_die": 10, "primary_ability": "Strength/Charisma", "description": "A holy warrior."},
                {"name": "Ranger", "hit_die": 10, "primary_ability": "Dexterity/Wisdom", "description": "A warrior of nature."},
                {"name": "Rogue", "hit_die": 8, "primary_ability": "Dexterity", "description": "A scoundrel."},
                {"name": "Sorcerer", "hit_die": 6, "primary_ability": "Charisma", "description": "Inherited magic."},
                {"name": "Warlock", "hit_die": 8, "primary_ability": "Charisma", "description": "Pact magic."},
                {"name": "Wizard", "hit_die": 6, "primary_ability": "Intelligence", "description": "Scholarly magic."}
            ]
            conn.execute(insert(classes), class_list)
            conn.commit()

        # Seed Species
        if not conn.execute(select(species)).fetchall():
            print("Seeding Species...")
            species_list = [
                {"name": "Human", "speed": 30, "size": "Medium", "description": "Versatile."},
                {"name": "Elf", "speed": 30, "size": "Medium", "description": "Magical."},
                {"name": "Dwarf", "speed": 25, "size": "Medium", "description": "Hardy."},
                {"name": "Halfling", "speed": 25, "size": "Small", "description": "Nimble."},
                {"name": "Dragonborn", "speed": 30, "size": "Medium", "description": "Draconic."},
                {"name": "Gnome", "speed": 25, "size": "Small", "description": "Inventive."},
                {"name": "Tiefling", "speed": 30, "size": "Medium", "description": "Infernal."},
                {"name": "Orc", "speed": 30, "size": "Medium", "description": "Strong."}
            ]
            conn.execute(insert(species), species_list)
            conn.commit()