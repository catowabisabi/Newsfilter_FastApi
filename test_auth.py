"""
NewsFilter Auth Testing Script v2
Full 3-step flow: authenticate -> authorize -> getTokens
"""

import requests
import json
import os
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

USERNAME   = os.getenv("NEWSFILTER_USERNAME")
PASSWORD   = os.getenv("NEWSFILTER_PASSWORD")
CLIENT_ID  = os.getenv("NEWSFILTER_CLIENT_ID")

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
)

session = requests.Session()
session.headers.update({
    "User-Agent":  BROWSER_UA,
    "Origin":      "https://newsfilter.io",
    "Referer":     "https://newsfilter.io/",
    "DNT":         "1",
})

access_token = None

# ======================================================
print("=" * 60)
print("STEP 1 - POST /co/authenticate")
print("=" * 60)

r1 = session.post(
    "https://login.newsfilter.io/co/authenticate",
    headers={
        "Accept":       "*/*",
        "Content-Type": "application/json",
        "auth0-client": "eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMi4xIn0=",
    },
    json={
        "client_id":       CLIENT_ID,
        "username":        USERNAME,
        "password":        PASSWORD,
        "credential_type": "http://auth0.com/oauth/grant-type/password-realm",
        "realm":           "Username-Password-Authentication",
    },
    timeout=30,
)

print("Status :", r1.status_code)
print("Body   :", r1.text)

if r1.status_code != 200:
    print("FAILED step 1")
    exit(1)

step1 = r1.json()
login_ticket = step1["login_ticket"]
co_verifier  = step1.get("co_verifier", "")
print()
print("login_ticket :", login_ticket, "(" + str(len(login_ticket)) + " chars)")
print("co_verifier  :", co_verifier)

# ======================================================
print()
print("=" * 60)
print("STEP 2 - GET /authorize (extract code from redirect)")
print("=" * 60)

authorize_url = (
    "https://login.newsfilter.io/authorize"
    "?client_id=" + CLIENT_ID +
    "&response_type=code"
    "&redirect_uri=https://newsfilter.io/callback"
    "&scope=openid profile email"
    "&audience=NewsFilter.io"
    "&login_ticket=" + login_ticket +
    "&co_verifier=" + co_verifier +
    "&realm=Username-Password-Authentication"
    "&auth0Client=eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMi4xIn0="
)

print("URL:", authorize_url[:150] + "...")

r2 = session.get(authorize_url, allow_redirects=False, timeout=30)
print("Status  :", r2.status_code)
location = r2.headers.get("Location", "")
print("Location:", location[:300])

# Follow redirects to find ?code=
auth_code = None
current_url = location
redirect_count = 0

while current_url and redirect_count < 10:
    redirect_count += 1
    parsed = urlparse(current_url)
    qs = parse_qs(parsed.query)
    
    if "code" in qs:
        auth_code = qs["code"][0]
        print()
        print("Found auth code in redirect #" + str(redirect_count) + ":", auth_code, "(" + str(len(auth_code)) + " chars)")
        break
    
    # Check fragment for implicit flow
    if parsed.fragment:
        frag_qs = parse_qs(parsed.fragment)
        if "access_token" in frag_qs:
            access_token = frag_qs["access_token"][0]
            print()
            print("Found access_token in fragment!", access_token[:60] + "...")
            break
    
    print("  Redirect #" + str(redirect_count) + ":", current_url[:150])
    
    try:
        r_next = session.get(current_url, allow_redirects=False, timeout=15)
        current_url = r_next.headers.get("Location", "")
        if not current_url:
            print("  No more redirects. Status:", r_next.status_code)
            print("  Body:", r_next.text[:300])
    except Exception as e:
        print("  Redirect target error (may be expected):", str(e)[:100])
        break

# Check final URL too
if not auth_code and current_url:
    parsed = urlparse(current_url)
    qs = parse_qs(parsed.query)
    if "code" in qs:
        auth_code = qs["code"][0]
        print("Found auth code in final URL:", auth_code)

