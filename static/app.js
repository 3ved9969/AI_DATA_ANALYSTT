function addMessage(text, cls) {
  const chatBox = document.getElementById("chatBox");
  const div = document.createElement("div");
  const isUser = cls === "user";
  
  div.className = `p-2.5 rounded-lg text-xs leading-relaxed flex gap-2 items-start ${
    isUser 
      ? "bg-blue-500/5 border border-blue-500/10 text-blue-300 font-mono" 
      : "bg-slate-900 border border-slate-800 text-slate-300"
  }`;

  const avatar = isUser 
    ? `<div class="h-4 w-4 rounded bg-blue-500/20 text-blue-400 flex items-center justify-center shrink-0 mt-0.5"><i data-lucide="user" class="h-2.5 w-2.5"></i></div>`
    : `<div class="h-4 w-4 rounded bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0 mt-0.5"><i data-lucide="bot" class="h-2.5 w-2.5"></i></div>`;

  div.innerHTML = `${avatar}<div class="flex-1">${text}</div>`;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  lucide.createIcons();
}

async function uploadFile() {
  const fileInput = document.getElementById("fileInput");
  const status = document.getElementById("uploadStatus");
  if (!fileInput.files.length) {
    status.innerHTML = `<span class="text-amber-400 font-mono text-[10px]">⚠️ Error: Choose a file matrix module first.</span>`;
    return;
  }

  status.innerHTML = `<span class="text-blue-400 animate-pulse font-mono text-[10px]">⚙️ Transforming and indexing database layer...</span>`;
  
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  
  try {
    const res = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();

    if (data.error) {
      status.innerHTML = `<span class="text-rose-400 text-[10px]">❌ ${data.error}</span>`;
      return;
    }

    status.innerHTML = `<span class="text-emerald-400 text-[10px]">✨ Ingestion Complete</span>`;
    addMessage(`Data matrix ingested securely. System configured to process ${data.schema.rows} records across ${data.schema.columns_count} columns cleanly.`, "bot");
  } catch (err) {
    status.innerHTML = `<span class="text-rose-400 text-[10px]">❌ Communication exception on upload channel.</span>`;
  }
}

function renderTable(columns, rows) {
  const container = document.getElementById("tableContainer");
  if (!rows || !rows.length) {
    container.innerHTML = `<div class="p-6 text-center text-slate-500 text-xs">No vector instances returned.</div>`;
    return;
  }

  let html = `<div class="overflow-x-auto"><table class="w-full border-collapse text-left font-mono text-[11px] text-slate-300">
    <thead class="bg-slate-900/60 border-b border-slate-800 text-slate-400 text-[10px] uppercase tracking-wider">
      <tr>`;
  columns.forEach(col => html += `<th class="px-3 py-2.5 font-semibold">${col}</th>`);
  html += `</tr></thead><tbody class="divide-y divide-slate-800/40">`;

  rows.forEach((row, i) => {
    html += `<tr class="${i % 2 === 0 ? 'bg-slate-950/20' : 'bg-[#0f172a]/10'} hover:bg-slate-800/20 transition-colors">`;
    columns.forEach(col => {
      let cellData = row[col] ?? "";
      html += `<td class="px-3 py-2 truncate max-w-[180px]" title="${cellData}">${cellData}</td>`;
    });
    html += "</tr>";
  });

  html += "</tbody></table></div>";
  container.innerHTML = html;
}

function renderInsight(insight, reportUrl) {
  const container = document.getElementById("insightContainer");
  container.innerHTML = `
    <div class="flex flex-col gap-3 text-left font-sans text-xs h-full">
      <h3 class="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-1.5">${insight.headline || "Calculated Engine Insights Run"}</h3>
      <div class="flex-1 flex flex-col gap-2 overflow-y-auto pr-1">
        <p class="text-slate-300 text-[11px]"><strong class="text-blue-400 block text-[9px] uppercase tracking-wider mb-0.5">Observation Summary</strong>${insight.insight || ""}</p>
        <p class="text-slate-400 text-[11px]"><strong class="text-amber-400 block text-[9px] uppercase tracking-wider mb-0.5">Observed Root Cause Vector</strong>${insight.possible_reason || ""}</p>
        <p class="text-slate-400 text-[11px]"><strong class="text-emerald-400 block text-[9px] uppercase tracking-wider mb-0.5">Strategic Recommendation</strong>${insight.recommendation || ""}</p>
      </div>
      <a href="${reportUrl}" target="_blank" class="mt-auto w-full py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-[11px] rounded-lg text-center transition-all flex items-center justify-center gap-1">
        <i data-lucide="file-text" class="h-3 w-3 text-blue-400"></i> Download PDF Ledger Report
      </a>
    </div>
  `;
  lucide.createIcons();
}

function renderChart(chartUrl) {
  const container = document.getElementById("chartContainer");
  if (!chartUrl) {
    container.innerHTML = `
      <div class="p-6 text-center text-slate-600 flex flex-col items-center justify-center h-full">
        <i data-lucide="eye-off" class="h-6 w-6 text-slate-800 mb-1"></i>
        <p class="text-[11px]">No graphical map required for this parameter configuration structure.</p>
      </div>`;
    return;
  }
  container.innerHTML = `<iframe src="${chartUrl}" class="w-full h-[360px] border-0 rounded-lg bg-[#0b0f19]"></iframe>`;
}

async function sendQuery() {
  const input = document.getElementById("questionInput");
  const question = input.value.trim();
  if (!question) return;

  addMessage(question, "user");
  input.value = "";

  try {
    const res = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    const data = await res.json();
    if (data.error) {
      addMessage(`❌ Pipeline operational failure: ${data.error}`, "bot");
      return;
    }
    
    addMessage(data.insight?.insight || "Analytical compute complete.", "bot");
    renderTable(data.columns, data.result);
    renderChart(data.chart_url);
    renderInsight(data.insight, data.report_url);
  } catch (err) {
    addMessage("❌ Connection Loss: Server cluster did not return structural data.", "bot");
  }
}