/**
 * Enterprise RAG Assistant - Frontend Application Logic
 * Full client interacting with FastAPI backend on http://localhost:8000
 */

const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";

let currentSessionId = "session_" + Math.random().toString(36).substring(2, 9);
let chatSessions = [currentSessionId];
let networkGraphData = { nodes: [], links: [] };

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initHealthCheck();
  initChat();
  initSearch();
  initUpload();
  initGraph();
  loadDocuments();
  updateSessionList();
});

/* ==========================================================================
   Navigation & Tabs
   ========================================================================== */
function initTabs() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach((pane) => pane.classList.remove("active"));

      tab.classList.add("active");
      const targetPane = document.getElementById(tab.dataset.tab);
      if (targetPane) targetPane.classList.add("active");

      if (tab.dataset.tab === "graph-tab") {
        fetchGraphTriplets();
      } else if (tab.dataset.tab === "docs-tab") {
        loadDocuments();
      }
    });
  });
}

/* ==========================================================================
   Backend Health Polling
   ========================================================================== */
async function initHealthCheck() {
  const statusPill = document.getElementById("backendStatus");
  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        statusPill.innerHTML = `
          <div class="status-dot"></div>
          <span>Backend: Online (${data.documents_count || 0} Docs)</span>
        `;
        statusPill.style.color = "#34d399";
        statusPill.style.borderColor = "rgba(16, 185, 129, 0.3)";
        document.getElementById("statDocsCount").textContent = data.documents_count || 0;
      } else {
        throw new Error();
      }
    } catch {
      statusPill.innerHTML = `
        <div class="status-dot" style="background:#f43f5e; box-shadow:0 0 8px #f43f5e;"></div>
        <span>Backend: Disconnected</span>
      `;
      statusPill.style.color = "#f43f5e";
      statusPill.style.borderColor = "rgba(244, 63, 94, 0.3)";
    }
  };

  checkHealth();
  setInterval(checkHealth, 10000);
}

/* ==========================================================================
   Conversational RAG Chat
   ========================================================================== */
