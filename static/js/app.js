// ── 全局状态 ──
const S = {
    sessions: [],
    sid: null,
    subject: '数学',
    loading: false,
    configured: false
};

// ── 工具函数 ──

async function api(method, url, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    return (await fetch(url, opts)).json();
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

function md(t) {
    try {
        return marked.parse(t);
    } catch (e) {
        return t.replace(/\n/g, '<br>');
    }
}

function scrollBottom() {
    const c = document.getElementById('cMsgs');
    c.scrollTop = c.scrollHeight;
}

// ── 屏幕切换 ──

function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
    document.getElementById(id).classList.remove('hidden');
}

function goWelcome() {
    S.sid = null;
    showScreen('sWelcome');
    renderList();
}

// ── 侧边栏 ──

function openSidebar() {
    document.getElementById('sidebar').classList.add('open');
    document.getElementById('overlay').classList.add('show');
}

function closeSidebar() {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('overlay').classList.remove('show');
}

// ── 配置检查 ──

async function checkConfig() {
    const r = await api('GET', '/api/config');
    S.configured = r.configured;
    if (!r.configured) {
        showScreen('sSettings');
    }
}

// ── 设置页 ──

function showSettings() {
    closeSidebar();
    api('GET', '/api/config').then(r => {
        document.getElementById('cfgKey').value = r.api_key || '';
        document.getElementById('cfgUrl').value = r.base_url || 'https://api.deepseek.com';
        document.getElementById('cfgModel').value = r.model || 'deepseek-chat';
    });
    document.getElementById('testResult').style.display = 'none';
    showScreen('sSettings');
}

// 切换服务商
document.getElementById('providerPills').addEventListener('click', e => {
    const p = e.target.closest('.pill');
    if (!p) return;
    document.querySelectorAll('#providerPills .pill').forEach(x => x.classList.remove('on'));
    p.classList.add('on');
    document.getElementById('cfgUrl').value = p.dataset.url;
    document.getElementById('cfgModel').value = p.dataset.model;
    const hint = document.getElementById('providerHint');
    const link = document.getElementById('providerLink');
    const name = p.dataset.hint;
    const regUrl = p.dataset.reg;
    hint.innerHTML = name + ': <a href="' + regUrl + '" target="_blank" id="providerLink">' + regUrl.replace('https://', '') + '</a> 注册后获取';
});

async function saveSettings() {
    const key = document.getElementById('cfgKey').value.trim();
    const url = document.getElementById('cfgUrl').value.trim();
    const model = document.getElementById('cfgModel').value.trim();
    if (!key) {
        document.getElementById('cfgKey').focus();
        return;
    }
    const btn = document.querySelector('.btn-save');
    btn.textContent = '测试中...';
    btn.disabled = true;
    const r = await api('POST', '/api/config', { api_key: key, base_url: url, model: model });
    const el = document.getElementById('testResult');
    el.style.display = 'block';
    if (r.ok) {
        el.className = 'test-result test-ok';
        el.textContent = '✅ ' + r.message;
        S.configured = true;
        setTimeout(() => goWelcome(), 1500);
    } else {
        el.className = 'test-result test-fail';
        el.textContent = '❌ ' + r.message;
    }
    btn.textContent = '保存并测试';
    btn.disabled = false;
}

// ── 会话列表 ──

async function loadSessions() {
    S.sessions = await api('GET', '/api/sessions');
    renderList();
}

function renderList() {
    const el = document.getElementById('sList');
    if (!S.sessions.length) {
        el.innerHTML = '<p style="color:var(--sidebar-text);text-align:center;padding:32px 16px;font-size:13px;">还没有错题记录<br>点击上方按钮开始</p>';
        return;
    }
    el.innerHTML = S.sessions.map(s => `
        <div class="session-item ${s.id === S.sid ? 'active' : ''}" onclick="openSession('${s.id}')">
            <span class="session-subject sub-${s.subject}">${s.subject}</span>
            <span class="session-title">${esc(s.title)}</span>
            ${s.mastered ? '<span class="mastered-dot"></span>' : ''}
            <button class="session-del" onclick="event.stopPropagation();delSession('${s.id}')">×</button>
        </div>`).join('');
}

async function delSession(id) {
    if (!confirm('确定删除？')) return;
    await api('DELETE', `/api/sessions/${id}`);
    if (S.sid === id) {
        S.sid = null;
        showScreen('sWelcome');
    }
    await loadSessions();
}

// ── 表单 ──

function showForm() {
    if (!S.configured) {
        showSettings();
        return;
    }
    closeSidebar();
    showScreen('sForm');
    document.getElementById('inQ').value = '';
    document.getElementById('inA').value = '';
    document.getElementById('inQ').focus();
}

function hideForm() {
    showScreen(S.sid ? 'sChat' : 'sWelcome');
}

