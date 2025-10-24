import requests
import endpoints
import helper
import json
from traceback import print_exc
import re
from cache import cache_response

@cache_response(ttl=600)  # Cache for 10 minutes
def search_for_song_clean(query, page=1, limit=20):
    """Fast search with clean output format"""
    try:
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
    except Exception as e:
        print(f"Search error: {e}")
        return []

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

@cache_response(ttl=3600)  # Cache for 1 hour
def get_lyrics(lyrics_id):
    try:
        url = endpoints.lyrics_base_url + lyrics_id
        lyrics_json = requests.get(url, timeout=10).text
        lyrics_text = json.loads(lyrics_json)
        return lyrics_text.get('lyrics', '')
    except Exception as e:
        print(f"Lyrics error: {e}")
        return ''

@cache_response(ttl=1800)
def get_album_clean(album_id, include_lyrics=False):
    """Get album details in clean format"""
    try:
        response = requests.get(endpoints.album_details_base_url + album_id, timeout=10)
        if response.status_code == 200:
            songs_json = response.text.encode().decode('unicode-escape')
            album_data = json.loads(songs_json)
            
            # Transform album data
            album_data['image'] = album_data.get('image', '').replace("150x150", "500x500")
            album_data['name'] = helper.format(album_data.get('name', ''))
            album_data['title'] = helper.format(album_data.get('title', ''))
            
            # Transform songs
            clean_songs = []
            for song in album_data.get('songs', []):
                clean_song = helper.format_song_clean(song)
                if include_lyrics and clean_song.get('lyrics_id'):
                    clean_song['lyrics'] = get_lyrics(clean_song['lyrics_id'])
                clean_songs.append(clean_song)
            
            album_data['songs'] = clean_songs
            return album_data
        return None
    except Exception as e:
        print(f"Album error: {e}")
        return None

@cache_response(ttl=1800)
def get_playlist_clean(playlist_id, include_lyrics=False):
    """Get playlist details in clean format"""
    try:
        response = requests.get(endpoints.playlist_details_base_url + playlist_id, timeout=10)
        if response.status_code == 200:
            songs_json = response.text.encode().decode('unicode-escape')
            playlist_data = json.loads(songs_json)
            
            # Transform playlist data
            playlist_data['firstname'] = helper.format(playlist_data.get('firstname', ''))
            playlist_data['listname'] = helper.format(playlist_data.get('listname', ''))
            
            # Transform songs
            clean_songs = []
            for song in playlist_data.get('songs', []):
                clean_song = helper.format_song_clean(song)
                if include_lyrics and clean_song.get('lyrics_id'):
                    clean_song['lyrics'] = get_lyrics(clean_song['lyrics_id'])
                clean_songs.append(clean_song)
            
            playlist_data['songs'] = clean_songs
            return playlist_data
        return None
    except Exception as e:
        print_exc()
        return None

# Legacy functions for backward compatibility
def search_for_song(query, lyrics, songdata, page=1, limit=20):
    if query.startswith('http') and 'saavn.com' in query:
        id = get_song_id(query)
        return get_song(id, lyrics)

    search_base_url = endpoints.search_songs_base_url.format(page=page, limit=limit) + query
    response = requests.get(search_base_url).text.encode().decode('unicode-escape')
    pattern = r'\(From "([^"]+)"\)'
    response = json.loads(re.sub(pattern, r"(From '\1')", response))
    
    if 'results' in response:
        song_response = response['results']
    else:
        song_response = []
    
    if not songdata:
        return {
            "page": page,
            "limit": limit,
            "total": len(song_response),
            "results": song_response
        }
    
    songs = []
    for song in song_response:
        id = song['id']
        song_data = get_song(id, lyrics)
        if song_data:
            songs.append(song_data)
    
    return {
        "page": page,
        "limit": limit,
        "total": len(songs),
        "results": songs
    }

def search_for_song_fast(query, page=1, limit=30):
    return search_for_song_clean(query, page, limit)

def get_song(id, lyrics):
    return get_song_clean(id, lyrics)

def get_song_id(url):
    res = requests.get(url, data=[('bitrate', '320')])
    try:
        return(res.text.split('"pid":"'))[1].split('","')[0]
    except IndexError:
        return res.text.split('"song":{"type":"')[1].split('","image":')[0].split('"id":"')[-1]

def get_album(album_id, lyrics):
    return get_album_clean(album_id, lyrics)

def get_album_id(input_url):
    res = requests.get(input_url)
    try:
        return res.text.split('"album_id":"')[1].split('"')[0]
    except IndexError:
        return res.text.split('"page_id","')[1].split('","')[0]

def get_playlist(listId, lyrics):
    return get_playlist_clean(listId, lyrics)

def get_playlist_id(input_url):
    res = requests.get(input_url).text
    try:
        return res.split('"type":"playlist","id":"')[1].split('"')[0]
    except IndexError:
        return res.split('"page_id","')[1].split('","')[0]
