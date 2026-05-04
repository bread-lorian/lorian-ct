# -*- coding: utf-8 -*-
import os, sys, io, json
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import uuid, sqlite3
from flask import Flask, render_template, request, jsonify, g
from openai import OpenAI

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# ── 配置文件路径 ──────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DATABASE = os.path.join(BASE_DIR, "notebook.db")

# ── 默认配置 ──────────────────────────────────────────
DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat"
}

# ── 配置读写 ──────────────────────────────────────────
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def get_ai_client():
    cfg = load_config()
    if not cfg.get("api_key"):
        return None, None
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    return client, cfg.get("model", "deepseek-chat")

# ── AI 提示词 ──────────────────────────────────────────
SYSTEM_PROMPT = """你是"lorian-ct"，一位温暖耐心的AI学习辅导伙伴。

## 关于你自己
- 你叫"lorian-ct"，是 Lorian-ct 项目的AI助手
- 你由**落雨纪元算法与数据研究中心团队**所开发
- 你当前是**第一代版本**，属于**测试版本**
- 当用户问你是谁、谁开发的、这是什么项目时，按以上信息回答

## 核心原则
- **绝不直接给出正确答案**，引导学生自己发现错误并找到正确解法
- **每次只引导一步**，循序渐进，不要一次给太多信息
- **用提问代替讲解**，激发学生主动思考

## 引导流程

### 阶段1：诊断错因
收到错题后：
1. 简短肯定学生纠错的态度（一两句话即可）
2. 分析错误类型：概念理解偏差 / 计算过程失误 / 审题不仔细 / 方法选择不当
3. 指出具体出错的环节，但**不展示正确做法**

### 阶段2：启发思考
- 提出一个精准的引导性问题
- 引导学生重新审视出错的那一步
- 如果是数学题，可以让学生重新检查某个条件或公式

### 阶段3：递进提示
如果学生仍然困惑：
- 给出一个更具体的提示（相关知识点、公式）
- 用类比或生活中的例子帮助理解
- 但依然保留关键步骤让学生自己完成

### 阶段4：巩固总结
当学生理解后：
- 真诚地肯定学生的进步
- 用 2-3 句话总结关键知识点
- 指出一个常见的变式或易错点

## 语言风格
- 用"你"称呼学生，语气亲切自然
- 回复简洁有力，每次 80-200 字
- 数学公式用 LaTeX：行内 $...$ ，独立行 $$...$$

## 特殊情况
- 学生直接要答案 → 温和拒绝："直接看答案多没意思呀，来，我们一起想想……"
- 题目信息不完整 → 请学生补充
- 学生答对了 → 热情肯定并总结"""

