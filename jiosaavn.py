from cache import cache_response

@cache_response(ttl=600)  # Cache for 10 minutes
def search_for_song_clean(query, page=1, limit=20):
    """Fast search with clean output format"""
    search_url = endpoints.search_songs_base_url.format(page=page, limit=limit) + query
    response = requests.get(search_url, timeout=10).text.encode().decode('unicode-escape')
    
    # Clean the response
    pattern = r'\(From "([^"]+)"\)'
    response = json.loads(re.sub(pattern, r"(From '\1')", response))
    
    results = response.get('results', [])
    clean_results = []
    
    for song in results:
        clean_song = helper.format_song_clean(song)
        if clean_song.get('media_url'):
            clean_results.append(clean_song)
    
    return clean_results

@cache_response(ttl=1800)  # Cache for 30 minutes
def get_song_clean(song_id, include_lyrics=False):
    """Get song details in clean format"""
    try:
        url = endpoints.song_details_base_url + song_id
        response = requests.get(url, timeout=10).text.encode().decode('unicode-escape')
        song_data = json.loads(response).get(song_id)
        
        if not song_data:
            return None
        
        clean_data = helper.format_song_clean(song_data)
        
        # Add lyrics if requested
        if include_lyrics and clean_data.get('lyrics_id'):
            clean_data['lyrics'] = get_lyrics(clean_data['lyrics_id'])
        
        return clean_data
        
    except Exception as e:
        print(f"Error fetching song {song_id}: {str(e)}")
        return None
