
from flask import Flask, render_template, jsonify, request
import requests
import sqlite3
import os
import random 

app = Flask(__name__)
DATABASE = 'games.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/free')
def free():
    return render_template('freetoplay.html')

@app.route('/populategames', methods=['GET'])
def games():
    conn = get_db_connection()
    conn.execute('DELETE FROM games')
    games_exist = conn.execute('SELECT COUNT(*) FROM games').fetchone()[0] > 0
    
    if not games_exist:
        # Fetch and store games from Steam
        response = requests.get('https://api.steampowered.com/ISteamApps/GetAppList/v2/')
        steam_games = response.json()['applist']['apps']
        
        for game in steam_games:
            if game.get('name', '').strip():
                name = game['name']
                appid = game['appid']
                url = f"https://store.steampowered.com/app/{appid}/"
                icon_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"
                conn.execute('INSERT INTO games (name, appid, url, icon_url, source) VALUES (?, ?, ?, ?, ?)',
                             (name, appid, url, icon_url, 'steam'))

        # Fetch and store games from FreeToGame
        response = requests.get('https://www.freetogame.com/api/games')
        free_games = response.json()
        
        for game in free_games:
            if game.get('title', '').strip():
                name = game['title']
                appid = game['id']
                url = game['game_url']
                icon_url = game['thumbnail']
                conn.execute('INSERT INTO games (name, appid, url, icon_url, source) VALUES (?, ?, ?, ?, ?)',
                             (name, appid, url, icon_url, 'freetogame'))

        conn.commit()

    conn.close()
    return jsonify({"message": "Games data fetched and stored successfully"})

@app.route('/gameslist', methods=['GET'])
def games_list():
    page = int(request.args.get('page', 1))
    per_page = 100
    start = (page - 1) * per_page

    conn = get_db_connection()
    games = conn.execute('SELECT * FROM games ORDER BY name LIMIT ? OFFSET ?', (per_page, start)).fetchall()
    total_game_count = conn.execute('SELECT COUNT(*) FROM games').fetchone()[0]
    conn.close()

    games_with_links = [{
        'name': game['name'],
        'appid': game['appid'],
        'url': game['url'],
        'icon_url': game['icon_url']
    } for game in games]

    response_data = {
        "total_game_amount": total_game_count,
        "games": games_with_links
    }

    return jsonify(response_data)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    conn = get_db_connection()
    games = conn.execute("SELECT * FROM games WHERE name LIKE ? LIMIT 100", ('%' + query + '%',)).fetchall()
    conn.close()

    games_list = [{
        'name': game['name'],
        'appid': game['appid'],
        'url': game['url'],
        'icon_url': game['icon_url']
    } for game in games]

    return jsonify(games_list)

@app.route('/randomgame', methods=['GET'])
def random_game():
    conn = get_db_connection()
    random_game = conn.execute('SELECT * FROM games ORDER BY RANDOM() LIMIT 1').fetchone()
    conn.close()
    
    if random_game:
        game_data = {
            'name': random_game['name'],
            'appid': random_game['appid'],
            'url': random_game['url'],
            'icon_url': random_game['icon_url']
        }
        return jsonify(game_data)
    else:
        return jsonify({"message": "No games found in the database"})

@app.route('/freegames', methods=['GET'])
def free_games():
    page = int(request.args.get('page', 1))
    per_page = 100
    start = (page - 1) * per_page

    conn = get_db_connection()
    games = conn.execute('SELECT * FROM games WHERE source = "freetogame" ORDER BY name LIMIT ? OFFSET ?', (per_page, start)).fetchall()
    total_free_game_count = conn.execute('SELECT COUNT(*) FROM games WHERE source = "freetogame"').fetchone()[0]
    conn.close()
    
    games_with_links = [{
        'name': game['name'],
        'appid': game['appid'],
        'url': game['url'],
        'icon_url': game['icon_url']
    } for game in games]

    response_data = {
        "total_free_game_amount": total_free_game_count,
        "games": games_with_links
    }

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(host='192.168.0.39', port=25565, debug=True)