if not auth_code and not access_token:
    print()
    print("response_type=code failed. Trying response_type=token id_token ...")
    
    # Get fresh ticket
    r1b = session.post(
        "https://login.newsfilter.io/co/authenticate",
        headers={
            "Accept":       "*/*",
            "Content-Type": "application/json",
            "auth0-client": "eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMi4xIn0=",
        },
        json={
            "client_id":       CLIENT_ID,
            "username":        USERNAME,
            "password":        PASSWORD,
            "credential_type": "http://auth0.com/oauth/grant-type/password-realm",
            "realm":           "Username-Password-Authentication",
        },
        timeout=30,
    )
    step1b = r1b.json()
    
    authorize_url2 = (
        "https://login.newsfilter.io/authorize"
        "?client_id=" + CLIENT_ID +
        "&response_type=token%20id_token"
        "&redirect_uri=https://newsfilter.io/callback"
        "&scope=openid profile email"
        "&login_ticket=" + step1b["login_ticket"] +
        "&co_verifier=" + step1b.get("co_verifier", "") +
        "&realm=Username-Password-Authentication"
        "&nonce=test123"
        "&auth0Client=eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMi4xIn0="
    )
    
    r2b = session.get(authorize_url2, allow_redirects=False, timeout=30)
    loc2 = r2b.headers.get("Location", "")
    print("  Implicit flow status:", r2b.status_code)
    print("  Location:", loc2[:300])
    
    if "#" in loc2:
        frag = loc2.split("#", 1)[1]
        frag_qs = parse_qs(frag)
        if "access_token" in frag_qs:
            access_token = frag_qs["access_token"][0]
            print()
            print("Got access_token from implicit flow!", access_token[:60] + "...")
    
    if "code" in parse_qs(urlparse(loc2).query):
        auth_code = parse_qs(urlparse(loc2).query)["code"][0]
        print("Found code in implicit redirect:", auth_code)

# ======================================================
if auth_code and not access_token:
    print()
    print("=" * 60)
    print("STEP 3 - POST /public/actions (getTokens)")
    print("=" * 60)

    r3 = session.post(
        "https://api.newsfilter.io/public/actions",
        headers={
            "Accept":       "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
            "caching-key":  "sfksmdmdg0aadsf224533130",
        },
        json={
            "isPublic":    True,
            "type":        "getTokens",
            "code":        auth_code,
            "redirectUri": "https://newsfilter.io/callback",
        },
        timeout=30,
    )

    print("Status :", r3.status_code)
    print("Body   :", r3.text[:1000])

    if r3.status_code == 200:
        tok_data = r3.json()
        if isinstance(tok_data, dict):
            access_token = (
                tok_data.get("accessToken") or
                tok_data.get("access_token") or
                tok_data.get("id_token")
            )

# ======================================================
if access_token:
    print()
    print("=" * 60)
    print("STEP 4 - Test API (TSLA)")
    print("=" * 60)

    api_resp = requests.post(
        "https://api.newsfilter.io/actions",
        headers={
            "Authorization": "Bearer " + access_token,
            "Content-Type":  "application/json;charset=UTF-8",
            "Accept":        "application/json, text/plain, */*",
            "Origin":        "https://newsfilter.io",
            "Referer":       "https://newsfilter.io/",
            "User-Agent":    BROWSER_UA,
            "caching-key":   "sfksmdmdg0aadsf224533130",
        },
        json={
            "type":        "filterArticles",
            "isPublic":    False,
            "queryString": 'symbols:"TSLA"',
            "from":        0,
            "size":        5,
        },
        timeout=30,
    )
    print("Status :", api_resp.status_code)
    data = api_resp.json()
    articles = data.get("articles", [])
    print("Articles returned:", len(articles))
    if articles:
        for i, a in enumerate(articles[:3]):
            print("  [" + str(i+1) + "] " + a.get("title", "")[:80])
    else:
        print("Response:", api_resp.text[:500])
else:
    print()
    print("NO ACCESS TOKEN - all methods failed")
