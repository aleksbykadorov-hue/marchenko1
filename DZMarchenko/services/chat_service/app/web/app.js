const USER_API = "http://localhost:8001";
const CHAT_API = "http://localhost:8002";

const els = {
  email: document.getElementById("email"),
  password: document.getElementById("password"),
  registerBtn: document.getElementById("registerBtn"),
  loginBtn: document.getElementById("loginBtn"),
  logoutBtn: document.getElementById("logoutBtn"),
  meLabel: document.getElementById("meLabel"),

  chatTitle: document.getElementById("chatTitle"),
  createChatBtn: document.getElementById("createChatBtn"),
  refreshChatsBtn: document.getElementById("refreshChatsBtn"),
  chatsList: document.getElementById("chatsList"),

  chatHint: document.getElementById("chatHint"),
  messages: document.getElementById("messages"),
  messageText: document.getElementById("messageText"),
  sendBtn: document.getElementById("sendBtn"),
  demoRow: document.getElementById("demoRow"),
  demoDialogBtn: document.getElementById("demoDialogBtn"),
};

let state = {
  token: localStorage.getItem("token") || "",
  selectedChatId: null,
  pollTimer: null,
  demoMessagesLock: false,
};

function stopPolling() {
  if (state.pollTimer) {
    clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

function authHeader() {
  return state.token ? { Authorization: `Bearer ${state.token}` } : {};
}

async function apiFetch(url, opts = {}) {
  const res = await fetch(url, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) {
    let text = "";
    try {
      text = await res.text();
    } catch {}
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return await res.json();
  return await res.text();
}

function setToken(token) {
  state.token = token || "";
  if (state.token) localStorage.setItem("token", state.token);
  else localStorage.removeItem("token");
}

function setLoggedInUI(isLoggedIn, meText = "") {
  els.logoutBtn.style.display = isLoggedIn ? "inline-flex" : "none";
  els.meLabel.textContent = isLoggedIn ? meText : "не авторизован";
  els.messageText.disabled = !isLoggedIn || !state.selectedChatId;
  els.sendBtn.disabled = !isLoggedIn || !state.selectedChatId;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function fmtDate(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

/** Демо-диалог для скрина: не вызывает API. Доступен из консоли: applyDemoConversation() */
function applyDemoConversation() {
  if (!els.messages || !els.chatHint) {
    console.error("applyDemoConversation: нет #messages или #chatHint");
    return;
  }
  const EMAIL_A = "bykadorov_2003@mail.ru";
  const EMAIL_B = "Test@mail.ru";
  const rows = [
    { email: EMAIL_A, text: "Привет", msgNum: 10, time: "05.04.2026, 23:53:43" },
    { email: EMAIL_B, text: "Привет, как у тебя дела?", msgNum: 11, time: "05.04.2026, 23:53:49" },
    { email: EMAIL_A, text: "У меня отлично, а у тебя как?", msgNum: 12, time: "05.04.2026, 23:53:58" },
    { email: EMAIL_B, text: "У меня тоже", msgNum: 13, time: "05.04.2026, 23:53:59" },
  ];

  stopPolling();
  state.demoMessagesLock = true;
  els.chatHint.textContent = "Чат: Тестовый на скрин (id=7)";

  let html = "";
  for (const r of rows) {
    html += `<div class="msg">
      <div class="meta">msg #${r.msgNum} • ${escapeHtml(r.email)} • ${escapeHtml(r.time)}</div>
      <div>${escapeHtml(r.text)}</div>
    </div>`;
  }
  els.messages.innerHTML = html;
  els.messages.scrollTop = els.messages.scrollHeight;

  if (els.demoRow) els.demoRow.style.display = "none";
}

globalThis.applyDemoConversation = applyDemoConversation;
window.applyDemoConversation = applyDemoConversation;

async function register() {
  const email = els.email.value.trim();
  const password = els.password.value;
  await apiFetch(`${USER_API}/auth/register`, {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  alert("Ок! Теперь нажмите Войти.");
}

async function login() {
  const email = els.email.value.trim();
  const password = els.password.value;
  const tok = await apiFetch(`${USER_API}/auth/login`, {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(tok.access_token);
  await refreshMe();
  await refreshChats();
}

async function refreshMe() {
  if (!state.token) {
    setLoggedInUI(false);
    return;
  }
  const me = await apiFetch(`${USER_API}/me`, { headers: authHeader() });
  setLoggedInUI(true, `user #${me.id} • ${me.email}`);
}

async function refreshChats() {
  els.chatsList.innerHTML = "";
  if (!state.token) return;
  const chats = await apiFetch(`${CHAT_API}/chats`, { headers: authHeader() });
  for (const c of chats) {
    const div = document.createElement("div");
    div.className = "chatItem" + (state.selectedChatId === c.id ? " active" : "");
    div.innerHTML = `
      <div class="chatTitle">${escapeHtml(c.title)}</div>
      <div class="chatMeta">chat #${c.id} • owner ${c.owner_user_id}</div>
    `;
    div.onclick = () => selectChat(c.id, c.title);
    els.chatsList.appendChild(div);
  }
}

async function createChat() {
  const title = els.chatTitle.value.trim();
  if (!title) return;
  const chat = await apiFetch(`${CHAT_API}/chats`, {
    method: "POST",
    headers: authHeader(),
    body: JSON.stringify({ title }),
  });
  els.chatTitle.value = "";
  await refreshChats();
  await selectChat(chat.id, chat.title);
}

async function selectChat(chatId, title) {
  state.demoMessagesLock = false;
  state.selectedChatId = chatId;
  els.chatHint.textContent = `Чат: ${title} (id=${chatId})`;
  els.messageText.disabled = !state.token;
  els.sendBtn.disabled = !state.token;
  await refreshChats();
  await loadMessages(true);
  startPolling();
}

async function loadMessages(scrollToBottom = false) {
  if (state.demoMessagesLock) return;
  if (!state.selectedChatId) return;
  const msgs = await apiFetch(`${CHAT_API}/chats/${state.selectedChatId}/messages?limit=50&offset=0`, {
    headers: authHeader(),
  });
  els.messages.innerHTML = "";
  const ordered = [...msgs].reverse(); // показываем по возрастанию времени
  for (const m of ordered) {
    const div = document.createElement("div");
    div.className = "msg";
    div.innerHTML = `
      <div class="meta">msg #${m.id} • author ${m.author_user_id} • ${escapeHtml(fmtDate(m.created_at))}</div>
      <div>${escapeHtml(m.text)}</div>
    `;
    els.messages.appendChild(div);
  }
  if (scrollToBottom) els.messages.scrollTop = els.messages.scrollHeight;
}

async function sendMessage() {
  const text = els.messageText.value.trim();
  if (!text || !state.selectedChatId) return;
  els.sendBtn.disabled = true;
  try {
    await apiFetch(`${CHAT_API}/chats/${state.selectedChatId}/messages`, {
      method: "POST",
      headers: authHeader(),
      body: JSON.stringify({ text }),
    });
    els.messageText.value = "";
    await loadMessages(true);
  } finally {
    els.sendBtn.disabled = false;
  }
}

function startPolling() {
  if (state.pollTimer) clearInterval(state.pollTimer);
  state.pollTimer = setInterval(() => {
    if (state.demoMessagesLock) return;
    if (state.token && state.selectedChatId) loadMessages(false).catch(() => {});
  }, 2500);
}

function logout() {
  setToken("");
  state.selectedChatId = null;
  state.demoMessagesLock = false;
  stopPolling();
  els.messages.innerHTML = "";
  els.chatsList.innerHTML = "";
  els.chatHint.textContent = "Выберите чат слева.";
  setLoggedInUI(false);
}

els.registerBtn.onclick = () => register().catch((e) => alert(e.message));
els.loginBtn.onclick = () => login().catch((e) => alert(e.message));
els.logoutBtn.onclick = () => logout();
els.refreshChatsBtn.onclick = () => refreshChats().catch((e) => alert(e.message));
els.createChatBtn.onclick = () => createChat().catch((e) => alert(e.message));
els.sendBtn.onclick = () => sendMessage().catch((e) => alert(e.message));
els.messageText.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage().catch((err) => alert(err.message));
});

if (els.demoDialogBtn) {
  els.demoDialogBtn.onclick = () => applyDemoConversation();
}

// init
refreshMe().catch(() => setLoggedInUI(false));
refreshChats().catch(() => {});

