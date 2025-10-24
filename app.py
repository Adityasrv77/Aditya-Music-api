from response_helper import success_response, error_response, pagination_meta

@app.route('/v2/songs/search')
def search_songs_clean():
    try:
        query = request.args.get('query', '').strip()
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', 20, type=int), 50)  # Max 50 per page
        include_lyrics = request.args.get('lyrics', 'false').lower() == 'true'
        
        if not query:
            return error_response("Query parameter is required", 400)
        
        # Fast search with clean format
        results = jiosaavn.search_for_song_clean(query, page, limit)
        
        meta = pagination_meta(page, limit, len(results))
        return success_response(results, "Songs retrieved successfully", meta)
        
    except Exception as e:
        return error_response("Search failed", 500, str(e))

@app.route('/v2/songs/<song_id>')
def get_song_clean(song_id):
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
