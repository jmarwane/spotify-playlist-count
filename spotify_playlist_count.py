import os
import argparse
import re
import time
import csv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# --------- CONFIGURATION ---------
CREDENTIALS_CSV = "creds.csv"  # Path to the CSV file with credentials
OUTPUT_DIR = "out"
# ---------------------------------


def load_spotify_credentials(csv_path):
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        credentials = next(reader)
        return credentials['client_id'], credentials['client_secret']


def setup_spotify_client():
    client_id, client_secret = load_spotify_credentials(CREDENTIALS_CSV)
    auth_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def get_playlist_tracks(sp, playlist_id):
    print("Fetching playlist tracks via Spotify API...")
    tracks = []
    results = sp.playlist_items(playlist_id, additional_types=['track'], limit=100)
    while results:
        for item in results['items']:
            track = item['track']
            if track:  # Skip removed/unavailable tracks
                track_id = track['id']
                name = track['name']
                artists = ', '.join(artist['name'] for artist in track['artists'])
                url = f"https://open.spotify.com/track/{track_id}"
                popularity = track.get('popularity', 0)
                tracks.append({
                    'name': name,
                    'artist': artists,
                    'url': url,
                    'popularity': popularity
                })
        if results['next']:
            results = sp.next(results)
        else:
            break
    print(f"Found {len(tracks)} tracks.")
    return tracks


def setup_driver():
    options = Options()
    options.add_argument('--headless')  # Legacy headless mode
    return webdriver.Chrome(options=options)


def get_stream_count(driver, track_url):
    try:
        driver.get(track_url)
        wait = WebDriverWait(driver, 10)
        playcount_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-testid="playcount"]')))
        return playcount_element.text
    except Exception as e:
        print(f"Error getting play count for {track_url}: {e}")
        return "N/A"


def parse_stream_count(count_str):
    try:
        return int(count_str.replace(',', '').strip())
    except:
        return 0  # fallback if parsing fails (e.g., N/A)


def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)


def get_playlist_name(sp, playlist_id):
    playlist = sp.playlist(playlist_id)
    return playlist['name']


def main():
    parser = argparse.ArgumentParser(description="Fetch Spotify playlist stream counts.")
    parser.add_argument("--playlist_id", required=True, help="Spotify Playlist ID or full URL")
    args = parser.parse_args()

    playlist_id = args.playlist_id.split("/")[-1].split("?")[0]
    sp = setup_spotify_client()
    driver = setup_driver()

    playlist_name = get_playlist_name(sp, playlist_id)
    sanitized_name = sanitize_filename(playlist_name)
    output_csv = os.path.join(OUTPUT_DIR, f"{sanitized_name}_stream_counts.csv")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_streams = 0

    try:
        # Step 1: Get track info via API
        tracks = get_playlist_tracks(sp, playlist_id)

        # Step 2: Scrape play counts
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Track Name', 'Artist', 'Track URL', 'Popularity', 'Stream Count'])

            for track in tracks:
                # Print initial line (will be overwritten after stream count is fetched)
                print(f"Processing: {track['name']} by {track['artist']}...", end='\r', flush=True)

                stream_count = get_stream_count(driver, track['url'])
                streams_int = parse_stream_count(stream_count)
                total_streams += streams_int

                # Overwrite the same line with completed message
                print(f"✔ Done: {track['name']} by {track['artist']} | Popularity: {track['popularity']} | Streams: {streams_int}".ljust(100))

                writer.writerow([track['name'], track['artist'], track['url'], track['popularity'], streams_int])
                # time.sleep(1)  # optional: to be gentle with Spotify

        print(f"\n✅ Done! Stream counts saved to: {output_csv}")
        print()  # move to a new line after progress updates
        print(f"\n🎧 Total Streams: {total_streams:,}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
