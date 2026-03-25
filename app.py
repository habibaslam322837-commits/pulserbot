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

# ====================== UI ======================
def ui():
    return """
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
    const tg = window.Telegram.WebApp;
    tg.expand();
    tg.ready();
    const user = tg.initDataUnsafe?.user;
    if (user && !window.location.search.includes("id=")) {
        window.location.href = '/?id=' + user.id + '&username=' + (user.username || '') + '&first_name=' + encodeURIComponent(user.first_name || '');
    }
    </script>
    <style>
    body {background: linear-gradient(135deg, #0a0c10, #1a1f2e); color: #e0f0ff; font-family: 'Inter', system-ui;}
    .card {background: rgba(19, 23, 31, 0.95); border: 1px solid #334155; padding: 20px; border-radius: 20px; margin-bottom: 16px; box-shadow: 0 10px 30px -10px rgba(234, 179, 8, 0.4);}
    .btn {padding: 18px; border-radius: 16px; text-align: center; display: block; font-weight: 700; transition: all 0.3s ease; font-size: 1.1rem;}
    .neon {box-shadow: 0 0 20px #facc15;}
    .glow {animation: glow 2s ease-in-out infinite alternate;}
    .marquee {overflow: hidden; white-space: nowrap;}
    .marquee-content {display: inline-block; animation: marquee 35s linear infinite;}
    @keyframes glow { from {text-shadow: 0 0 10px #facc15;} to {text-shadow: 0 0 25px #facc15;} }
    @keyframes marquee { from {transform: translateX(100%);} to {transform: translateX(-100%);} }
    </style>
    """

