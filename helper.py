import base64
import requests
from pyDes import *
from bs4 import BeautifulSoup
import json
import re

def format_song_clean(data):
    """Transform song data to clean format - UPDATED FOR HYBRID SEARCH"""
    if not data:
        return None
    
    try:
        # Handle different data structures from API vs scraping
        media_url = data.get('media_url') or data.get('media_preview_url', '')
        
        # Get media URL with fallback
        if not media_url or 'preview' in media_url:
            try:
                encrypted_url = data.get('encrypted_media_url')
                if encrypted_url:
                    media_url = decrypt_url(encrypted_url)
            except:
                media_url = data.get('media_preview_url', '').replace("preview", "aac").replace("_96_p.mp4", "_160.mp4")
        
        # Ensure best available quality
        if media_url and data.get('320kbps') != "true" and "_320.mp4" in media_url:
            media_url = media_url.replace("_320.mp4", "_160.mp4")
        
        # Extract artists properly
        artists = []
        if 'artists' in data and data['artists']:
            if isinstance(data['artists'], list):
                artists = [format(artist) for artist in data['artists'] if artist]
            else:
                artists = [format(data['artists'])]
        elif 'primary_artists' in data and data['primary_artists']:
            artists = [format(artist.strip()) for artist in data['primary_artists'].split(',') if artist.strip()]
        elif 'singers' in data and data['singers']:
            artists = [format(singer.strip()) for singer in data['singers'].split(',') if singer.strip()]
        
        # Remove duplicates
        artists = list(dict.fromkeys(artists))
        
        # Get song title
        song_title = data.get('song') or data.get('title') or ''
        
        # Format duration
        duration_sec = data.get('duration_sec')
        if not duration_sec:
            duration_str = data.get('duration', '0')
            duration_sec = convert_duration(duration_str)
        
        return {
            "id": data.get('id') or data.get('perma_url', '').split('/')[-1] if data.get('perma_url') else str(hash(song_title)),
            "song": format(song_title),
            "artists": artists,
            "album": format(data.get('album', '')),
            "year": data.get('year', ''),
            "language": format(data.get('language', '')).title(),
            "duration_sec": duration_sec,
            "play_count": safe_int(data.get('play_count', 0)),
            "image": data.get('image', '').replace("150x150", "500x500"),
            "media_url": media_url,
            "perma_url": data.get('perma_url', ''),
            "copyright": format(data.get('copyright_text', '')).replace("&copy;", "©").replace("&#169;", "©"),
            "lyrics_id": data.get('lyrics_id') if data.get('has_lyrics') == 'true' else None
        }
    
    except Exception as e:
        print(f"Error formatting song: {e}")
        return None

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
    """Clean and format strings"""
    if not string:
        return ""
    return string.encode().decode('unicode-escape').replace("&quot;", "'").replace("&amp;", "&").replace("&#039;", "'")

def decrypt_url(url):
    """Decrypt encrypted media URL"""
    try:
        des_cipher = des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
        enc_url = base64.b64decode(url.strip())
        dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode('utf-8')
        dec_url = dec_url.replace("_96.mp4", "_320.mp4")
        return dec_url
    except Exception as e:
        print(f"Decryption error: {e}")
        return ""

# WEB SCRAPING FUNCTIONS
def scrape_jiosaavn_search(query):
    """Scrape search results directly from JioSaavn website"""
    url = f"https://www.jiosaavn.com/search/{query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Method 1: Look for JSON data in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                content = script.string
                # Look for initial data
                if '__INITIAL_DATA__' in content:
                    json_match = re.search(r'__INITIAL_DATA__\s*=\s*({.*?});', content)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(1))
                            songs = extract_songs_from_initial_data(data)
                            if songs:
                                return songs
                        except json.JSONDecodeError:
                            continue
        
        # Method 2: Extract from HTML elements
        songs = extract_songs_from_html(soup)
        if songs:
            return songs
            
        return []
        
    except Exception as e:
        print(f"Scraping error: {e}")
        return []

def extract_songs_from_initial_data(data):
    """Extract songs from the initial data JSON"""
    songs = []
    
    try:
        # Navigate through different possible structures
        if 'entities' in data:
            entities = data['entities']
            
            # Look for song entities
            for entity_type, entity_data in entities.items():
                if 'song' in entity_type.lower() or 'track' in entity_type.lower():
                    if isinstance(entity_data, dict):
                        for song_id, song_info in entity_data.items():
                            if isinstance(song_info, dict):
                                song = parse_song_from_entity(song_info, song_id)
                                if song:
                                    songs.append(song)
        
        # Check for direct results
        if 'results' in data:
            results = data['results']
            if isinstance(results, list):
                for item in results:
                    if isinstance(item, dict) and item.get('type') == 'song':
                        song = parse_song_from_search_result(item)
                        if song:
                            songs.append(song)
        
        # Check for topquery results
        if 'topquery' in data and 'results' in data['topquery']:
            for item in data['topquery']['results']:
                song = parse_song_from_search_result(item)
                if song:
                    songs.append(song)
                    
    except Exception as e:
        print(f"Error extracting from initial data: {e}")
    
    return songs