# ── 数据库 ──────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '新错题',
                subject TEXT DEFAULT '其他',
                mastered INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );
        """)
        db.commit()

# ── 路由 ────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/config", methods=["GET"])
def get_config():
    cfg = load_config()
    return jsonify({
        "configured": bool(cfg.get("api_key")),
        "api_key": cfg.get("api_key", ""),
        "base_url": cfg.get("base_url", ""),
        "model": cfg.get("model", "")
    })

@app.route("/api/config", methods=["POST"])
def set_config():
    d = request.json or {}
    cfg = load_config()
    cfg["api_key"] = d.get("api_key", cfg.get("api_key", ""))
    cfg["base_url"] = d.get("base_url", cfg.get("base_url", ""))
    cfg["model"] = d.get("model", cfg.get("model", ""))
    save_config(cfg)

    # 测试连接
    if cfg.get("api_key"):
        try:
            client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
            client.chat.completions.create(
                model=cfg["model"],
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )
            return jsonify({"ok": True, "message": "配置成功，AI 连接正常！"})
        except Exception as e:
            return jsonify({"ok": False, "message": f"API Key 无法连接：{e}"})
    return jsonify({"ok": False, "message": "请填写 API Key"})

@app.route("/api/sessions")
def list_sessions():
    rows = get_db().execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/sessions", methods=["POST"])
def create_session():
    d = request.json or {}
    sid = uuid.uuid4().hex[:8]
    get_db().execute("INSERT INTO sessions (id,title,subject) VALUES (?,?,?)",
        (sid, d.get("title","新错题"), d.get("subject","其他")))
    get_db().commit()
    return jsonify({"id": sid, "title": d.get("title","新错题"), "subject": d.get("subject","其他")})

@app.route("/api/sessions/<sid>", methods=["DELETE"])
def delete_session(sid):
    db = get_db()
    db.execute("DELETE FROM messages WHERE session_id=?", (sid,))
    db.execute("DELETE FROM sessions WHERE id=?", (sid,))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/sessions/<sid>/mastered", methods=["PUT"])
def toggle_mastered(sid):
    db = get_db()
    row = db.execute("SELECT mastered FROM sessions WHERE id=?", (sid,)).fetchone()
    if not row:
        return jsonify({"error":"not found"}), 404
    val = 0 if row["mastered"] else 1
    db.execute("UPDATE sessions SET mastered=? WHERE id=?", (val, sid))
    db.commit()
    return jsonify({"mastered": val})

@app.route("/api/sessions/<sid>/messages")
def list_messages(sid):
    rows = get_db().execute("SELECT * FROM messages WHERE session_id=? ORDER BY created_at", (sid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/chat", methods=["POST"])
def chat():
    d = request.json or {}
    sid = d.get("session_id","")
    text = (d.get("message") or "").strip()
    if not text:
        return jsonify({"error":"消息不能为空"}), 400

    client, model = get_ai_client()
    if not client:
        return jsonify({"error":"请先配置 API Key"}), 400

    db = get_db()
    db.execute("INSERT INTO messages (session_id,role,content) VALUES (?,?,?)", (sid,"user",text))
    cnt = db.execute("SELECT COUNT(*) AS c FROM messages WHERE session_id=?", (sid,)).fetchone()["c"]
    if cnt == 1:
        title = text[:30]+("..." if len(text)>30 else "")
        db.execute("UPDATE sessions SET title=? WHERE id=?", (title, sid))
    db.commit()
    history = db.execute("SELECT role,content FROM messages WHERE session_id=? ORDER BY created_at", (sid,)).fetchall()
    messages = [{"role":"system","content":SYSTEM_PROMPT}]
    for m in history:
        messages.append({"role":m["role"],"content":m["content"]})
    try:
        resp = client.chat.completions.create(model=model, messages=messages, temperature=0.7, max_tokens=800)
        reply = resp.choices[0].message.content
    except Exception as e:
        reply = f"AI服务出了点问题，请检查API配置。\n\n错误详情：{e}"
    db.execute("INSERT INTO messages (session_id,role,content) VALUES (?,?,?)", (sid,"assistant",reply))
    db.execute("UPDATE sessions SET updated_at=datetime('now','localtime') WHERE id=?", (sid,))
    db.commit()
    return jsonify({"message": reply})

# ── 启动 ────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print()
    print("      ██╗      ██████╗ ██████╗ ██╗ █████╗ ███╗   ██╗")
    print("      ██║     ██╔═══██╗██╔══██╗██║██╔══██╗████╗  ██║")
    print("      ██║     ██║   ██║██████╔╝██║███████║██╔██╗ ██║")
    print("      ██║     ██║   ██║██╔══██╗██║██╔══██║██║╚██╗██║")
    print("      ███████╗╚██████╔╝██║  ██║██║██║  ██║██║ ╚████║")
    print("      ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝")
    print()
    print("      ████████╗ ██████╗████████╗")
    print("      ╚══██╔══╝██╔════╝╚══██╔══╝")
    print("         ██║   ██║        ██║   ")
    print("         ██║   ██║        ██║   ")
    print("         ██║   ╚██████╗   ██║   ")
    print("         ╚═╝    ╚═════╝   ╚═╝   ")
    print()
    print("    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("      lorian-ct · AI错题本")
    print("      由落雨纪元算法与数据研究中心团队开发")
    print("      当前版本: 第一代 · Deam测试版")
    print()
    print("      官网:  www.luoyeltd.com.cn")
    print("      博客:  blog.luoyeltd.com.cn")
    print("      (C) 落雨纪元算法与数据研究中心团队")
    print()
    print("    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("      服务已启动!")
    print("      请访问 http://localhost:5000")
    print("      按 Ctrl+C 停止服务")
    print()
    print("    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    app.run(debug=True, port=5000)