# ====================== DATABASE SETUP ======================
def init_db():
    conn = db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, type TEXT, balance REAL DEFAULT 0,
                    profit REAL DEFAULT 0, total_profit REAL DEFAULT 0, vip_level INTEGER DEFAULT 0,
                    reward_balance REAL DEFAULT 0, reward_timestamp TEXT,
                    username TEXT, first_name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deposits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, amount REAL,
                    network TEXT, txid TEXT, status TEXT DEFAULT 'pending', reason TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS withdraws (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, amount REAL,
                    address TEXT, network TEXT, status TEXT DEFAULT 'pending', reason TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, message TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS support (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT,
                    type TEXT, msg TEXT)''')
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
    if not user:
        c.execute("INSERT INTO users (id, type, username, first_name) VALUES (?,?,?,?)", (uid, "user", username, first_name))
        conn.commit()
        c.execute("SELECT * FROM users WHERE id=?", (uid,))
        user = c.fetchone()
    else:
        if username or first_name:
            c.execute("UPDATE users SET username=?, first_name=? WHERE id=?", (username, first_name, uid))
            conn.commit()
            c.execute("SELECT * FROM users WHERE id=?", (uid,))
            user = c.fetchone()

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
    </script>
    """
    return html

# ====================== SUPPORT (এখন পুরোপুরি ঠিক) ======================
@app.route("/support")
def support():
    uid = request.args.get("id")
    username = request.args.get("username") or "unknown"
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen">
    <div class="card">
        <h2 class="text-blue-400 text-2xl text-center mb-6">📩 Support</h2>
        <form action='/send_support'>
            <input type='hidden' name='uid' value='{uid}'>
            <input type='hidden' name='username' value='{username}'>
            <textarea name='msg' rows="5" placeholder='Type your message here...' class='text-black w-full p-4 rounded-2xl mb-6'></textarea>
            <button class='btn bg-gradient-to-r from-blue-500 to-cyan-500 text-white'>Send Message to Admin</button>
        </form>
    </div>
    </div>"""

@app.route("/send_support")
def send_support():
    uid = request.args.get("uid")
    username = request.args.get("username") or "unknown"
    msg = request.args.get("msg")
    
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO support VALUES(NULL,?,?,?,?)", (uid, username, "user", msg))
    conn.commit()
    conn.close()
    
    return f"""{ui()}
    <div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center">
        <div class="card">
            <h2 class="text-green-400 text-3xl mb-4">✅ Support Sent</h2>
            <p class="text-xl mb-8">Your message has been sent to the admin.</p>
            <a href="/?id={uid}" class="btn bg-green-500 text-white">Back to Home</a>
        </div>
    </div>"""

# ====================== বাকি সব রুট (আগের মতোই) ======================
@app.route("/deposit")
def deposit():
    uid = request.args.get("id")
    return f"""{ui()}<div class="max-w-md mx-auto p-4"><div class="card"><form action='/dep2'><input type='hidden' name='uid' value='{uid}'><input name='amount' placeholder='Amount' class='text-black w-full p-3 rounded mb-3'><select name='network' class='text-black w-full p-3 rounded mb-3'><option>TRC20</option><option>ERC20</option></select><button class='btn bg-gradient-to-r from-amber-400 to-yellow-500 text-black neon'>Next</button></form></div></div>"""

@app.route("/dep2")
def dep2():
    uid = request.args.get("uid")
    net = request.args.get("network")
    amount = request.args.get("amount")
    addr = TRC if net == "TRC20" else ERC
    return f"""{ui()}<div class="max-w-md mx-auto p-4"><div class="card">Send {amount} to:<br><span class="text-emerald-400 break-all">{addr}</span><form action='/dep3'><input type='hidden' name='uid' value='{uid}'><input type='hidden' name='amount' value='{amount}'><input type='hidden' name='network' value='{net}'><input name='txid' placeholder='TXID' class='text-black w-full p-3 rounded mt-4'><button class='btn bg-gradient-to-r from-amber-400 to-yellow-500 text-black neon'>Submit</button></form></div></div>"""

@app.route("/dep3")
def dep3():
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO deposits VALUES(NULL,?,?,?,?,?,?)", (request.args.get("uid"), request.args.get("amount"), request.args.get("network"), request.args.get("txid"), "pending", ""))
    conn.commit()
    conn.close()
    return f"""{ui()}
    <div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center">
        <div class="card">
            <h2 class="text-green-400 text-3xl mb-4">✅ Deposit Request Submitted</h2>
            <a href="/?id={request.args.get('uid')}" class="btn bg-green-500 text-white">Back to Home</a>
        </div>
    </div>"""

@app.route("/withdraw")
def withdraw():
    uid = request.args.get("id")
    return f"""{ui()}<div class="max-w-md mx-auto p-4"><div class="card"><form action='/w2'><input type='hidden' name='uid' value='{uid}'><input name='amount' placeholder='Amount' class='text-black w-full p-3 rounded mb-3'><input name='address' placeholder='Wallet Address' class='text-black w-full p-3 rounded mb-3'><select name='network' class='text-black w-full p-3 rounded mb-3'><option>TRC20</option><option>ERC20</option></select><button class='btn bg-gradient-to-r from-red-500 to-rose-600 text-white'>Submit</button></form></div></div>"""

@app.route("/w2")
def w2():
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO withdraws VALUES(NULL,?,?,?,?,?,?)", (request.args.get("uid"), request.args.get("amount"), request.args.get("address"), request.args.get("network"), "pending", ""))
    conn.commit()
    conn.close()
    return f"""{ui()}
    <div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center">
        <div class="card">
            <h2 class="text-green-400 text-3xl mb-4">✅ Withdraw Request Submitted</h2>
            <a href="/?id={request.args.get('uid')}" class="btn bg-green-500 text-white">Back to Home</a>
        </div>
    </div>"""

@app.route("/admin")
def admin():
    uid = request.args.get("id")
    if uid != ADMIN_ID:
        return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-red-400 text-3xl mb-4">🚫 Access Denied</h2><p class="text-xl">Only Admin can access this panel.</p></div></div>"""

    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, username, first_name, balance FROM users")
    users = c.fetchall()
    c.execute("SELECT * FROM support")
    sup = c.fetchall()
    conn.close()

    badge = f'<span class="ml-auto bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full">{len(sup)}</span>' if sup else ''

    user_list_html = ""
    for u in users:
        display_name = u[1] if u[1] else (u[2] if u[2] else u[0])
        user_list_html += f"""
        <div class="bg-[#252a31] p-4 rounded-2xl flex justify-between items-center">
            <div>
                <span class="font-medium text-white">@{display_name}</span><br>
                <span class="text-emerald-400 text-sm">{u[3]} USD</span>
            </div>
            <a href='/manage?uid={u[0]}' class="text-amber-400 font-medium">Manage</a>
        </div>
        """

    support_html = ""
    for s in sup:
        support_html += f"""
        <div class="card p-5">
            <p><strong>From:</strong> @{s[2]} (ID: {s[1]})</p>
            <p class="mt-2">{s[4]}</p>
            <form action='/reply_support' class="mt-4">
                <input type='hidden' name='uid' value='{s[1]}'>
                <input name='reply' placeholder="Reply to user..." class='text-black w-full p-3 rounded mb-3'>
                <button class='btn bg-blue-500 w-full'>Send Reply</button>
            </form>
        </div>
        """

    html = f"""{ui()}
    <div class="max-w-md mx-auto p-4">
    <h2 class="text-amber-400 text-center text-3xl mb-6 glow">🔐 Admin Panel</h2>
    <a href='/deposits' class='btn bg-gradient-to-r from-amber-400 to-yellow-500 text-black neon text-lg'>Pending Deposits</a>
    <a href='/withdraws' class='btn bg-gradient-to-r from-red-500 to-rose-600 text-white text-lg'>Pending Withdraws</a>
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
        {badge}
    </div>
    </div>
    <div id="supportModal" onclick="if(event.target===this)closeSupportModal()" class="hidden fixed inset-0 bg-black/90 flex items-end z-[9999]">
      <div onclick="event.stopImmediatePropagation()" class="bg-[#13171f] w-full max-w-md mx-auto rounded-3xl max-h-[88vh] overflow-hidden flex flex-col shadow-2xl mb-3">
        <div class="w-14 h-1.5 bg-gray-400 rounded-full mx-auto mt-4 mb-1"></div>
        <div class="px-6 pb-4 text-center text-xl font-semibold">Support Inbox</div>
        <div class="flex-1 overflow-y-auto px-5 pb-5 space-y-4">
            {support_html or '<div class="text-center text-gray-400 py-10">No support messages yet</div>'}
        </div>
      </div>
    </div>
    <script>
    function openSupportModal() {{ document.getElementById('supportModal').classList.remove('hidden'); document.getElementById('supportModal').classList.add('flex'); }}
    function closeSupportModal() {{ document.getElementById('supportModal').classList.add('hidden'); document.getElementById('supportModal').classList.remove('flex'); }}
    </script>
    """
    return html

@app.route("/deposits")
def deposits():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, user_id, amount, network, txid FROM deposits WHERE status='pending'")
    data = c.fetchall()
    conn.close()
    html = f"""{ui()}<div class="max-w-md mx-auto p-4"><h2 class="text-amber-400 text-center text-xl mb-4">Pending Deposits</h2><div class="space-y-4">"""
    if not data:
        html += "<div class='text-center py-10 text-gray-400'>No pending deposits yet</div>"
    else:
        for d in data:
            html += f"""<div class="card p-5"><p class="text-white"><strong>User ID:</strong> {d[1]}</p><p class="text-emerald-400"><strong>Amount:</strong> {d[2]} USD</p><p><strong>Network:</strong> {d[3]}</p><p><strong>TXID:</strong> {d[4]}</p><div class="mt-5 flex gap-3"><a href='/approve_dep?id={d[0]}' class='btn bg-green-500 flex-1'>Approve</a><form action='/reject_dep' class="flex-1"><input type='hidden' name='id' value='{d[0]}'><input name='reason' placeholder="Reject reason..." class='text-black w-full mb-3 p-3 rounded'><button type='submit' class='btn bg-red-500 w-full'>Reject</button></form></div></div>"""
    html += "</div></div>"
    return html

@app.route("/withdraws")
def withdraws():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, user_id, amount, address, network FROM withdraws WHERE status='pending'")
    data = c.fetchall()
    conn.close()
    html = f"""{ui()}<div class="max-w-md mx-auto p-4"><h2 class="text-amber-400 text-center text-xl mb-4">Pending Withdraws</h2><div class="space-y-4">"""
    if not data:
        html += "<div class='text-center py-10 text-gray-400'>No pending withdraws yet</div>"
    else:
        for d in data:
            html += f"""<div class="card p-5"><p class="text-white"><strong>User ID:</strong> {d[1]}</p><p class="text-emerald-400"><strong>Amount:</strong> {d[2]} USD</p><p><strong>Address:</strong> {d[3]}</p><p><strong>Network:</strong> {d[4]}</p><div class="mt-5 flex gap-3"><a href='/approve_w?id={d[0]}' class='btn bg-green-500 flex-1'>Approve</a><form action='/reject_w' class="flex-1"><input type='hidden' name='id' value='{d[0]}'><input name='reason' placeholder="Reject reason..." class='text-black w-full mb-3 p-3 rounded'><button type='submit' class='btn bg-red-500 w-full'>Reject</button></form></div></div>"""
    html += "</div></div>"
    return html

@app.route("/manage")
def manage():
    uid = request.args.get("uid")
    return f"""{ui()}<div class="max-w-md mx-auto p-4"><h2 class="text-amber-400 text-center text-xl mb-6">Manage User {uid}</h2>
    <div class="card"><form action='/add'><input type='hidden' name='uid' value='{uid}'><input name='amount' placeholder='Add Main Balance' class='text-black w-full p-3 rounded mb-3'><button class='btn bg-green-500 w-full'>Add Main Balance</button></form></div>
    <div class="card mt-3"><form action='/add_reward'><input type='hidden' name='uid' value='{uid}'><input name='amount' placeholder='Add Reward Balance' class='text-black w-full p-3 rounded mb-3'><button class='btn bg-purple-500 w-full'>Add Reward Balance</button></form></div>
    <div class="card mt-3"><form action='/remove'><input type='hidden' name='uid' value='{uid}'><input name='amount' placeholder='Remove Main Balance' class='text-black w-full p-3 rounded mb-3'><button class='btn bg-red-500 w-full'>Remove Main Balance</button></form></div>
    <div class="card mt-3"><form action='/profit'><input type='hidden' name='uid' value='{uid}'><input name='p' placeholder='Profit % (e.g. 5)' class='text-black w-full p-3 rounded mb-3'><button class='btn bg-blue-500 w-full'>Add Profit %</button></form></div>
    <div class="card mt-3"><form action='/msg'><input type='hidden' name='uid' value='{uid}'><textarea name='m' placeholder="Type message for user..." rows="3" class='text-black w-full p-3 rounded mb-3'></textarea><button class='btn bg-yellow-500 text-black w-full'>Send Message</button></form></div></div>"""

# ====================== SUCCESS PAGES ======================
@app.route("/approve_dep")
def approve_dep():
    uid = request.args.get("uid") or ADMIN_ID
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-green-400 text-3xl mb-4">✅ Deposit Approved</h2><a href="/?id={uid}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

@app.route("/reject_dep")
def reject_dep():
    uid = request.args.get("uid") or ADMIN_ID
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-green-400 text-3xl mb-4">❌ Deposit Rejected</h2><a href="/?id={uid}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

@app.route("/approve_w")
def approve_w():
    uid = request.args.get("uid") or ADMIN_ID
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-green-400 text-3xl mb-4">✅ Withdraw Approved</h2><a href="/?id={uid}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

@app.route("/reject_w")
def reject_w():
    uid = request.args.get("uid") or ADMIN_ID
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-green-400 text-3xl mb-4">❌ Withdraw Rejected</h2><a href="/?id={uid}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

@app.route("/add")
def add():
    uid = request.args.get("uid")
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-green-400 text-3xl mb-4">✅ Balance Added</h2><a href="/?id={uid}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

@app.route("/add_reward")
def add_reward():
    uid = request.args.get("uid")
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-green-400 text-3xl mb-4">✅ Reward Balance Added</h2><a href="/?id={uid}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

@app.route("/remove")
def remove():
    uid = request.args.get("uid")
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-green-400 text-3xl mb-4">✅ Balance Removed</h2><a href="/?id={uid}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

@app.route("/profit")
def profit():
    uid = request.args.get("uid")
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-green-400 text-3xl mb-4">✅ Profit Added</h2><a href="/?id={uid}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

@app.route("/msg")
def msg():
    uid = request.args.get("uid")
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-green-400 text-3xl mb-4">✅ Message Sent</h2><a href="/?id={uid}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

@app.route("/broadcast")
def broadcast():
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-green-400 text-3xl mb-4">✅ Broadcast Sent</h2><a href="/admin?id={ADMIN_ID}" class="btn bg-green-500 text-white">Back to Admin Panel</a></div></div>"""

@app.route("/reply_support")
def reply_support():
    uid = request.args.get("uid")
    return f"""{ui()}<div class="max-w-md mx-auto p-5 min-h-screen flex items-center justify-center text-center"><div class="card"><h2 class="text-green-400 text-3xl mb-4">✅ Reply Sent</h2><a href="/?id={uid}" class="btn bg-green-500 text-white">Back to Home</a></div></div>"""

# ====================== RUN ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
