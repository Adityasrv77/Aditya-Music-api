from flask import Flask, request, redirect, jsonify, json, g
import time
import jiosaavn
import os
from traceback import print_exc
from flask_cors import CORS
from response_helper import success_response, error_response, pagination_meta
from cache import clear_cache

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET", 'thankyoutonystark#weloveyou3000')
CORS(app)

# Performance tracking
@app.before_request
def start_timer():
    g.start = time.time()

@app.after_request
def add_header(response):
    # Add performance headers
    if hasattr(g, 'start'):
        response.headers['X-Response-Time'] = f'{time.time() - g.start:.3f}s'
    
    # Caching headers for successful responses
    if response.status_code == 200:
        response.headers['Cache-Control'] = 'public, max-age=300'  # 5 minutes
    
    return response

@app.route('/')
def home():
    return redirect("https://cyberboysumanjay.github.io/JioSaavnAPI/")

@app.route('/cache/clear')
def clear_cached_data():
    """Clear all cached data (admin endpoint)"""
    clear_cache()
    return success_response({}, "Cache cleared successfully")

# NEW CLEAN ENDPOINTS
@app.route('/v2/songs/search')
def search_songs_clean():
    try:
        query = request.args.get('query', '').strip()
        page = max(1, request.args.get('page', 1, type=int))
        limit = min(request.args.get('limit', 20, type=int), 50)
        include_lyrics = request.args.get('lyrics', 'false').lower() == 'true'
        
        if not query:
            return error_response("Query parameter is required", 400)
        
        results = jiosaavn.search_for_song_clean(query, page, limit)
        
        # Add lyrics if requested
        if include_lyrics:
            for song in results:
                if song.get('lyrics_id'):
                    song['lyrics'] = jiosaavn.get_lyrics(song['lyrics_id'])
        
        meta = pagination_meta(page, limit, len(results))
        return success_response(results, "Songs retrieved successfully", meta)
        
    except Exception as e:
        return error_response("Search failed", 500, str(e))

@app.route('/v2/songs/<song_id>')
def get_song_clean_endpoint(song_id):
    try:
        include_lyrics = request.args.get('lyrics', 'false').lower() == 'true'
        
        song_data = jiosaavn.get_song_clean(song_id, include_lyrics)
        
        if not song_data:
            return error_response("Song not found", 404)
        
        return success_response(song_data, "Song details retrieved")
        
    except Exception as e:
        return error_response("Failed to fetch song", 500, str(e))

@app.route('/v2/lyrics/<lyrics_id>')
def get_lyrics_clean(lyrics_id):
    try:
        lyrics = jiosaavn.get_lyrics(lyrics_id)
        
        response_data = {
            "lyrics_id": lyrics_id,
            "content": lyrics,
            "has_lyrics": bool(lyrics and lyrics.strip())
        }
        
        return success_response(response_data, "Lyrics retrieved")
        
    except Exception as e:
        return error_response("Failed to fetch lyrics", 500, str(e))

@app.route('/v2/albums/<album_id>')
def get_album_clean_endpoint(album_id):
    try:
        include_lyrics = request.args.get('lyrics', 'false').lower() == 'true'
        
        album_data = jiosaavn.get_album_clean(album_id, include_lyrics)
        
        if not album_data:
            return error_response("Album not found", 404)
        
        return success_response(album_data, "Album details retrieved")
        
    except Exception as e:
        return error_response("Failed to fetch album", 500, str(e))

@app.route('/v2/playlists/<playlist_id>')
def get_playlist_clean_endpoint(playlist_id):
    try:
        include_lyrics = request.args.get('lyrics', 'false').lower() == 'true'
        
        playlist_data = jiosaavn.get_playlist_clean(playlist_id, include_lyrics)
        
        if not playlist_data:
            return error_response("Playlist not found", 404)
        
        return success_response(playlist_data, "Playlist details retrieved")
        
    except Exception as e:
        return error_response("Failed to fetch playlist", 500, str(e))

