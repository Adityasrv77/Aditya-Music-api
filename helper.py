def format_song_clean(data):
    """Transform song data to clean format"""
    try:
        # Get media URL with fallback
        media_url = data.get('media_url')
        if not media_url or 'preview' in media_url:
            media_url = decrypt_url(data.get('encrypted_media_url', ''))
        
        # Ensure best available quality
        if data.get('320kbps') != "true" and "_320.mp4" in media_url:
            media_url = media_url.replace("_320.mp4", "_160.mp4")
    
    except Exception:
        # Fallback to preview URL conversion
        preview_url = data.get('media_preview_url', '')
        media_url = preview_url.replace("preview", "aac").replace("_96_p.mp4", "_160.mp4")
    
    # Clean and format all fields
    return {
        "id": data.get('id'),
        "song": format(data.get('song', '')),
        "artists": extract_artists(data),
        "album": format(data.get('album', '')),
        "year": data.get('year', ''),
        "language": data.get('language', ''),
        "duration_sec": convert_duration(data.get('duration', '0')),
        "play_count": safe_int(data.get('play_count', 0)),
        "image": data.get('image', '').replace("150x150", "500x500"),
        "media_url": media_url,
        "perma_url": data.get('perma_url', ''),
        "copyright": data.get('copyright_text', '').replace("&copy;", "©"),
        "lyrics_id": data.get('lyrics_id') if data.get('has_lyrics') == 'true' else None
    }

def extract_artists(data):
    """Extract and clean artists array"""
    artists = []
    
    # Try primary artists first
    primary = data.get('primary_artists', '')
    if primary:
        artists.extend([format(artist.strip()) for artist in primary.split(',') if artist.strip()])
    
    # Fallback to singers
    if not artists:
        singers = data.get('singers', '')
        if singers:
            artists.extend([format(singer.strip()) for singer in singers.split(',') if singer.strip()])
    
    # Remove duplicates and empty values
    return list(dict.fromkeys([a for a in artists if a]))

def convert_duration(duration_str):
    """Convert duration string to seconds"""
    try:
        if ':' in duration_str:
            parts = duration_str.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return int(duration_str)
    except:
        return 0

def safe_int(value, default=0):
    """Safely convert to integer"""
    try:
        return int(value)
    except:
        return default
