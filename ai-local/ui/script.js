document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chatForm");
  const messageInput = document.getElementById("messageInput");
  const chatLog = document.getElementById("chatLog");
  const sourcesList = document.getElementById("sourcesList");
  const rulesList = document.getElementById("rulesList");
  const aliasesList = document.getElementById("aliasesList");
  const factsList = document.getElementById("factsList");
  const memoryView = document.getElementById("memoryView");

  async function refreshPanels() {
    await Promise.all([loadRules(), loadAliases(), loadFacts(), loadMemory()]);
  }

  async function loadRules() {
    try {
      const res = await fetch("/rules");
      const data = await res.json();
      rulesList.innerHTML = "";
      data.items.forEach((item) => {
        const li = document.createElement("li");
        li.textContent = `${item.if} → ${item.reply}`;
        rulesList.appendChild(li);
      });
    } catch (err) {
      console.error("rules", err);
    }
  }

  async function loadAliases() {
    try {
      const res = await fetch("/aliases");
      const data = await res.json();
      aliasesList.innerHTML = "";
      Object.entries(data.items || {}).forEach(([key, value]) => {
        const li = document.createElement("li");
        li.textContent = `${key} → ${value}`;
        aliasesList.appendChild(li);
      });
    } catch (err) {
      console.error("aliases", err);
    }
  }

  async function loadFacts() {
    try {
      const res = await fetch("/facts");
      const data = await res.json();
      factsList.innerHTML = "";
      (data.items || []).forEach((item) => {
        const li = document.createElement("li");
        li.textContent = `${item.topic}: ${item.summary}`;
        factsList.appendChild(li);
      });
    } catch (err) {
      console.error("facts", err);
    }
  }

  async function loadMemory() {
    try {
      const res = await fetch("/memory");
      const data = await res.json();
      memoryView.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
      console.error("memory", err);
    }
  }

  function appendMessage(author, text) {
    const wrapper = document.createElement("div");
    wrapper.className = `bubble ${author}`;
    wrapper.innerHTML = `<strong>${author === "user" ? "Vous" : "IA"}</strong><p>${text}</p>`;
    chatLog.appendChild(wrapper);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function showSources(sources) {
    sourcesList.innerHTML = "";
    sources.forEach((url) => {
      const li = document.createElement("li");
      const link = document.createElement("a");
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener";
      link.textContent = url;
      li.appendChild(link);
      sourcesList.appendChild(li);
    });
  }

  chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = messageInput.value.trim();
    if (!message) {
      return;
    }
    appendMessage("user", message);
    messageInput.value = "";
    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          allow_web: document.querySelector("#allowWeb").checked,
        }),
      });
      const data = await res.json();
      appendMessage("bot", data.answer || "(pas de réponse)");
      showSources(data.sources || []);
      if (data.learned) {
        await loadFacts();
      }
    } catch (err) {
      appendMessage("bot", "Erreur de communication.");
      console.error(err);
    }
  });

  refreshPanels();
});
