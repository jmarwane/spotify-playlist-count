# spotify-playlist-count
Count streams of tracks in a spotify playlist

## Setup env
```sh
python3.10 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Create creds.csv
```python
client_id,client_secret
YOUR_CLIENT_ID,YOUR_CLIENT_SECRET
```

## Run script

```sh
python spotify_playlist_count.py --playlist_id #playlist id
```

