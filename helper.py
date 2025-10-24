import base64
import jiosaavn
from pyDes import *
import requests
from bs4 import BeautifulSoup
import json
import re

# ... (keep all your existing helper functions) ...

# NEW: Web scraping functions
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
                
                # Look for song data patterns
                if 'song' in content and 'duration' in content:
                    json_match = re.search(r'{\s*"songs":\s*\[.*?\]', content)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(0) + '}')
                            if 'songs' in data:
                                return data['songs']
                        except:
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
                    if isinstance(item, dict) and 'type' in item and item.get('type') == 'song':
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
        # Look for song cards
        song_elements = soup.find_all('div', class_=re.compile(r'song|track|result', re.I))
        
        for element in song_elements:
            song = parse_song_from_element(element)
            if song:
                songs.append(song)
                
        # Look for list items
        list_items = soup.find_all('li', class_=re.compile(r'song|track', re.I))
        for item in list_items:
            song = parse_song_from_list_item(item)
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
            'song': item.get('title', ''),
            'artists': [item.get('primary_artists', '')] if isinstance(item.get('primary_artists'), str) else item.get('artists', []),
            'image': item.get('image', ''),
            'duration': item.get('duration', ''),
            'album': item.get('album', ''),
            'year': item.get('year', ''),
            'language': item.get('language', ''),
            'perma_url': item.get('perma_url', '')
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
