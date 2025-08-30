from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
import re
from typing import Optional

import os

if os.getenv("RENDER") != "True":
    from dotenv import load_dotenv    
    load_dotenv()


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory ='templates')

API_KEY = os.getenv("API_KEY")
HEADERS = {"Authorization": API_KEY}

def validate_player_tag(tag: str) -> str:
    """Validate and clean player tag input"""
    if not tag:
        raise ValueError("Player tag cannot be empty")
    
    tag = tag.strip().upper()
    
    # Remove # if present
    if tag.startswith('#'):
        tag = tag[1:]
    
    # Check if tag contains only valid characters (letters and numbers)
    if not re.match(r'^[A-Z0-9]+$', tag):
        raise ValueError("Player tag contains invalid characters")
    
    # Check length (CR tags are typically 8-9 characters)
    if len(tag) < 3 or len(tag) > 12:
        raise ValueError("Player tag must be between 3-12 characters")
    
    return tag

def get_player_data(tag: str) -> dict:
    """Fetch player data from API with error handling"""
    if not API_KEY:
        raise ValueError("API key not configured")
    
    url = f'https://proxy.royaleapi.dev/v1/players/%23{tag}'
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        
        if res.status_code == 404:
            raise ValueError("Player not found - please check the tag")
        elif res.status_code == 403:
            raise ValueError("API access denied - check API key")
        elif res.status_code == 429:
            raise ValueError("Too many requests - please try again later")
        elif res.status_code != 200:
            raise ValueError(f"API error: {res.status_code}")
        
        return res.json()
    
    except requests.exceptions.Timeout:
        raise ValueError("Request timed out - please try again")
    except requests.exceptions.ConnectionError:
        raise ValueError("Connection error - please check your internet")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Request failed: {str(e)}")

def calculate_winrate(wins: int, losses: int) -> Optional[float]:
    """Calculate win rate percentage"""
    if wins + losses > 0:
        return round(100 * wins / (wins + losses), 2)
    return None

@app.get("/", response_class=HTMLResponse)    # app.get("/") means run this when the website loads
def form_get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
def form_post(request: Request, tag: str = Form(...)):
    try:
        # Validate and clean the tag
        clean_tag = validate_player_tag(tag)
        
        # Fetch player data
        player_data = get_player_data(clean_tag)
        
        # Calculate win rate
        wins = player_data.get("wins", 0)
        losses = player_data.get("losses", 0)
        winrate = calculate_winrate(wins, losses)
        
        # Calculate additional stats
        level = player_data.get("expLevel", 0)
        exp_points = player_data.get("expPoints", 0)
        total_donations = player_data.get("totalDonations", 0)
        
        # Get clan info if available
        clan_info = player_data.get("clan")
        
        # Get current deck
        current_deck = player_data.get("currentDeck", [])
        
        # Get favourite card
        favourite_card = player_data.get("currentFavouriteCard")
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "player": player_data,
            "winrate": winrate,
            "level": level,
            "exp_points": exp_points,
            "total_donations": total_donations,
            "clan_info": clan_info,
            "current_deck": current_deck,
            "favourite_card": favourite_card
        })
    
    except ValueError as e:
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": str(e)
        })
    except Exception as e:
        # Log the actual error for debugging
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": f"An unexpected error occurred: {str(e)}"
        })