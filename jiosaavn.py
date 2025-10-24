import requests
import endpoints
import helper
import json
from traceback import print_exc
import re


def search_for_song(query, lyrics, songdata, page=1, limit=20):
    if query.startswith('http') and 'saavn.com' in query:
        id = get_song_id(query)
        return get_song(id, lyrics)

    # Use proper search endpoint with pagination
    search_base_url = endpoints.search_songs_base_url.format(page=page, limit=limit) + query
    response = requests.get(search_base_url).text.encode().decode('unicode-escape')
    pattern = r'\(From "([^"]+)"\)'
    response = json.loads(re.sub(pattern, r"(From '\1')", response))
    
    # Get all songs from search results
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
    """Fast search without individual song API calls"""
    search_base_url = endpoints.search_songs_base_url.format(page=page, limit=limit) + query
    response = requests.get(search_base_url).text.encode().decode('unicode-escape')
    pattern = r'\(From "([^"]+)"\)'
    response = json.loads(re.sub(pattern, r"(From '\1')", response))
    
    if 'results' in response:
        results = response['results']
    else:
        results = []
    
    # Basic formatting without individual API calls
    formatted_results = []
    for song in results:
        formatted_song = {
            'id': song.get('id'),
            'title': helper.format(song.get('title', '')),
            'singers': helper.format(song.get('singers', '')),
            'album': helper.format(song.get('album', '')),
            'duration': song.get('duration'),
            'image': song.get('image', '').replace("150x150", "500x500"),
            'media_url': song.get('media_preview_url', ''),
            'perma_url': song.get('perma_url', ''),
            'language': song.get('language', ''),
            'year': song.get('year', ''),
            'primary_artists': helper.format(song.get('primary_artists', '')),
            'has_lyrics': song.get('has_lyrics', 'false')
        }
        formatted_results.append(formatted_song)
    
    return {
        "page": page,
        "limit": limit,
        "total": len(formatted_results),
        "results": formatted_results
    }


def get_song(id, lyrics):
    try:
        song_details_base_url = endpoints.song_details_base_url + id
        song_response = requests.get(
            song_details_base_url).text.encode().decode('unicode-escape')
        song_response = json.loads(song_response)
        song_data = helper.format_song(song_response[id], lyrics)
        if song_data:
            return song_data
    except:
        return None


def get_song_id(url):
    res = requests.get(url, data=[('bitrate', '320')])
    try:
        return(res.text.split('"pid":"'))[1].split('","')[0]
    except IndexError:
        return res.text.split('"song":{"type":"')[1].split('","image":')[0].split('"id":"')[-1]


def get_album(album_id, lyrics):
    songs_json = []
    try:
        response = requests.get(endpoints.album_details_base_url + album_id)
        if response.status_code == 200:
            songs_json = response.text.encode().decode('unicode-escape')
            songs_json = json.loads(songs_json)
            return helper.format_album(songs_json, lyrics)
    except Exception as e:
        print(e)
        return None


def get_album_id(input_url):
    res = requests.get(input_url)
    try:
        return res.text.split('"album_id":"')[1].split('"')[0]
    except IndexError:
        return res.text.split('"page_id","')[1].split('","')[0]


def get_playlist(listId, lyrics):
    try:
        response = requests.get(endpoints.playlist_details_base_url + listId)
        if response.status_code == 200:
            songs_json = response.text.encode().decode('unicode-escape')
            songs_json = json.loads(songs_json)
            return helper.format_playlist(songs_json, lyrics)
        return None
    except Exception:
        print_exc()
        return None


def get_playlist_id(input_url):
    res = requests.get(input_url).text
    try:
        return res.split('"type":"playlist","id":"')[1].split('"')[0]
    except IndexError:
        return res.split('"page_id","')[1].split('","')[0]


def get_lyrics(id):
    url = endpoints.lyrics_base_url + id
    lyrics_json = requests.get(url).text
    lyrics_text = json.loads(lyrics_json)
    return lyrics_text['lyrics']