def extract_songs_from_html(soup):
    """Extract songs from HTML elements"""
    songs = []
    
    try:
        # Look for song cards using various class patterns
        song_selectors = [
            '[class*="song"]',
            '[class*="track"]', 
            '[class*="result"]',
            '.song-list',
            '.track-list'
        ]
        
        for selector in song_selectors:
            elements = soup.select(selector)
            for element in elements:
                song = parse_song_from_element(element)
                if song:
                    songs.append(song)
                
    except Exception as e:
        print(f"Error extracting from HTML: {e}")
    
    return songs

def parse_song_from_entity(song_info, song_id):
    """Parse song from entity data"""
    try:
        return {
            'id': song_id,
            'song': song_info.get('title', ''),
            'artists': [artist.get('name', '') for artist in song_info.get('artists', [])],
            'image': song_info.get('image', ''),
            'duration': song_info.get('duration', ''),
            'album': song_info.get('album', {}).get('name', ''),
            'year': song_info.get('year', ''),
            'language': song_info.get('language', ''),
            'perma_url': song_info.get('url', f"https://www.jiosaavn.com/song/{song_id}")
        }
    except:
        return None

def parse_song_from_search_result(item):
    """Parse song from search result item"""
    try:
        return {
            'id': item.get('id', ''),
            'song': item.get('title', item.get('song', '')),
            'artists': [item.get('primary_artists', '')] if isinstance(item.get('primary_artists'), str) else item.get('artists', []),
            'image': item.get('image', ''),
            'duration': item.get('duration', ''),
            'album': item.get('album', ''),
            'year': item.get('year', ''),
            'language': item.get('language', ''),
            'perma_url': item.get('perma_url', item.get('url', ''))
        }
    except:
        return None

def parse_song_from_element(element):
    """Parse song from HTML element"""
    try:
        # Extract data from data attributes
        song_data = element.get('data-song', '{}')
        if song_data:
            try:
                data = json.loads(song_data)
                return {
                    'id': data.get('id', ''),
                    'song': data.get('title', ''),
                    'artists': data.get('artists', []),
                    'image': data.get('image', ''),
                    'duration': data.get('duration', '')
                }
            except:
                pass
                
        # Extract from text content
        title_element = element.find(class_=re.compile(r'title|name', re.I))
        artist_element = element.find(class_=re.compile(r'artist|singer', re.I))
        
        if title_element:
            return {
                'id': element.get('id', ''),
                'song': title_element.get_text(strip=True),
                'artists': [artist_element.get_text(strip=True)] if artist_element else [],
                'image': '',
                'duration': ''
            }
            
    except:
        pass
    
    return None

def remove_duplicate_songs(songs):
    """Remove duplicate songs based on ID and title"""
    seen = set()
    unique_songs = []
    
    for song in songs:
        if not song:
            continue
            
        # Create a unique identifier
        song_id = song.get('id', '')
        song_title = song.get('song', '').lower().strip()
        
        identifier = f"{song_id}_{song_title}" if song_id else song_title
        
        if identifier and identifier not in seen:
            seen.add(identifier)
            unique_songs.append(song)
    
    return unique_songs

# LEGACY FUNCTIONS FOR BACKWARD COMPATIBILITY
def format_song(data, lyrics):
    """Legacy function for backward compatibility"""
    clean_data = format_song_clean(data)
    if clean_data and lyrics and clean_data.get('lyrics_id'):
        # You'll need to import jiosaavn here or handle lyrics differently
        try:
            import jiosaavn
            clean_data['lyrics'] = jiosaavn.get_lyrics(clean_data['lyrics_id'])
        except:
            pass
    return clean_data

def format_album(data, lyrics):
    """Legacy album formatting"""
    if not data:
        return data
        
    data['image'] = data.get('image', '').replace("150x150", "500x500")
    data['name'] = format(data.get('name', ''))
    data['primary_artists'] = format(data.get('primary_artists', ''))
    data['title'] = format(data.get('title', ''))
    
    if 'songs' in data:
        for song in data['songs']:
            song = format_song(song, lyrics)
    
    return data

def format_playlist(data, lyrics):
    """Legacy playlist formatting"""
    if not data:
        return data
        
    data['firstname'] = format(data.get('firstname', ''))
    data['listname'] = format(data.get('listname', ''))
    
    if 'songs' in data:
        for song in data['songs']:
            song = format_song(song, lyrics)
    
    return data
