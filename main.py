from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests

import os

if os.getenv("RENDER") != "True":    #loads this if running local for testing, but when deployed api key is injected
    from dotenv import load_dotenv    
    load_dotenv()


app = FastAPI()
templates = Jinja2Templates(directory ='templates')

API_KEY = os.getenv("API_KEY")
HEADERS = {"Authorization": API_KEY}

@app.get("/", response_class=HTMLResponse)    # app.get("/") means run this when the website loads
def form_get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/", response_class=HTMLResponse)    # @app.post("/") means run when form is submitted (submitting player id)
def form_post(request: Request, tag: str = Form(...)):
    tag = tag.upper()   # capitalizes input
    url = f'https://api.clashroyale.com/v1/players/%23{tag}'    #uses %23 as URL encoding for "#" to auto add it
    res = requests.get(url, headers=HEADERS)    # makes a GET request to clash royale API

    if res.status_code != 200:    # status code 200 means success
        return templates.TemplateResponse("index.html", {"request": request, "error": "Invalid tag or API error"})
    
    player_data = res.json()

    #winrate implementation:
    wins = player_data.get("wins", 0)
    losses = player_data.get("losses", 0)

    if wins + losses > 0:
        winrate = round(100 * wins / (wins + losses),2)
    else:
        winrate = None


    return templates.TemplateResponse("index.html", {
        "request": request, 
        "player": player_data, 
        "winrate": winrate    #add winrate here so the html can get it
        })