// 学科选择
document.getElementById('pills').addEventListener('click', e => {
    const p = e.target.closest('.pill');
    if (!p) return;
    document.querySelectorAll('#pills .pill').forEach(x => x.classList.remove('on'));
    p.classList.add('on');
    S.subject = p.dataset.s;
});

// ── 聊天 ──

async function openSession(id) {
    S.sid = id;
    closeSidebar();
    const s = S.sessions.find(x => x.id === id);
    document.getElementById('cTitle').textContent = s.title;
    const tag = document.getElementById('cTag');
    tag.textContent = s.subject;
    tag.className = 'sub-tag sub-' + s.subject;
    updMastered(s.mastered);
    showScreen('sChat');
    const msgs = await api('GET', `/api/sessions/${id}/messages`);
    const el = document.getElementById('cMsgs');
    el.innerHTML = msgs.map(m => msgHTML(m)).join('');
    scrollBottom();
    doMath();
    renderList();
}

async function toggleMastered() {
    if (!S.sid) return;
    const r = await api('PUT', `/api/sessions/${S.sid}/mastered`);
    updMastered(r.mastered);
    await loadSessions();
}

function updMastered(v) {
    const b = document.getElementById('cMastered');
    b.textContent = v ? '✅ 已掌握' : '⬜ 标记已掌握';
    b.classList.toggle('is-m', !!v);
}

async function submitQ() {
    const q = document.getElementById('inQ').value.trim();
    const a = document.getElementById('inA').value.trim();
    if (!q) {
        document.getElementById('inQ').focus();
        return;
    }
    const s = await api('POST', '/api/sessions', {
        title: q.slice(0, 30) + (q.length > 30 ? '...' : ''),
        subject: S.subject
    });
    S.sid = s.id;
    await loadSessions();
    document.getElementById('cTitle').textContent = s.title;
    const tag = document.getElementById('cTag');
    tag.textContent = s.subject;
    tag.className = 'sub-tag sub-' + s.subject;
    updMastered(0);
    showScreen('sChat');
    renderList();
    let msg = `【题目】\n${q}`;
    if (a) msg += `\n\n【我的错误答案】\n${a}`;
    document.getElementById('cMsgs').innerHTML = '';
    appendMsg({ role: 'user', content: msg });
    await aiReply(msg);
}

async function sendMsg() {
    const inp = document.getElementById('cInput');
    const text = inp.value.trim();
    if (!text || S.loading) return;
    inp.value = '';
    inp.style.height = 'auto';
    appendMsg({ role: 'user', content: text });
    await aiReply(text);
}

async function aiReply(text) {
    showTyping();
    S.loading = true;
    document.getElementById('cSend').disabled = true;
    try {
        const r = await api('POST', '/api/chat', { session_id: S.sid, message: text });
        hideTyping();
        if (r.error === '请先配置 API Key') {
            appendMsg({
                role: 'assistant',
                content: '请先点击左侧「API 设置」配置 API Key 后再使用。'
            });
            S.loading = false;
            document.getElementById('cSend').disabled = false;
            return;
        }
        appendMsg({ role: 'assistant', content: r.message });
        await loadSessions();
    } catch (e) {
        hideTyping();
        appendMsg({ role: 'assistant', content: '网络出错了，请稍后重试。' });
    }
    S.loading = false;
    document.getElementById('cSend').disabled = false;
}

// ── 消息渲染 ──

function msgHTML(m) {
    const u = m.role === 'user';
    return `<div class="msg ${u ? 'msg-user' : 'msg-ai'}">
        ${u ? '' : '<div class="msg-av">🌧️</div>'}
        <div class="msg-bubble"><div class="msg-content">${md(m.content)}</div></div>
        ${u ? '<div class="msg-av">我</div>' : ''}
    </div>`;
}

function appendMsg(m) {
    document.getElementById('cMsgs').insertAdjacentHTML('beforeend', msgHTML(m));
    scrollBottom();
    doMath();
}

function doMath() {
    if (typeof renderMathInElement === 'function') {
        renderMathInElement(document.getElementById('cMsgs'), {
            delimiters: [
                { left: '$$', right: '$$', display: true },
                { left: '$', right: '$', display: false }
            ],
            throwOnError: false
        });
    }
}

// ── 打字动画 ──

function showTyping() {
    document.getElementById('cMsgs').insertAdjacentHTML('beforeend',
        `<div class="msg msg-ai" id="typingDot">
            <div class="msg-av">🌧️</div>
            <div class="msg-bubble">
                <div class="typing"><span></span><span></span><span></span></div>
            </div>
        </div>`);
    scrollBottom();
}

function hideTyping() {
    const e = document.getElementById('typingDot');
    if (e) e.remove();
}

// ── 输入框事件 ──

const cInput = document.getElementById('cInput');
cInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMsg();
    }
});
cInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 160) + 'px';
});

// ── 初始化 ──

marked.setOptions({ breaks: true, gfm: true });
checkConfig();
loadSessions();
