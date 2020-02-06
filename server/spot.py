import os
import requests
import urllib
import urlparse
import base64
import time
import json
import threading
import random

CLIENT_ID = '< Put your spotify api client id here >'
CLIENT_SECRET = '< Put your spotify api client secret here >'
REDIRECT_URI = 'http://localhost:8000' # Just a dummy address
SCOPES = 'user-read-private user-read-email user-read-playback-state user-read-currently-playing user-modify-playback-state'



_state_cb = None
_refresh_token = None
_access_token = None
_expires = None



def spot_loadauth():
    global _access_token
    global _refresh_token
    global _expires
    try:
        with open('lastauth.json', 'r') as f:
            j = json.loads(f.read())
            if 'refresh_token' in j:
                _refresh_token = j['refresh_token']
            if 'access_token' in j:
                _access_token = j['access_token']
            if 'expires' in j:
                _expires = j['expires']
    except Exception, e:
        print ("Failed to load token", e)
    if _refresh_token:
        print ("Loaded stored refresh tokeb: %s" % (_refresh_token))



def spot_saveauth():
    global _access_token
    global _refresh_token
    global _expires
    with open('lastauth.json', 'w') as f:
        f.write(json.dumps({
            'refresh_token': _refresh_token,
            'access_token': _access_token,
            'expires': _expires
        }))



def spot_login():
    global _access_token
    global _refresh_token
    global _expires
    opts = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'scope': SCOPES,
        'redirect_uri': REDIRECT_URI
    }
    print("\n")
    print("Time to log in!")
    url = 'https://accounts.spotify.com/authorize?' + urllib.urlencode(opts)
    print("\n")
    print("Open this URL:")
    print(url)
    print("\n")
    print("Then paste the redirection url here:")
    u = raw_input("").strip()
    up = urlparse.urlparse(u)
    qs = urlparse.parse_qs(up.query)
    print("\n")
    authcode = qs['code'][0]
    data2 = urllib.urlencode({
        'grant_type': 'authorization_code',
        'code': authcode,
        'redirect_uri': REDIRECT_URI,
    })
    print("Sending payload: %r" % (data2))
    basicauth = base64.b64encode(CLIENT_ID + ':' + CLIENT_SECRET)
    resp = requests.post('https://accounts.spotify.com/api/token', data2, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic ' + basicauth})
    j2 = resp.json()
    print("Got resp: %r" % (j2))
    _access_token = j2['access_token']
    _expires = time.time() * 1000.0 + j2['expires_in']
    _refresh_token = j2['refresh_token']
    spot_saveauth()



def spot_updatetoken():
    global _expires
    global _access_token
    global _refresh_token
    if time.time() * 1000.0 < _expires - 10000.0:
        return
    data2 = urllib.urlencode({
        'grant_type': 'refresh_token',
        'refresh_token': _refresh_token,
    })
    print("Sending payload: %r" % (data2))
    basicauth = base64.b64encode(CLIENT_ID + ':' + CLIENT_SECRET)
    resp = requests.post('https://accounts.spotify.com/api/token', data2, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic ' + basicauth})
    if resp:
        j2 = resp.json()
        print("Got resp: %r" % (j2))
        _access_token = j2['access_token']
        _expires = time.time() * 1000.0 + j2['expires_in']
        spot_saveauth()
    else:
        print("Failed to refresh token!?")



_spot_thread_alive = False
_spot_thread = None



def spot_thread():
    global _spot_thread_alive
    t = 0
    while _spot_thread_alive:
        t += 1
        if t > 30:
            t = 0
            spot_requeststate()
        time.sleep(0.1)



def spot_init():
    global _refresh_token
    global _spot_thread
    global _spot_thread_alive
    spot_loadauth()
    if not _refresh_token:
        spot_login()
    _spot_thread_alive = True
    _spot_thread = threading.Thread(target=spot_thread)
    _spot_thread.start()
    spot_updatetoken()



def spot_kill():
    global _spot_thread_alive
    global _spot_thread
    _spot_thread_alive = False
    _spot_thread.join()



def spot_setstatehandler(cb):
    global _state_cb
    _state_cb = cb



def spot_requeststate():
    global _access_token
    global _state_cb
    spot_updatetoken()
    resp = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers={'Authorization': 'Bearer ' + _access_token})
    if resp.status_code == 200:
        j2 = resp.json()
        if _state_cb:
            _state_cb(j2)



def spot_next():
    global _access_token
    spot_updatetoken()
    print("Spot: Sending NEXT")
    resp = requests.post('https://api.spotify.com/v1/me/player/next', headers={'Authorization': 'Bearer ' + _access_token})
    spot_requeststate()



def spot_previous():
    spot_updatetoken()
    print("Spot: Sending PREVIOUS")
    resp = requests.post('https://api.spotify.com/v1/me/player/previous', headers={'Authorization': 'Bearer ' + _access_token})
    spot_requeststate()



def spot_play():
    spot_updatetoken()
    print("Spot: Sending PLAY")
    resp = requests.put('https://api.spotify.com/v1/me/player/play', headers={'Authorization': 'Bearer ' + _access_token})
    spot_requeststate()



def spot_pause():
    spot_updatetoken()
    print("Spot: Sending PAUSE")
    resp = requests.put('https://api.spotify.com/v1/me/player/pause', headers={'Authorization': 'Bearer ' + _access_token})
    spot_requeststate()



def spot_get_colors(imageurl):
    global _access_token
    global _state_cb
    spot_updatetoken()
    # This code used to fetch a color from an api
    # Just randomise a color for now
    return [
        random.randint(0, 150),
        random.randint(0, 150),
        random.randint(0, 150),
    ]