function initChat() {
  const chatInput = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const newChatBtn = document.getElementById("newChatBtn");

  const sendMessage = async () => {
    const text = chatInput.value.trim();
    if (!text) return;

    chatInput.value = "";
    appendChatMessage("user", text);

    // Placeholder assistant message
    const msgId = "bot_" + Date.now();
    appendChatMessage("assistant", '<div class="typing-indicator">Synthesizing answer with citations...</div>', [], msgId);

    try {
      const res = await fetch(`${API_BASE}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          session_id: currentSessionId,
        }),
      });

      if (!res.ok) throw new Error("Failed to receive response from backend");
      const data = await res.json();

      updateAssistantMessage(msgId, data.response, data.sources || []);
    } catch (err) {
      updateAssistantMessage(
        msgId,
        `⚠️ Error: Could not reach backend server at ${API_BASE}. Make sure the FastAPI server is running with 'python -m app.main'.`
      );
    }
  };

  sendBtn.addEventListener("click", sendMessage);
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  if (newChatBtn) {
    newChatBtn.addEventListener("click", () => {
      currentSessionId = "session_" + Math.random().toString(36).substring(2, 9);
      chatSessions.unshift(currentSessionId);
      updateSessionList();
      document.getElementById("chatMessages").innerHTML = `
        <div class="message-row assistant">
          <div class="message-avatar">AI</div>
          <div class="message-bubble">
            Hello! I am your Enterprise RAG Assistant. Ask me anything about your documents, policies, or financial reports.
          </div>
        </div>
      `;
    });
  }

  // Quick prompt chips
  document.querySelectorAll(".prompt-chips .chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      chatInput.value = chip.textContent.trim();
      chatInput.focus();
    });
  });
}

function appendChatMessage(role, content, sources = [], elementId = null) {
  const container = document.getElementById("chatMessages");
  const row = document.createElement("div");
  row.className = `message-row ${role}`;
  if (elementId) row.id = elementId;

  const avatar = role === "user" ? "You" : "AI";
  let citationsHtml = "";

  if (sources && sources.length > 0) {
    citationsHtml = `
      <div class="citations-box">
        ${sources
          .map(
            (s) => `
          <div class="citation-chip" title="Metadata: ${JSON.stringify(s.metadata || {})}">
            📄 ${s.file_name} ${s.page ? `(p. ${s.page})` : ""}
          </div>
        `
          )
          .join("")}
      </div>
    `;
  }

  row.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-bubble">
      <div class="message-text">${content}</div>
      ${citationsHtml}
    </div>
  `;

  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
}

function updateAssistantMessage(elementId, content, sources = []) {
  const el = document.getElementById(elementId);
  if (!el) return;

  let citationsHtml = "";
  if (sources && sources.length > 0) {
    citationsHtml = `
      <div class="citations-box">
        ${sources
          .map(
            (s) => `
          <div class="citation-chip">
            📄 ${s.file_name} ${s.page ? `(p. ${s.page})` : ""}
          </div>
        `
          )
          .join("")}
      </div>
    `;
  }

  const bubble = el.querySelector(".message-bubble");
  if (bubble) {
    bubble.innerHTML = `
      <div class="message-text">${content.replace(/\n/g, "<br>")}</div>
      ${citationsHtml}
    `;
  }
}

function updateSessionList() {
  const list = document.getElementById("sessionList");
  if (!list) return;
  list.innerHTML = "";

  chatSessions.forEach((sId, idx) => {
    const item = document.createElement("div");
    item.className = `session-item ${sId === currentSessionId ? "active" : ""}`;
    item.innerHTML = `
      <span>💬 Session #${idx + 1} (${sId.slice(0, 8)})</span>
    `;
    item.addEventListener("click", () => {
      currentSessionId = sId;
      updateSessionList();
    });
    list.appendChild(item);
  });
}

/* ==========================================================================
   Retrieval & Search
   ========================================================================== */
function initSearch() {
  const searchBtn = document.getElementById("searchBtn");
  const searchInput = document.getElementById("searchInput");
  const isHybridCheckbox = document.getElementById("isHybridSearch");

  searchBtn.addEventListener("click", async () => {
    const query = searchInput.value.trim();
    if (!query) return;

    const resultsContainer = document.getElementById("searchResults");
    resultsContainer.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--text-muted);">Executing retrieval and re-ranking...</div>`;

    const isHybrid = isHybridCheckbox ? isHybridCheckbox.checked : false;
    const deptFilter = document.getElementById("filterDept").value;
    const topK = parseInt(document.getElementById("topKSlider").value, 10);

    try {
      let endpoint = `${API_BASE}/api/v1/query`;
      let payload = {
        query: query,
        top_k: topK,
      };

      if (isHybrid) {
        endpoint = `${API_BASE}/api/v1/query/hybrid`;
        payload = { query: query, top_k: topK, alpha: 0.5 };
      } else if (deptFilter) {
        payload.filters = { department: deptFilter };
      }

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      renderSearchResults(data, isHybrid);
    } catch (err) {
      resultsContainer.innerHTML = `<div style="color:var(--accent-rose); padding:1rem;">Failed to execute search: ${err.message}</div>`;
    }
  });
}

function renderSearchResults(data, isHybrid) {
  const container = document.getElementById("searchResults");
  container.innerHTML = "";

  if (isHybrid) {
    if (!data.nodes || data.nodes.length === 0) {
      container.innerHTML = `<div style="padding:1.5rem; color:var(--text-dim);">No hybrid nodes matched your query.</div>`;
      return;
    }
    data.nodes.forEach((n, idx) => {
      const card = document.createElement("div");
      card.className = "glass-card";
      card.style.marginBottom = "1rem";
      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
          <span style="font-weight:600; color:#818cf8;">Rank #${idx + 1} | Score: ${(n.score || 0).toFixed(4)}</span>
          <span style="font-size:0.8rem; color:var(--text-dim);">${n.metadata?.file_name || "Document"}</span>
        </div>
        <p style="font-size:0.9rem; line-height:1.5;">${n.content}</p>
      `;
      container.appendChild(card);
    });
  } else {
    const card = document.createElement("div");
    card.className = "glass-card";
    card.innerHTML = `
      <h3 style="font-size:1.1rem; color:#fff; margin-bottom:0.75rem;">Synthesized Answer:</h3>
      <p style="margin-bottom:1rem; line-height:1.6;">${data.answer || "No response generated."}</p>
      <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:0.5rem; font-weight:600;">Cited Sources:</div>
      <div class="citations-box" style="border:none; margin:0; padding:0;">
        ${(data.sources || [])
          .map((s) => `<div class="citation-chip">📄 ${s.file_name}</div>`)
          .join("")}
      </div>
    `;
    container.appendChild(card);
  }
}

/* ==========================================================================
   Document Upload & Ingestion
   ========================================================================== */
function initUpload() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });
}

async function handleFileUpload(file) {
  const uploadStatus = document.getElementById("uploadStatus");
  uploadStatus.innerHTML = `<div style="color:#818cf8; margin-top:1rem;">⏳ Ingesting and parsing <b>${file.name}</b>...</div>`;

  const formData = new FormData();
  formData.append("file", file);

  const dept = document.getElementById("docDept") ? document.getElementById("docDept").value : "General";
  const cat = document.getElementById("docCat") ? document.getElementById("docCat").value : "Documentation";

  formData.append("department", dept);
  formData.append("category", cat);
  formData.append("access_level", "internal");

  try {
    const res = await fetch(`${API_BASE}/api/v1/documents/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) throw new Error("Document ingestion failed");
    const data = await res.json();

    uploadStatus.innerHTML = `
      <div style="color:#10b981; margin-top:1rem; padding:0.75rem; background:rgba(16,185,129,0.1); border-radius:8px;">
        ✅ <b>${file.name}</b> successfully ingested into <b>${data.nodes_created}</b> searchable chunks!
      </div>
    `;
    loadDocuments();
  } catch (err) {
    uploadStatus.innerHTML = `
      <div style="color:#f43f5e; margin-top:1rem; padding:0.75rem; background:rgba(244,63,94,0.1); border-radius:8px;">
        ❌ Ingestion Error: ${err.message}
      </div>
    `;
  }
}

async function loadDocuments() {
  const listEl = document.getElementById("documentsTableBody");
  if (!listEl) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/documents`);
    const data = await res.json();

    if (!data.documents || data.documents.length === 0) {
      listEl.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:1.5rem; color:var(--text-dim);">No documents uploaded yet.</td></tr>`;
      return;
    }

    listEl.innerHTML = data.documents
      .map(
        (doc) => `
        <tr style="border-bottom:1px solid var(--border-subtle);">
          <td style="padding:1rem;">📄 <b>${doc.name}</b></td>
          <td style="padding:1rem; color:var(--text-muted);">${(doc.size_bytes / 1024).toFixed(1)} KB</td>
          <td style="padding:1rem; color:var(--text-muted);">${new Date(doc.modified * 1000).toLocaleString()}</td>
          <td style="padding:1rem;"><span class="brand-badge" style="background:rgba(16,185,129,0.15); color:#34d399;">Indexed</span></td>
        </tr>
      `
      )
      .join("");
  } catch {
    listEl.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:1.5rem; color:var(--text-dim);">Could not retrieve document list.</td></tr>`;
  }
}

/* ==========================================================================
   GraphRAG Visualizer (Interactive Canvas)
   ========================================================================== */
function initGraph() {
  const exploreBtn = document.getElementById("exploreGraphBtn");
  const entityInput = document.getElementById("graphEntityInput");

  if (exploreBtn) {
    exploreBtn.addEventListener("click", () => {
      const entity = entityInput.value.trim() || "alice";
      fetchGraphExploration(entity);
    });
  }
}

async function fetchGraphTriplets() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/graph/triplets`);
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("tripletsCount").textContent = data.triplet_count || 0;
    renderCanvasGraph(data.triplets || []);
  } catch (err) {
    console.warn("Could not fetch triplets:", err);
  }
}

async function fetchGraphExploration(entity) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/graph/explore`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entity: entity, max_depth: 3 }),
    });

    const data = await res.json();
    const resultBox = document.getElementById("graphExploreOutput");
    if (resultBox) {
      resultBox.innerHTML = `
        <h4 style="margin-bottom:0.5rem; color:#818cf8;">Traversal paths from "${data.entity}": (${data.paths_found} found)</h4>
        <ul style="padding-left:1.25rem; font-size:0.85rem; color:var(--text-muted);">
          ${(data.network_subgraph || [])
            .map((p) => `<li style="margin-bottom:0.25rem;"><code>${p}</code></li>`)
            .join("")}
        </ul>
      `;
    }
  } catch (err) {
    console.error("Graph explore error:", err);
  }
}

