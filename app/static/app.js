const SESSION_KEY = "langgraph-agent-ui-sessions";

const nodesToAgents = {
  supervisor: "supervisor",
  planning: "planning",
  research: "research",
  coding: "coding",
  rag: "rag",
  direct: "supervisor",
  aggregate: "aggregate",
};

const state = {
  sessions: loadSessions(),
  activeSessionId: null,
  running: false,
};

const elements = {
  sessionList: document.querySelector("#sessionList"),
  sessionTitle: document.querySelector("#sessionTitle"),
  newSessionButton: document.querySelector("#newSessionButton"),
  clearSessionsButton: document.querySelector("#clearSessionsButton"),
  messages: document.querySelector("#messages"),
  chatForm: document.querySelector("#chatForm"),
  messageInput: document.querySelector("#messageInput"),
  sendButton: document.querySelector("#sendButton"),
  connectionStatus: document.querySelector("#connectionStatus"),
  activeAgent: document.querySelector("#activeAgent"),
  routeStatus: document.querySelector("#routeStatus"),
};

function loadSessions() {
  const raw = localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return [];
  }
  try {
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

function saveSessions() {
  localStorage.setItem(SESSION_KEY, JSON.stringify(state.sessions));
}

function createSession() {
  const now = new Date();
  const session = {
    id: `session-${now.getTime()}`,
    title: "New conversation",
    createdAt: now.toISOString(),
    messages: [],
  };
  state.sessions.unshift(session);
  state.activeSessionId = session.id;
  saveSessions();
  render();
}

function getActiveSession() {
  return state.sessions.find((session) => session.id === state.activeSessionId);
}

function setActiveSession(sessionId) {
  state.activeSessionId = sessionId;
  resetAgentStrip();
  render();
}

function addMessage(role, content) {
  const session = getActiveSession();
  if (!session) {
    return;
  }
  session.messages.push({ role, content, at: new Date().toISOString() });
  if (role === "user" && session.title === "New conversation") {
    session.title = content.slice(0, 48) || "Conversation";
  }
  saveSessions();
  renderMessages(session);
  renderSessions();
  scrollMessagesToBottom();
}

function render() {
  if (!state.activeSessionId && state.sessions.length > 0) {
    state.activeSessionId = state.sessions[0].id;
  }
  if (state.sessions.length === 0) {
    createSession();
    return;
  }
  renderSessions();
  renderMessages(getActiveSession());
}

function renderSessions() {
  elements.sessionList.innerHTML = "";
  for (const session of state.sessions) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `session-item ${session.id === state.activeSessionId ? "active" : ""}`;
    button.innerHTML = `<strong>${escapeHtml(session.title)}</strong><small>${session.messages.length} messages</small>`;
    button.addEventListener("click", () => setActiveSession(session.id));
    elements.sessionList.appendChild(button);
  }
  const active = getActiveSession();
  elements.sessionTitle.textContent = active?.title || "New conversation";
}

function renderMessages(session) {
  elements.messages.innerHTML = "";
  for (const message of session?.messages || []) {
    const bubble = document.createElement("article");
    bubble.className = `message ${message.role}`;
    bubble.textContent = message.content;
    elements.messages.appendChild(bubble);
  }
  scrollMessagesToBottom();
}

function scrollMessagesToBottom() {
  requestAnimationFrame(() => {
    elements.messages.scrollTop = elements.messages.scrollHeight;
  });
}

function setRunning(isRunning) {
  state.running = isRunning;
  elements.sendButton.disabled = isRunning;
  elements.messageInput.disabled = isRunning;
  elements.connectionStatus.textContent = isRunning ? "Running" : "Ready";
  elements.connectionStatus.className = `status-pill ${isRunning ? "running" : ""}`;
}

function resetAgentStrip() {
  document.querySelectorAll(".agent-step").forEach((node) => {
    node.classList.remove("active", "done", "skipped");
  });
  elements.activeAgent.textContent = "No agent running";
  elements.routeStatus.textContent = "Waiting for request";
}

function markAgent(agentName, status = "active") {
  const agentNode = document.querySelector(`[data-agent="${agentName}"]`);
  if (!agentNode) {
    return;
  }
  document.querySelectorAll(".agent-step.active").forEach((node) => {
    node.classList.remove("active");
    node.classList.add("done");
  });
  agentNode.classList.remove("skipped");
  agentNode.classList.add(status);
  elements.activeAgent.textContent = `${labelFor(agentName)} agent working`;
  elements.routeStatus.textContent = `${labelFor(agentName)} running`;
}

function markRoute(routeName) {
  const specialistAgents = ["planning", "research", "coding", "rag"];
  specialistAgents.forEach((agentName) => {
    const node = document.querySelector(`[data-agent="${agentName}"]`);
    if (!node) {
      return;
    }
    node.classList.toggle("skipped", routeName !== agentName);
  });
  elements.routeStatus.textContent = `Route: ${labelFor(routeName)}`;
}

async function sendMessage(message) {
  const session = getActiveSession();
  if (!session) {
    return;
  }

  addMessage("user", message);
  resetAgentStrip();
  setRunning(true);

  try {
    const response = await fetch("/api/v1/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: session.id, message, stream: true }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    await readSseStream(response.body.getReader());
  } catch (error) {
    elements.connectionStatus.textContent = "Error";
    elements.connectionStatus.className = "status-pill error";
    addMessage("system", error.message);
  } finally {
    document.querySelectorAll(".agent-step.active").forEach((node) => {
      node.classList.remove("active");
      node.classList.add("done");
    });
    elements.activeAgent.textContent = "No agent running";
    elements.routeStatus.textContent = "Completed";
    setRunning(false);
  }
}

async function readSseStream(reader) {
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() || "";
    for (const frame of frames) {
      handleSseFrame(frame);
    }
  }
}

function handleSseFrame(frame) {
  const line = frame.split("\n").find((item) => item.startsWith("data: "));
  if (!line) {
    return;
  }
  const payload = line.slice(6);
  if (payload === "[DONE]") {
    return;
  }

  const update = JSON.parse(payload);
  const agentName = nodesToAgents[update.event];
  if (agentName) {
    markAgent(agentName);
  }

  if (update.event === "supervisor" && update.data?.route) {
    markRoute(update.data.route);
    addMessage("system", `Supervisor routed this request to: ${update.data.route}`);
  }

  if (update.event === "aggregate" && update.data?.final_response) {
    addMessage("assistant", update.data.final_response);
  }

  if (update.data?.error) {
    addMessage("system", update.data.error);
  }
}

function labelFor(agentName) {
  return agentName.charAt(0).toUpperCase() + agentName.slice(1);
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return entities[char];
  });
}

elements.newSessionButton.addEventListener("click", createSession);
elements.clearSessionsButton.addEventListener("click", () => {
  state.sessions = [];
  state.activeSessionId = null;
  saveSessions();
  resetAgentStrip();
  render();
});

elements.chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = elements.messageInput.value.trim();
  if (!message || state.running) {
    return;
  }
  elements.messageInput.value = "";
  sendMessage(message);
});

elements.messageInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey) {
    return;
  }
  event.preventDefault();
  elements.chatForm.requestSubmit();
});

render();
