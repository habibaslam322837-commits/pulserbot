from flask import Flask, request
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)

def db():
    return sqlite3.connect("users.db")

TRC = "TSd1kwMavFDHJNXXqioSXWjywrEJW5Dt3U"
ERC = "0x3ae6c6ca3a0cdd54d93f605284a423b572caca72"

ADMIN_ID = "8671125457"
BOT_USERNAME = "pulseofficialsbot"

def ui():
    return """
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
    const tg = window.Telegram.WebApp;
    tg.expand();
    tg.ready();
    const user = tg.initDataUnsafe?.user;
    if (window.location.pathname === '/' && user && !window.location.search.includes("id=")) {
        window.location.href = '/?id=' + user.id + '&username=' + (user.username || '') + '&first_name=' + encodeURIComponent(user.first_name || '');
    }
    </script>
    <style>
    body {background: linear-gradient(135deg, #0a0c10, #1a1f2e); color: #e0f0ff; font-family: 'Inter', system-ui;}
    .card {background: rgba(19, 23, 31, 0.95); border: 1px solid #334155; padding: 24px; border-radius: 24px; margin-bottom: 20px; box-shadow: 0 10px 30px -10px rgba(234, 179, 8, 0.8);}
    .btn {padding: 18px; border-radius: 16px; text-align: center; display: block; font-weight: 700; transition: all 0.3s ease; font-size: 1.1rem;}
    .neon {box-shadow: 0 0 30px #facc15;}
    .glow {animation: glow 2s ease-in-out infinite alternate;}
    .marquee {overflow: hidden; white-space: nowrap;}
    .marquee-content {display: inline-block; animation: marquee 35s linear infinite;}
    @keyframes glow { from {text-shadow: 0 0 15px #facc15;} to {text-shadow: 0 0 35px #facc15;} }
    @keyframes marquee { from {transform: translateX(100%);} to {transform: translateX(-100%);} }
    .profile-btn {background: linear-gradient(90deg, #22d3ee, #67e8f9); color: #0f172a; box-shadow: 0 0 30px #22d3ee; font-size: 1.25rem; font-weight: 800; text-shadow: 0 0 15px rgba(103, 232, 249, 0.6);}
    h1, h2, h3 { font-weight: 800; letter-spacing: -0.5px; }
    .text-amber-300, .text-amber-400 { text-shadow: 0 0 12px rgba(251, 191, 36, 0.7); }
    .text-emerald-400 { text-shadow: 0 0 10px rgba(16, 185, 129, 0.6); }
    .text-purple-400 { text-shadow: 0 0 10px rgba(168, 85, 247, 0.6); }
    .text-yellow-400 { text-shadow: 0 0 10px rgba(234, 179, 8, 0.7); }
    input, select, textarea { border-radius: 12px; padding: 14px; width: 100%; background: #f8fafc; color: #0f172a; margin-bottom: 12px; }
    </style>
    """

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, type TEXT, balance REAL DEFAULT 0,
                    profit REAL DEFAULT 0, total_profit REAL DEFAULT 0, vip_level INTEGER DEFAULT 0,
                    reward_balance REAL DEFAULT 0, reward_timestamp TEXT,
                    username TEXT, first_name TEXT, last_name TEXT, email TEXT,
                    phone TEXT, country_code TEXT, address TEXT, referral_code TEXT, registered INTEGER DEFAULT 0)''')
    for col in ["last_name", "email", "phone", "country_code", "address", "referral_code", "registered"]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except:
            pass
    conn.commit()
    conn.close()

init_db()

def get_vip_level(balance):
    if balance >= 50000: return 7
    if balance >= 20000: return 6
    if balance >= 10000: return 5
    if balance >= 5000: return 4
    if balance >= 2000: return 3
    if balance >= 1000: return 2
    if balance >= 500: return 1
    return 0

def get_vip_bonus(level):
    bonuses = {1: 50, 2: 100, 3: 200, 4: 500, 5: 1000, 6: 2000, 7: 5000}
    return bonuses.get(level, 0)

# ====================== REGISTRATION PAGE ======================
@app.route("/register")
def register():
    uid = request.args.get("id")
    username = request.args.get("username") or ""
    first_name = request.args.get("first_name") or ""
    return f"""{ui()}
    <div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center">
        <div class="card">
            <div class="flex justify-center items-center gap-3 mb-8">
                <span class="text-5xl">🚀</span>
                <h1 class="text-4xl font-bold text-amber-400 glow">PulseForge Nova</h1>
            </div>
            <h2 class="text-center text-2xl mb-6 text-white">Create Your Account</h2>
            
            <form action="/register_submit">
                <input type="hidden" name="uid" value="{uid}">
                <input type="text" name="first_name" value="{first_name}" placeholder="First Name" required>
                <input type="text" name="last_name" placeholder="Last Name" required>
                <input type="email" name="email" placeholder="Email Address" required>
                
                <div class="flex gap-3">
                    <select name="country_code" class="w-1/3 text-black" required>
                        <option value="" disabled selected>Select your country</option>
                        <option value="+880">🇧🇩 +880 (Bangladesh)</option>
                        <option value="+91">🇮🇳 +91 (India)</option>
                        <option value="+1">🇺🇸 +1 (USA/Canada)</option>
                        <option value="+44">🇬🇧 +44 (UK)</option>
                        <option value="+971">🇦🇪 +971 (UAE)</option>
                        <option value="+966">🇸🇦 +966 (Saudi Arabia)</option>
                        <option value="+92">🇵🇰 +92 (Pakistan)</option>
                        <option value="+65">🇸🇬 +65 (Singapore)</option>
                        <option value="+60">🇲🇾 +60 (Malaysia)</option>
                    </select>
                    <input type="tel" name="phone" placeholder="Phone Number" class="flex-1" required>
                </div>
                
                <textarea name="address" rows="2" placeholder="Full Address" class="text-black" required></textarea>
                <input type="text" name="referral_code" placeholder="Referral Code (Optional)">
                
                <div class="flex items-center gap-2 mt-4 mb-6">
                    <input type="checkbox" id="agree" name="agree" class="w-5 h-5" required>
                    <label for="agree" class="text-sm">I agree to the <span class="text-cyan-400 underline">Terms & Conditions</span></label>
                </div>
                
                <button type="submit" class="btn bg-gradient-to-r from-cyan-400 to-blue-500 text-white neon text-xl w-full">Register Now</button>
            </form>
        </div>
    </div>"""

@app.route("/register_submit")
def register_submit():
    uid = request.args.get("uid")
    first_name = request.args.get("first_name", "")
    last_name = request.args.get("last_name", "")
    email = request.args.get("email", "")
    country_code = request.args.get("country_code", "")
    phone = request.args.get("phone", "")
    address = request.args.get("address", "")
    referral_code = request.args.get("referral_code", "")

    conn = db()
    c = conn.cursor()
    c.execute("""UPDATE users SET 
                 first_name=?, last_name=?, email=?, 
                 country_code=?, phone=?, address=?, referral_code=?, registered=1 
                 WHERE id=?""", 
              (first_name, last_name, email, country_code, phone, address, referral_code, uid))
    conn.commit()
    conn.close()

    return f"""{ui()}
    <div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center">
        <div class="card">
            <h2 class="text-green-400 text-3xl mb-4">🎉 Registration Successful!</h2>
            <p class="text-xl mb-8">Welcome to PulseForge Nova</p>
            <a href="/?id={uid}" class="btn bg-green-500 text-white">Go to Dashboard →</a>
        </div>
    </div>"""

# ====================== HOME ======================
@app.route("/")
def home():
    uid = request.args.get("id")
    username = request.args.get("username") or None
    first_name = request.args.get("first_name") or None

    if not uid:
        return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-red-400 text-2xl mb-4">⚠️ Access Denied</h2><p class="text-xl mb-6">Please start the bot first.</p><a href="https://t.me/{BOT_USERNAME}" target="_blank" class="btn bg-green-500 text-white text-lg">🚀 Start Bot Now</a></div></div>"""

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    user = c.fetchone()

    if not user or user[14] == 0:   # registered = 0
        conn.close()
        return f"""{ui()}<script>window.location.href = '/register?id={uid}';</script>"""

    # Normal dashboard
    current_vip = get_vip_level(user[2])
    if current_vip > user[5]:
        bonus = get_vip_bonus(current_vip)
        now = datetime.now().isoformat()
        c.execute("UPDATE users SET vip_level=?, reward_balance=reward_balance+?, reward_timestamp=? WHERE id=?", (current_vip, bonus, now, uid))
        c.execute("INSERT INTO messages VALUES(NULL,?,?)", (uid, f"Congratulations! You are now VIP {current_vip} - {bonus} USDT reward added!"))
        conn.commit()
        c.execute("SELECT * FROM users WHERE id=?", (uid,))
        user = c.fetchone()

    if user[7] and user[6] > 0:
        reward_time = datetime.fromisoformat(user[7])
        if datetime.now() - reward_time >= timedelta(hours=24):
            c.execute("UPDATE users SET balance=balance+?, reward_balance=0, reward_timestamp=NULL WHERE id=?", (user[6], uid))
            c.execute("INSERT INTO messages VALUES(NULL,?,?)", (uid, f"{user[6]} USDT Reward Balance has been added to your Main Balance!"))
            conn.commit()
            c.execute("SELECT * FROM users WHERE id=?", (uid,))
            user = c.fetchone()

    c.execute("SELECT message FROM messages WHERE user_id=?", (uid,))
    msgs = c.fetchall()
    conn.close()

    badge = f'<span class="ml-auto bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full">{len(msgs)}</span>' if msgs else ''
    vip_text = f"You are now VIP {user[5]} tier" if user[5] > 0 else "Regular Member"
    messages_html = "".join([f'<div class="bg-[#252a31] p-4 rounded-2xl"><strong>From Admin/Support:</strong><br>{m[0]}</div>' for m in msgs])

    admin_html = ''
    if uid == ADMIN_ID:
        admin_html = f'''
        <a href="/admin?id={uid}" class="block mt-6 mx-5 bg-gradient-to-r from-purple-600 to-violet-600 text-white text-center py-6 rounded-3xl font-bold text-2xl shadow-2xl neon">
            🔐 Admin Panel
        </a>
        <div class="text-center text-green-400 text-sm mt-2">✅ You are Admin (UID: {uid})</div>
        '''

    html = f"""{ui()}
    <div class="max-w-md mx-auto p-5 min-h-screen">
    <div class="text-center mb-4"><h1 class="text-amber-300 text-2xl font-bold glow">Make Your Day Happy with PulseForge!</h1></div>
    <div class="flex justify-center items-center gap-2 mb-8"><span class="text-4xl">🚀</span><h2 class="text-amber-400 text-3xl font-bold tracking-widest glow">PulseForge</h2></div>
    <div class="flex justify-end mb-3"><span class="bg-gradient-to-r from-amber-400 to-yellow-500 text-black text-sm font-bold px-5 py-1 rounded-full">{vip_text}</span></div>
    <div class="card neon text-center"><h1 class="text-5xl font-bold text-amber-300">{user[2]} USD</h1></div>
    <div class="card">📈 Daily Profit: <span class="text-emerald-400 font-semibold">{user[3]}</span><br>💰 Total Profit: <span class="text-emerald-400 font-semibold">{user[4]}</span><br>🌟 Reward Balance: <span class="text-purple-400 font-semibold">{user[6]} USD</span></div>

    <a href="/profile?id={uid}" class="profile-btn btn neon text-xl mb-4">👤 Profile</a>

    <a href='/deposit?id={uid}' class='btn bg-gradient-to-r from-amber-400 to-yellow-500 text-black neon text-lg'>Deposit</a>
    <a href='/withdraw?id={uid}' class='btn bg-gradient-to-r from-red-500 to-rose-600 text-white text-lg'>Withdraw</a>
    <a href='/support?id={uid}&username={username}' class='btn bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-lg'>Support</a>
    <div onclick="openMessagesModal()" class="card mt-6 flex items-center justify-between cursor-pointer hover:bg-[#1f2937]"><h3 class="text-amber-400 text-xl flex items-center gap-2">📩 Messages</h3>{badge}</div>
    <div onclick="openVipModal()" class="card mt-6 flex items-center justify-between cursor-pointer hover:bg-[#1f2937]"><h3 class="text-amber-400 text-xl flex items-center gap-2">🌟 VIP System</h3><span class="text-yellow-400">→</span></div>
    {admin_html}
    <div class="card mt-6 bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-center py-3 overflow-hidden"><div class="marquee"><div class="marquee-content text-sm font-semibold">🎁 VIP Rewards Program &nbsp;&nbsp;&nbsp; VIP1 → 500 (50) &nbsp;&nbsp;&nbsp; ... VIP7 → 50000 (5000)</div></div></div>
    </div>

    <!-- Modals -->
    <div id="messagesModal" onclick="if(event.target===this)closeMessagesModal()" class="hidden fixed inset-0 bg-black/90 flex items-end z-[9999]">
      <div onclick="event.stopImmediatePropagation()" class="bg-[#13171f] w-full max-w-md mx-auto rounded-3xl max-h-[88vh] overflow-hidden flex flex-col shadow-2xl mb-3">
        <div class="w-14 h-1.5 bg-gray-400 rounded-full mx-auto mt-4 mb-1"></div>
        <div class="px-6 pb-4 text-center text-xl font-semibold">Messages</div>
        <div class="flex-1 overflow-y-auto px-5 pb-5 space-y-4">{messages_html or '<div class="text-center text-gray-400 py-10">No messages yet</div>'}</div>
        <div class="p-4 border-t border-gray-700">
            <button onclick="markAsRead()" class="btn bg-green-500 text-white w-full">Mark All as Read</button>
        </div>
      </div>
    </div>
    <div id="vipModal" onclick="if(event.target===this)closeVipModal()" class="hidden fixed inset-0 bg-black/90 flex items-end z-[9999]">
      <div onclick="event.stopImmediatePropagation()" class="bg-[#13171f] w-full max-w-md mx-auto rounded-3xl max-h-[88vh] overflow-hidden flex flex-col shadow-2xl mb-3">
        <div class="w-14 h-1.5 bg-gray-400 rounded-full mx-auto mt-4 mb-1"></div>
        <div class="px-6 pb-4 text-center text-xl font-semibold">🎁 VIP Rewards Program</div>
        <div class="flex-1 overflow-y-auto px-6 pb-6 space-y-6 text-white text-sm">
          <div class="text-center text-amber-300 text-lg font-bold">Upgrade your VIP level to earn more rewards!</div>
          <div>🌟 <strong>VIP1</strong> - 500 USDT reward (50 USDT add)</div>
          <div>🌟 <strong>VIP2</strong> - 1000 USDT reward (100 USDT add)</div>
          <div>🌟 <strong>VIP3</strong> - 2000 USDT reward (200 USDT add)</div>
          <div>🌟 <strong>VIP4</strong> - 5000 USDT reward (500 USDT add)</div>
          <div>🌟 <strong>VIP5</strong> - 10000 USDT reward (1000 USDT add)</div>
          <div>🌟 <strong>VIP6</strong> - 20000 USDT reward (2000 USDT add)</div>
          <div>🌟 <strong>VIP7</strong> - 50000 USDT reward (5000 USDT add)</div>
        </div>
      </div>
    </div>

    <script>
    function openMessagesModal() {{ document.getElementById('messagesModal').classList.remove('hidden'); document.getElementById('messagesModal').classList.add('flex'); }}
    function closeMessagesModal() {{ document.getElementById('messagesModal').classList.add('hidden'); document.getElementById('messagesModal').classList.remove('flex'); }}
    function openVipModal() {{ document.getElementById('vipModal').classList.remove('hidden'); document.getElementById('vipModal').classList.add('flex'); }}
    function closeVipModal() {{ document.getElementById('vipModal').classList.add('hidden'); document.getElementById('vipModal').classList.remove('flex'); }}
    function markAsRead() {{
        const uid = new URLSearchParams(window.location.search).get('id');
        fetch('/clear_messages?id=' + uid).then(() => location.reload());
    }}
    </script>
    """
    return html

# ====================== ALL USER INFORMATION (নতুন বাটনের জন্য নতুন পেজ) ======================
@app.route("/all_user_info")
def all_user_info():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, username, first_name, last_name, email, phone, country_code, address, referral_code, balance, vip_level FROM users")
    users = c.fetchall()
    conn.close()

    user_cards = ""
    for u in users:
        user_cards += f"""
        <div class="card">
            <div class="text-amber-400 font-bold mb-2">@{u[1] or u[2] or u[0]}</div>
            <div><strong>Name:</strong> {u[2] or ''} {u[3] or ''}</div>
            <div><strong>Email:</strong> {u[4] or 'N/A'}</div>
            <div><strong>Phone:</strong> {u[5] or 'N/A'} {u[6] or ''}</div>
            <div><strong>Address:</strong> {u[7] or 'N/A'}</div>
            <div><strong>Referral Code:</strong> {u[8] or 'N/A'}</div>
            <div><strong>Balance:</strong> <span class="text-amber-300">{u[9]} USD</span></div>
            <div><strong>VIP Level:</strong> <span class="text-yellow-400">VIP {u[10]}</span></div>
        </div>
        """

    html = f"""{ui()}
    <div class="max-w-md mx-auto p-4">
    <h2 class="text-amber-400 text-center text-3xl mb-6 glow">👥 All Users Information</h2>
    {user_cards or '<div class="text-center text-gray-400 py-10">No users yet</div>'}
    <a href="/admin?id={ADMIN_ID}" class="btn bg-gray-500 text-white mt-6">← Back to Admin Panel</a>
    </div>
    """
    return html

# ====================== ADMIN PANEL (নতুন বাটন যোগ করা হয়েছে) ======================
@app.route("/admin")
def admin():
    uid = request.args.get("id")
    if uid != ADMIN_ID:
        return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-red-400 text-3xl mb-4">🚫 Access Denied</h2><p class="text-xl">Only Admin can access this panel.</p></div></div>"""

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, username, first_name, last_name, email, phone, country_code, address, balance FROM users")
    users = c.fetchall()
    c.execute("SELECT * FROM support")
    sup = c.fetchall()
    c.execute("SELECT COUNT(*) FROM deposits WHERE status='pending'")
    pending_dep = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM withdraws WHERE status='pending'")
    pending_wd = c.fetchone()[0]
    conn.close()

    badge_support = f'<span class="ml-auto bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full">{len(sup)}</span>' if sup else ''
    badge_dep = f'<span class="ml-auto bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full">{pending_dep}</span>' if pending_dep > 0 else ''
    badge_wd = f'<span class="ml-auto bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full">{pending_wd}</span>' if pending_wd > 0 else ''

    user_list_html = ""
    for u in users:
        display_name = u[1] if u[1] else (u[2] if u[2] else u[0])
        user_list_html += f"""
        <div class="bg-[#252a31] p-4 rounded-2xl flex justify-between items-center">
            <div>
                <span class="font-medium text-white">@{display_name}</span><br>
                <span class="text-emerald-400 text-sm">{u[8]} USD</span>
            </div>
            <div class="flex gap-2">
                <a href='/manage?uid={u[0]}' class="text-amber-400 font-medium">Manage</a>
                <a href='/user_details?uid={u[0]}' class="text-cyan-400 font-medium">Details</a>
            </div>
        </div>
        """

    html = f"""{ui()}
    <div class="max-w-md mx-auto p-4">
    <h2 class="text-amber-400 text-center text-3xl mb-6 glow">🔐 Admin Panel</h2>
    
    <!-- নতুন বাটন যোগ করা হয়েছে -->
    <a href='/all_user_info' class='btn bg-gradient-to-r from-cyan-400 to-blue-500 text-white neon text-lg flex justify-between items-center mb-4'>👥 All User Information</a>
    
    <a href='/deposits' class='btn bg-gradient-to-r from-amber-400 to-yellow-500 text-black neon text-lg flex justify-between items-center'>Pending Deposits {badge_dep}</a>
    <a href='/withdraws' class='btn bg-gradient-to-r from-red-500 to-rose-600 text-white text-lg flex justify-between items-center'>Pending Withdraws {badge_wd}</a>
    
    <div class="card mt-6">
        <h3 class="text-amber-400 mb-3">Broadcast to All Users</h3>
        <form action='/broadcast'>
            <textarea name='m' placeholder="Type message here..." rows="4" class='text-black w-full p-3 rounded mb-3'></textarea>
            <button class='btn bg-blue-500 w-full'>Send Broadcast</button>
        </form>
    </div>
    
    <div class="card mt-4">
        <h3 class="text-amber-400 mb-3">All Users</h3>
        <div class="space-y-3">
            {user_list_html}
        </div>
    </div>
    
    <div onclick="openSupportModal()" class="card mt-4 flex items-center justify-between cursor-pointer hover:bg-[#1f2937]">
        <h3 class="text-amber-400 text-lg flex items-center gap-2">📩 Support Inbox</h3>
        {badge_support}
    </div>
    </div>
    <div id="supportModal" onclick="if(event.target===this)closeSupportModal()" class="hidden fixed inset-0 bg-black/90 flex items-end z-[9999]">
      <div onclick="event.stopImmediatePropagation()" class="bg-[#13171f] w-full max-w-md mx-auto rounded-3xl max-h-[88vh] overflow-hidden flex flex-col shadow-2xl mb-3">
        <div class="w-14 h-1.5 bg-gray-400 rounded-full mx-auto mt-4 mb-1"></div>
        <div class="px-6 pb-4 text-center text-xl font-semibold">Support Inbox</div>
        <div class="flex-1 overflow-y-auto px-5 pb-5 space-y-4">
            {''.join([f'<div class="card p-5"><p><strong>From:</strong> @{s[2]}</p><p class="mt-2">{s[4]}</p><form action="/reply_support"><input type="hidden" name="uid" value="{s[1]}"><input name="reply" placeholder="Reply..." class="text-black w-full p-3 rounded mb-3"><button class="btn bg-blue-500 w-full">Send Reply</button></form></div>' for s in sup]) or '<div class="text-center text-gray-400 py-10">No support messages yet</div>'}
        </div>
      </div>
    </div>
    <script>
    function openSupportModal() {{ document.getElementById('supportModal').classList.remove('hidden'); document.getElementById('supportModal').classList.add('flex'); }}
    function closeSupportModal() {{ document.getElementById('supportModal').classList.add('hidden'); document.getElementById('supportModal').classList.remove('flex'); }}
    </script>
    """
    return html

# ====================== বাকি সব রুট (আগের মতোই) ======================
# (profile, clear_messages, support, deposit, withdraw, manage, user_details ইত্যাদি আগের কোড থেকে একই)

@app.route("/profile")
def profile():
    uid = request.args.get("id")
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    user = c.fetchone()
    conn.close()
    if not user:
        return f"""{ui()}<div class="max-w-md mx-auto p-5 text-center">User not found</div>"""

    html = f"""{ui()}
    <div class="max-w-md mx-auto p-5 min-h-screen">
        <div class="card">
            <h2 class="text-amber-400 text-2xl text-center mb-6">👤 Profile Summary</h2>
            <div class="space-y-4 text-lg">
                <div><strong>Main Balance:</strong> <span class="text-amber-300">{user[2]} USD</span></div>
                <div><strong>Daily Profit:</strong> <span class="text-emerald-400">{user[3]} USD</span></div>
                <div><strong>Total Profit:</strong> <span class="text-emerald-400">{user[4]} USD</span></div>
                <div><strong>Reward Balance:</strong> <span class="text-purple-400">{user[6]} USD</span></div>
                <div><strong>VIP Level:</strong> <span class="text-yellow-400">VIP {user[5]}</span></div>
            </div>
        </div>
        <a href="/?id={uid}" class="btn bg-gray-500 text-white mt-8">← Back to Main Menu</a>
    </div>
    """
    return html

@app.route("/clear_messages")
def clear_messages():
    uid = request.args.get("id")
    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()
    return "Messages cleared"

# ====================== RUN ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
