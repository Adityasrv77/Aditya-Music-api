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

# ... (keep all your existing setup code) ...

@app.route('/v2/songs/search')
def search_songs_clean():
    try:
        query = request.args.get('query', '').strip()
        page = max(1, request.args.get('page', 1, type=int))
        limit = min(request.args.get('limit', 20, type=int), 50)
        include_lyrics = request.args.get('lyrics', 'false').lower() == 'true'
        use_scraping = request.args.get('scraping', 'true').lower() == 'true'
        
        if not query:
            return error_response("Query parameter is required", 400)
        
        # Use hybrid search
        results = jiosaavn.search_for_song_clean(query, page, limit, use_scraping)
        
        # Add lyrics if requested
        if include_lyrics:
            for song in results:
                if song.get('lyrics_id'):
                    song['lyrics'] = jiosaavn.get_lyrics(song['lyrics_id'])
        
        meta = pagination_meta(page, limit, len(results))
        return success_response(results, "Songs retrieved successfully", meta)
        
    except Exception as e:
        return error_response("Search failed", 500, str(e))

# ... (keep all your other routes unchanged) ...
