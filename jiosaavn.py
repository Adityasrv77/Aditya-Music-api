import requests
import endpoints
import helper  # Make sure this line exists
import json
from traceback import print_exc
import re
from cache import cache_response


@cache_response(ttl=600)
def search_for_song_clean(query, page=1, limit=20, use_scraping=True):
    """Hybrid search that combines API and web scraping"""
    all_results = []
    
    # Step 1: Try API search (fastest)
    print(f"🔍 Searching API for: {query}")
    api_results = search_via_api(query, page, limit)
    all_results.extend(api_results)
    
    # Step 2: If few results or use_scraping enabled, try web scraping
    if use_scraping and (not api_results or len(api_results) < 10):
        print(f"🌐 Web scraping for: {query}")
        scraped_results = helper.scrape_jiosaavn_search(query)
        all_results.extend(scraped_results)
    
    # Step 3: Remove duplicates and format
    unique_results = helper.remove_duplicate_songs(all_results)
    clean_results = []
    
    for song in unique_results:
        clean_song = helper.format_song_clean(song)
        if clean_song and clean_song.get('song'):
            clean_results.append(clean_song)
    
    print(f"✅ Found {len(clean_results)} unique songs for: {query}")
    return clean_results[:limit]  # Respect limit

def search_via_api(query, page=1, limit=20):
    """Try multiple API endpoints"""
    api_results = []
    
    # Try different API endpoints
    endpoints_to_try = [
        # Original search endpoint
        f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&_marker=0&cc=in&p={page}&n={limit}&q={query}",
        
        # Alternative endpoints
        f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&cc=in&includeMetaTags=1&query={query}",
        f"https://www.jiosaavn.com/api.php?__call=search.getTopQuery&_format=json&query={query}",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.jiosaavn.com/',
        'Origin': 'https://www.jiosaavn.com'
    }
    
    for endpoint in endpoints_to_try:
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            if response.status_code == 200:
                response_text = response.text.encode().decode('unicode-escape')
                
                # Clean the response
                pattern = r'\(From "([^"]+)"\)'
                response_text = re.sub(pattern, r"(From '\1')", response_text)
                
                data = json.loads(response_text)
                
                # Extract results from different response structures
                if 'results' in data and data['results']:
                    api_results.extend(data['results'])
                    break  # Use first successful endpoint
                elif 'songs' in data and data['songs']:
                    api_results.extend(data['songs'])
                    break
                elif 'albums' in data and data['albums']:
                    # Extract songs from albums
                    for album in data['albums']:
                        if 'songs' in album:
                            api_results.extend(album['songs'])
                    break
                    
        except Exception as e:
            print(f"API endpoint failed {endpoint}: {e}")
            continue
    
    return api_results

@cache_response(ttl=1800)
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

# ... (keep all your other existing functions unchanged) ...