function renderCanvasGraph(triplets) {
  const canvas = document.getElementById("graphCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  canvas.width = canvas.parentElement.clientWidth;
  canvas.height = canvas.parentElement.clientHeight || 520;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Extract unique entities
  const nodes = {};
  triplets.forEach((t) => {
    nodes[t.subject] = true;
    nodes[t.object] = true;
  });

  const nodeKeys = Object.keys(nodes);
  if (nodeKeys.length === 0) {
    ctx.fillStyle = "#64748b";
    ctx.font = "14px Inter";
    ctx.textAlign = "center";
    ctx.fillText("No triplets extracted yet. Ingest documents to populate Knowledge Graph.", canvas.width / 2, canvas.height / 2);
    return;
  }

  // Radial positioning
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  const radius = Math.min(centerX, centerY) - 80;

  const positions = {};
  nodeKeys.forEach((key, idx) => {
    const angle = (idx / nodeKeys.length) * 2 * Math.PI;
    positions[key] = {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });

  // Draw Edges
  triplets.forEach((t) => {
    const p1 = positions[t.subject];
    const p2 = positions[t.object];
    if (p1 && p2) {
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.strokeStyle = "rgba(99, 102, 241, 0.4)";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Relation label
      const midX = (p1.x + p2.x) / 2;
      const midY = (p1.y + p2.y) / 2;
      ctx.fillStyle = "#a5b4fc";
      ctx.font = "10px JetBrains Mono";
      ctx.textAlign = "center";
      ctx.fillText(t.relation, midX, midY - 4);
    }
  });

  // Draw Nodes
  nodeKeys.forEach((key) => {
    const pos = positions[key];
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, 14, 0, 2 * Math.PI);
    ctx.fillStyle = "#6366f1";
    ctx.shadowColor = "#6366f1";
    ctx.shadowBlur = 12;
    ctx.fill();
    ctx.shadowBlur = 0;

    ctx.fillStyle = "#fff";
    ctx.font = "12px Inter";
    ctx.textAlign = "center";
    ctx.fillText(key, pos.x, pos.y + 28);
  });
}
