D&D Campaign Character Creator

A local web application for rolling D&D 5e stats (4d6 drop lowest), assigning attributes, and saving characters to a database. Features Discord OAuth2 for secure login and an Admin Dashboard for the DM.

Features

Discord Login: Secure authentication using OAuth2.

Stat Roller: Generates 3 distinct sets of stats using the "4d6 Drop Lowest" algorithm.

Anti-Cheese: Locks the dice roll to the user's account to prevent infinite rerolls.

Character Management: Users can view their created character sheet.

DM Dashboard: Admin (DM) can view all characters and unlock/reset players who need to reroll.

Setup Instructions

1. Prerequisites

Python 3.10+

A Discord Developer Application (for Client ID/Secret)

2. Installation

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy aiosqlite python-dotenv httpx itsdangerous


3. Configuration (.env)

Create a file named .env in the root directory:

DISCORD_CLIENT_ID=your_client_id_here
DISCORD_CLIENT_SECRET=your_client_secret_here
DISCORD_REDIRECT_URI=[http://127.0.0.1:8000/auth/callback](http://127.0.0.1:8000/auth/callback)
SECRET_KEY=any_random_string_for_security
ADMIN_DISCORD_ID=your_numeric_discord_id


Note: To get your Admin ID, enable Developer Mode in Discord and right-click your username -> Copy User ID.

4. Running the App

uvicorn main:app --reload


Home: https://www.google.com/search?q=http://127.0.0.1:8000/static/index.html

Admin: https://www.google.com/search?q=http://127.0.0.1:8000/static/admin.html (Only accessible if logged in as Admin)

Database

The project uses campaign.db (SQLite).
To reset the database structure (e.g. after code updates):

Stop the server.

Delete campaign.db.

Restart the server (it will auto-seed Classes and Species).