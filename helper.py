import base64
import jiosaavn
from pyDes import *

def format_song_clean(data):
    """Transform song data to clean format"""
    try:
        # Get media URL with fallback
        media_url = data.get('media_url')
        if not media_url or 'preview' in media_url:
            try:
                media_url = decrypt_url(data.get('encrypted_media_url', ''))
            except:
                media_url = None
        
        # If still no media URL, try to convert from preview
        if not media_url:
            preview_url = data.get('media_preview_url', '')
            if preview_url:
                media_url = preview_url.replace("preview", "aac").replace("_96_p.mp4", "_160.mp4")
        
        # Ensure best available quality
        if media_url and data.get('320kbps') != "true" and "_320.mp4" in media_url:
            media_url = media_url.replace("_320.mp4", "_160.mp4")
    
    except Exception as e:
        print(f"Media URL error: {e}")
        media_url = data.get('media_preview_url', '').replace("preview", "aac").replace("_96_p.mp4", "_160.mp4")
    
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
        "copyright": format(data.get('copyright_text', '')).replace("&copy;", "©"),
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

def format(string):
    return string.encode().decode().replace("&quot;", "'").replace("&amp;", "&").replace("&#039;", "'")

def decrypt_url(url):
    des_cipher = des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
    enc_url = base64.b64decode(url.strip())
    dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode('utf-8')
    dec_url = dec_url.replace("_96.mp4", "_320.mp4")
    return dec_url

# Legacy functions for backward compatibility
def format_song(data, lyrics):
    clean_data = format_song_clean(data)
    if lyrics and clean_data.get('lyrics_id'):
        clean_data['lyrics'] = jiosaavn.get_lyrics(clean_data['lyrics_id'])
    return clean_data

def format_album(data, lyrics):
    data['image'] = data['image'].replace("150x150", "500x500")
    data['name'] = format(data['name'])
    data['primary_artists'] = format(data['primary_artists'])
    data['title'] = format(data['title'])
    for song in data['songs']:
        song = format_song(song, lyrics)
    return data

def format_playlist(data, lyrics):
    data['firstname'] = format(data['firstname'])
    data['listname'] = format(data['listname'])
    for song in data['songs']:
        song = format_song(song, lyrics)
    return data
