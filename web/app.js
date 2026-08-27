const $ = (id) => document.getElementById(id);

const state = {
  logs: [],
  selected: null,
  timeline: null,
};

function fmtRange(log) {
  const d = log.date || "日期未知";
  const a = log.start_time || "--:--:--";
  const b = log.end_time || "--:--:--";
  return `${d}  ${a} – ${b}`;
}

function fmtSize(n) {
  if (n == null) return "";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

async function refreshSpec() {
  try {
    const s = await api("/api/spec");
    const c = s.counts || {};
    $("spec-info").textContent =
      `映射 ${c.mapping || 0} · 关键 ${c.key || 0} · 异常 ${c.anomaly || 0} · 噪声 ${c.noise || 0}`;
  } catch (e) {
    $("spec-info").textContent = "规则未加载";
  }
}

async function refreshLogs() {
  const data = await api("/api/logs");
  state.logs = data.logs || [];
  renderList();
}

function renderList() {
  const ul = $("file-list");
  ul.innerHTML = "";
  if (!state.logs.length) {
    ul.innerHTML = `<li style="cursor:default;opacity:.7">还没有导入的日志</li>`;
    return;
  }
  for (const log of state.logs) {
    const li = document.createElement("li");
    if (state.selected === log.id) li.classList.add("active");
    const counts = log.counts || {};
    li.innerHTML = `
      <button class="del" data-del="${log.id}" title="删除">删除</button>
      <div class="fname"></div>
      <div class="fmeta"><span></span><span></span></div>
      <div class="badges"></div>`;
    li.querySelector(".fname").textContent = log.original_name;
    li.querySelector(".fmeta span").textContent = fmtRange(log);
    li.querySelector(".fmeta span:last-child").textContent =
      `${log.line_count || 0} 行 · ${fmtSize(log.size)}`;
    const badges = li.querySelector(".badges");
    if (counts.key) {
      const b = document.createElement("span");
      b.className = "badge key";
      b.textContent = `重点 ${counts.key}`;
      badges.appendChild(b);
    }
    if (counts.anomaly) {
      const b = document.createElement("span");
      b.className = "badge anomaly";
      b.textContent = `异常 ${counts.anomaly}`;
      badges.appendChild(b);
    }
    li.addEventListener("click", (ev) => {
      if (ev.target.closest("[data-del]")) return;
      selectLog(log.id);
    });
    li.querySelector("[data-del]").addEventListener("click", async (ev) => {
      ev.stopPropagation();
      if (!confirm(`删除 ${log.original_name} ？`)) return;
      await api(`/api/logs/${log.id}`, { method: "DELETE" });
      if (state.selected === log.id) {
        state.selected = null;
        $("timeline-wrap").hidden = true;
        $("empty-state").hidden = false;
      }
      await refreshLogs();
    });
    ul.appendChild(li);
  }
}

async function selectLog(id) {
  state.selected = id;
  renderList();
  await loadTimeline();
}

async function loadTimeline() {
  if (!state.selected) return;
  const noise = $("tog-noise").checked ? "1" : "0";
  const all = $("tog-all").checked ? "1" : "0";
  $("empty-state").hidden = true;
  $("timeline-wrap").hidden = false;
  $("timeline").innerHTML = `<p class="hint">加载中…</p>`;
  try {
    const data = await api(
      `/api/logs/${state.selected}/timeline?show_noise=${noise}&show_all=${all}`
    );
    state.timeline = data;
    renderTimeline(data);
  } catch (e) {
    $("timeline").innerHTML = `<p class="err">${e.message}</p>`;
  }
}

function renderCounts(c) {
  $("counts").innerHTML = `
    <div class="count"><b>${c.total || 0}</b><span>总计</span></div>
    <div class="count k"><b>${c.key || 0}</b><span>重点</span></div>
    <div class="count a"><b>${c.anomaly || 0}</b><span>异常</span></div>
    <div class="count"><b>${c.hidden_noise || 0}</b><span>噪声</span></div>`;
  const extra = [];
  extra.push(`本页 ${c.returned || 0} 条`);
  if (c.unmatched) extra.push(`未映射 ${c.unmatched}`);
  $("return-count").textContent = extra.join(" · ");
}

function renderTimeline(data) {
  $("tl-title").textContent = data.name || "";
  const bits = [fmtRange(data)];
  if (data.date_source === "mtime") bits.push("日期取自文件时间");
  if (data.truncated) bits.push("结果已截断");
  $("tl-meta").textContent = bits.join(" · ");
  renderCounts(data.counts || {});

  const box = $("timeline");
  box.innerHTML = "";
  const events = data.events || [];
  if (!events.length) {
    box.innerHTML = `<p class="hint">当前过滤条件下没有事件。试试「显示噪声」或「显示全部」。</p>`;
    return;
  }

  let lastGroup = null;
  let lastPage = null;
  const frag = document.createDocumentFragment();
  for (const ev of events) {
    if (ev.session === "startup" || ev.session === "exit") {
      const s = document.createElement("div");
      s.className = `session ${ev.session}`;
      s.textContent = ev.session === "startup" ? "会话开始 · 软件启动" : "会话结束 · 软件退出";
      frag.appendChild(s);
      lastGroup = ev.group || lastGroup;
    }

    const pageLabel = ev.page || "";
    if (ev.category === "page" || (pageLabel && pageLabel !== lastPage)) {
      const label = pageLabel || ev.step || ev.group;
      if (label) {
        const ph = document.createElement("div");
        ph.className = "page-h";
        ph.textContent = label;
        frag.appendChild(ph);
      }
      lastPage = pageLabel || lastPage;
      if (ev.group && ev.group === (pageLabel || ev.step)) lastGroup = ev.group;
    } else if (pageLabel) {
      lastPage = pageLabel;
    }

    if (ev.group && ev.group !== lastGroup && ev.mark !== "none") {
      const g = document.createElement("div");
      g.className = "group-h";
      g.textContent = ev.group;
      frag.appendChild(g);
      lastGroup = ev.group;
    } else if (ev.group) {
      lastGroup = ev.group;
    }

    const el = document.createElement("article");
    const cls = ["event"];
    if (ev.mark === "key") cls.push("key");
    if (ev.mark === "anomaly") cls.push("anomaly");
    if (ev.mark === "pin") cls.push("pin");
    if (ev.source === "noise" || ev.category === "noise") cls.push("noise");
    el.className = cls.join(" ");

    const lv = ev.level ? `<span class="etag lv-${ev.level}">${ev.level}</span>` : "";
    const step = ev.step ? `<span class="estep">${escapeHtml(ev.step)}</span>` : "";
    const mm =
      ev.value_mm != null && ev.value_mm !== ""
        ? `<span class="emm">${Number(ev.value_mm).toFixed(2)} mm</span>`
        : "";
    el.innerHTML = `
      <div class="erow">
        <span class="etime">${ev.time || "--:--:--"}</span>
        ${step}
        ${mm}
        <span class="emsg"></span>
        ${lv}
      </div>
      <div class="detail"></div>`;
    el.querySelector(".emsg").textContent = ev.message || (ev.block ? "(非标准块)" : "");
    const detail = el.querySelector(".detail");
    const meta = [
      ev.date ? `日期 ${ev.date}` : null,
      ev.level ? `级别 ${ev.level}` : "非标准行",
      ev.thread ? `线程 ${ev.thread}` : null,
      `行 ${ev.line}${ev.line_end && ev.line_end !== ev.line ? "–" + ev.line_end : ""}`,
      ev.category ? `类别 ${ev.category}` : null,
      ev.source ? `规则 ${ev.source}` : null,
    ]
      .filter(Boolean)
      .join(" · ");
    const pre = document.createElement("pre");
    pre.textContent = ev.raw || ev.message || "";
    detail.appendChild(document.createTextNode(meta));
    detail.appendChild(pre);

    el.addEventListener("click", () => el.classList.toggle("open"));
    frag.appendChild(el);
  }
  box.appendChild(frag);
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

$("file-input").addEventListener("change", async (ev) => {
  const files = [...ev.target.files];
  ev.target.value = "";
  if (!files.length) return;
  const fd = new FormData();
  for (const f of files) fd.append("files", f, f.name);
  $("upload-status").textContent = `正在导入 ${files.length} 个文件…`;
  try {
    const res = await fetch("/api/logs", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "导入失败");
    const n = (data.imported || []).length;
    const errn = (data.errors || []).length;
    $("upload-status").textContent = `已导入 ${n} 个` + (errn ? `，失败 ${errn}` : "");
    await refreshLogs();
    if (data.imported && data.imported[0]) selectLog(data.imported[0].id);
  } catch (e) {
    $("upload-status").textContent = e.message;
  }
});

$("tog-noise").addEventListener("change", loadTimeline);
$("tog-all").addEventListener("change", loadTimeline);
$("reload-spec").addEventListener("click", async () => {
  await api("/api/spec/reload", { method: "POST" });
  await refreshSpec();
  if (state.selected) await loadTimeline();
});

refreshSpec();
refreshLogs();