# LEGACY ENDPOINTS (for backward compatibility)
@app.route('/song/')
def search():
    lyrics = False
    songdata = True
    query = request.args.get('query')
    lyrics_ = request.args.get('lyrics')
    songdata_ = request.args.get('songdata')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    fast = request.args.get('fast', 'false')
    
    if lyrics_ and lyrics_.lower() != 'false':
        lyrics = True
    if songdata_ and songdata_.lower() != 'true':
        songdata = False
        
    if query:
        if fast.lower() == 'true':
            return jsonify(jiosaavn.search_for_song_fast(query, page, limit))
        else:
            return jsonify(jiosaavn.search_for_song(query, lyrics, songdata, page, limit))
    else:
        error = {
            "status": False,
            "error": 'Query is required to search songs!'
        }
        return jsonify(error)

@app.route('/song/get/')
def get_song():
    lyrics = False
    id = request.args.get('id')
    lyrics_ = request.args.get('lyrics')
    if lyrics_ and lyrics_.lower() != 'false':
        lyrics = True
    if id:
        resp = jiosaavn.get_song(id, lyrics)
        if not resp:
            error = {
                "status": False,
                "error": 'Invalid Song ID received!'
            }
            return jsonify(error)
        else:
            return jsonify(resp)
    else:
        error = {
            "status": False,
            "error": 'Song ID is required to get a song!'
        }
        return jsonify(error)

@app.route('/playlist/')
def playlist():
    lyrics = False
    query = request.args.get('query')
    lyrics_ = request.args.get('lyrics')
    if lyrics_ and lyrics_.lower() != 'false':
        lyrics = True
    if query:
        id = jiosaavn.get_playlist_id(query)
        songs = jiosaavn.get_playlist(id, lyrics)
        return jsonify(songs)
    else:
        error = {
            "status": False,
            "error": 'Query is required to search playlists!'
        }
        return jsonify(error)

@app.route('/album/')
def album():
    lyrics = False
    query = request.args.get('query')
    lyrics_ = request.args.get('lyrics')
    if lyrics_ and lyrics_.lower() != 'false':
        lyrics = True
    if query:
        id = jiosaavn.get_album_id(query)
        songs = jiosaavn.get_album(id, lyrics)
        return jsonify(songs)
    else:
        error = {
            "status": False,
            "error": 'Query is required to search albums!'
        }
        return jsonify(error)

@app.route('/lyrics/')
def lyrics():
    query = request.args.get('query')

    if query:
        try:
            if 'http' in query and 'saavn' in query:
                id = jiosaavn.get_song_id(query)
                lyrics = jiosaavn.get_lyrics(id)
            else:
                lyrics = jiosaavn.get_lyrics(query)
            response = {}
            response['status'] = True
            response['lyrics'] = lyrics
            return jsonify(response)
        except Exception as e:
            error = {
                "status": False,
                "error": str(e)
            }
            return jsonify(error)

    else:
        error = {
            "status": False,
            "error": 'Query containing song link or id is required to fetch lyrics!'
        }
        return jsonify(error)

@app.route('/result/')
def result():
    lyrics = False
    query = request.args.get('query')
    lyrics_ = request.args.get('lyrics')
    if lyrics_ and lyrics_.lower() != 'false':
        lyrics = True

    if 'saavn' not in query:
        return jsonify(jiosaavn.search_for_song_fast(query, 1, 20))
    try:
        if '/song/' in query:
            song_id = jiosaavn.get_song_id(query)
            song = jiosaavn.get_song(song_id, lyrics)
            return jsonify(song)

        elif '/album/' in query:
            id = jiosaavn.get_album_id(query)
            songs = jiosaavn.get_album(id, lyrics)
            return jsonify(songs)

        elif '/playlist/' in query or '/featured/' in query:
            id = jiosaavn.get_playlist_id(query)
            songs = jiosaavn.get_playlist(id, lyrics)
            return jsonify(songs)

    except Exception as e:
        print_exc()
        error = {
            "status": True,
            "error": str(e)
        }
        return jsonify(error)
    return None

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5100, use_reloader=True, threaded=True)
