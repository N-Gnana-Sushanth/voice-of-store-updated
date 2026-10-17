/**
 * Voice of Store — FIRST SIGNAL AI
 * Frontend Application Controller
 * Robust, null-safe DOM management and API bindings
 */

(function () {
  "use strict";

  // --- Utility Helpers ---
  const $ = (selector, context = document) => {
    try { return context ? context.querySelector(selector) : null; }
    catch (_) { return null; }
  };

  const $$ = (selector, context = document) => {
    try { return context ? [...context.querySelectorAll(selector)] : []; }
    catch (_) { return []; }
  };

  const safeOn = (target, event, handler, options) => {
    const el = typeof target === "string" ? $(target) : target;
    if (el && typeof el.addEventListener === "function") {
      el.addEventListener(event, handler, options);
      return true;
    }
    return false;
  };

  const safeText = (target, text) => {
    const el = typeof target === "string" ? $(target) : target;
    if (el) el.textContent = text ?? "";
  };

  const safeHtml = (target, html) => {
    const el = typeof target === "string" ? $(target) : target;
    if (el) el.innerHTML = html ?? "";
  };

  const safeValue = (target, defaultVal = "") => {
    const el = typeof target === "string" ? $(target) : target;
    return el && "value" in el ? el.value : defaultVal;
  };

  const esc = (v) =>
    String(v ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[c] || c));

  const nice = (s) =>
    String(s || "")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());

  // --- API Client ---
  async function api(url, options = {}) {
    const res = await fetch(url, options);
    let data;
    try {
      data = await res.json();
    } catch (_) {
      data = { error: `Server returned non-JSON response (${res.status})` };
    }
    if (!res.ok) {
      throw new Error(data.error || data.message || `Request failed (${res.status})`);
    }
    return data;
  }

  // --- Toast Notifications ---
  let toastTimeout = null;
  function toast(msg, type = "info") {
    const t = $("#toast");
    if (!t) return;
    t.textContent = msg;
    t.className = `toast toast-${type}`;
    t.classList.remove("hidden");
    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
      t.classList.add("hidden");
    }, 3200);
  }

  // --- Page Navigation ---
  function showPage(name) {
    const targetPage = name || "overview";
    $$(".page").forEach((p) => {
      p.classList.toggle("visible", p.id === targetPage);
    });
    $$(".nav").forEach((b) => {
      b.classList.toggle("active", b.dataset.page === targetPage);
    });

    const titles = {
      overview: "Overview",
      signals: "FIRST SIGNAL",
      feedback: "All Feedback",
      actions: "Action Tracker",
      reports: "Weekly Reports",
    };
    safeText("#page-title", titles[targetPage] || "Overview");
    safeText("#header-breadcrumb-current", titles[targetPage] || "Overview");

    // Load data for the active view
    const loaders = {
      overview: loadOverview,
      signals: loadSignals,
      feedback: loadFeedback,
      actions: loadActions,
      reports: loadReport,
    };
    const loader = loaders[targetPage] || loadOverview;
    try {
      loader();
    } catch (err) {
      console.error(`Error loading page ${targetPage}:`, err);
    }
  }

  // --- Incident Card Sorting & Filtering ---
  function sortIncidents(items, mode) {
    const rank = { Critical: 0, High: 1, Medium: 2, Low: 3 };
    return [...items].sort((a, b) => {
      if (mode === "low") {
        return (
          (rank[b.severity] ?? 4) - (rank[a.severity] ?? 4) ||
          (b.report_count || 0) - (a.report_count || 0)
        );
      }
      if (mode === "evidence") {
        return (
          (b.report_count || 0) - (a.report_count || 0) ||
          (rank[a.severity] ?? 4) - (rank[b.severity] ?? 4)
        );
      }
      if (mode === "newest") {
        return String(b.latest_seen || "").localeCompare(String(a.latest_seen || ""));
      }
      // Default: High -> Low
      return (
        (rank[a.severity] ?? 4) - (rank[b.severity] ?? 4) ||
        (b.report_count || 0) - (a.report_count || 0)
      );
    });
  }

  function filterIncidents(items, prefix) {
    const q = safeValue(`#${prefix}-search`).trim().toLowerCase();
    const sev = safeValue(`#${prefix}-severity`);
    const status = safeValue(`#${prefix}-status`);

    return items.filter((i) => {
      const hay = [
        i.summary,
        i.store_id,
        i.issue_type,
        i.department,
        i.assigned_user,
        i.id,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchQ = !q || hay.includes(q);
      const matchSev = !sev || i.severity === sev;
      const matchStatus = !status || i.status === status;
      return matchQ && matchSev && matchStatus;
    });
  }

  // --- Incident Card HTML Generator ---
  function incidentCard(i, showActions = true) {
    if (!i) return "";
    const evidenceList = Array.isArray(i.evidence) ? i.evidence : [];
    const seenEv = new Set();
    const dedupedEv = [];
    for (const e of evidenceList) {
      const eid = e.id || e.feedback_id;
      if (eid && seenEv.has(eid)) continue;
      if (eid) seenEv.add(eid);
      dedupedEv.push(e);
    }
    const quotes = dedupedEv
      .slice(0, 3)
      .map((e) => {
        const textEn = e.description_en || e.translated_text || e.original_text || e.text || e.quote || "";
        const orig = e.original_text || e.text || e.quote || "";
        const isTrans = e.is_translated || (e.source_language && e.source_language !== "en" && orig !== textEn);
        return `<div class="quote">“${esc(textEn)}”${isTrans ? ` <span class="trans-pill-small" title="Original: ${esc(orig)}">Translated</span>` : ""} <span class="incident-meta">— ${esc(e.id || e.feedback_id || "")} · ${esc(e.channel || "")}</span></div>`;
      })
      .join("");

    const statusOpts = [
      "Detected — awaiting review",
      "Under investigation",
      "Confirmed",
      "Inconclusive",
      "Not substantiated",
      "Action in progress",
      "Pending verification",
      "Resolved",
    ];

    const deptOpts = [
      "Store Operations",
      "Store Ops",
      "Supply Chain",
      "Merchandising",
      "Digital",
      "HR",
      "Customer Experience",
      "Unassigned",
    ];

    const sevClass = ["Critical", "High", "Medium", "Low"].includes(i.severity)
      ? i.severity
      : "Medium";

    return `<article class="incident-card" data-id="${esc(i.id)}">
      <div class="incident-top">
        <div>
          <div class="incident-title">
            ${esc(i.summary || "Incident")} 
            <span class="incident-meta-id">· ${esc(i.id)}</span>
          </div>
          <div class="incident-meta">
            <strong>${esc(i.store_id || "")}</strong> · ${nice(i.issue_type)} · ${i.report_count || 1} linked report(s) · First seen: ${esc((i.first_seen || "—").replace("T", " ").slice(0, 16))}
          </div>
        </div>
        <span class="pill ${esc(sevClass)}">${esc(i.severity || "Medium")} priority</span>
      </div>

      <div class="why">
        <div><b>Why raised:</b> ${esc(i.why_raised || i.description || "Related customer reports require operational review.")}</div>
        <div class="why-sub"><b>Suggested owner:</b> ${esc(i.department || "Unassigned")} · <b>Latest:</b> ${esc((i.latest_seen || "—").replace("T", " ").slice(0, 16))}</div>
      </div>

      ${quotes || `<p class="muted empty-quotes">No linked evidence quotes yet. Full feedback records remain available in All Feedback.</p>`}

      <div class="view-row">
        <button class="quiet view-problem" data-id="${esc(i.id)}">View full problem statement →</button>
      </div>

      ${
        showActions
          ? `<div class="actions">
          <label class="actions-label">
            <span>Status</span>
            <select class="status-select" aria-label="Incident status">
              ${statusOpts
                .map(
                  (s) =>
                    `<option value="${esc(s)}" ${s === i.status ? "selected" : ""}>${esc(s)}</option>`
                )
                .join("")}
            </select>
          </label>
          <label class="actions-label">
            <span>Assignee</span>
            <input class="owner-input" placeholder="Assigned user" value="${esc(i.assigned_user || "")}" aria-label="Assigned user">
          </label>
          <label class="actions-label">
            <span>Department</span>
            <select class="department-select" aria-label="Department">
              ${deptOpts
                .map(
                  (d) =>
                    `<option value="${esc(d)}" ${d === i.department ? "selected" : ""}>${esc(d)}</option>`
                )
                .join("")}
            </select>
          </label>
          <div class="actions-btn-group">
            <button class="primary save-incident">Save update</button>
            <button class="quick-action" data-quick-status="Under investigation">Acknowledge</button>
            <button class="quick-action" data-quick-status="Resolved">Resolve</button>
          </div>
          <input class="note-input" placeholder="Investigation note / resolution summary..." aria-label="Investigation note">
        </div>`
          : ""
      }
    </article>`;
  }

  // --- Data Loading Functions ---

  async function loadOverview() {
    try {
      const d = await api("/api/overview");
      const fbCount = d.feedback_count ?? d.stats?.total_feedback ?? 0;
      const openCount = d.unresolved_count ?? d.stats?.active_incidents ?? 0;
      const highCount = d.high_priority_count ?? d.stats?.critical_high_incidents ?? 0;

      safeText("#feedback-count", fbCount);
      safeText("#stat-total-feedback", fbCount);

      safeText("#open-count", openCount);
      safeText("#stat-active-incidents", openCount);

      safeText("#high-count", highCount);
      safeText("#stat-critical-high", highCount);

      const rawItems = Array.isArray(d.incidents) && d.incidents.length
        ? d.incidents
        : (Array.isArray(d.needs_attention) ? d.needs_attention : []);
      const seenIds = new Set();
      const items = [];
      for (const inc of rawItems) {
        if (!inc || !inc.id || seenIds.has(inc.id)) continue;
        seenIds.add(inc.id);
        items.push(inc);
      }

      const container = $("#overview-incidents") || $("#overview-needs-attention");
      if (container) {
        if (!items.length) {
          container.innerHTML = `<div class="empty">Nothing needs urgent attention right now. Add or import feedback to begin detection.</div>`;
        } else {
          container.innerHTML = items.map((i) => incidentCard(i, false)).join("");
        }
      }
    } catch (err) {
      console.error("loadOverview error:", err);
      toast(err.message, "error");
    }
  }

  async function loadSignals() {
    const container = $("#signal-list");
    if (!container) return;
    try {
      const all = await api("/api/incidents");
      const seenIds = new Set();
      const uniqueIncidents = [];
      for (const inc of all) {
        if (!inc || !inc.id || seenIds.has(inc.id)) continue;
        seenIds.add(inc.id);
        uniqueIncidents.push(inc);
      }
      const sortMode = safeValue("#signal-sort", "high");
      const filtered = filterIncidents(sortIncidents(uniqueIncidents, sortMode), "signal");

      if (!filtered.length) {
        container.innerHTML = `<div class="empty">No matching signals found. Ordinary issues require multiple local reports; mandatory safety triggers surface immediately.</div>`;
      } else {
        const countNotice = `<p class="muted signal-count">Showing <strong>${filtered.length}</strong> active signal(s). Open any problem statement to inspect evidence quotes and audit logs.</p>`;
        container.innerHTML = countNotice + filtered.map((i) => incidentCard(i, true)).join("");
      }
    } catch (err) {
      console.error("loadSignals error:", err);
      toast(err.message, "error");
    }
  }

  async function loadActions() {
    const container = $("#action-list");
    if (!container) return;
    try {
      const all = await api("/api/incidents");
      const seenIds = new Set();
      const uniqueIncidents = [];
      for (const inc of all) {
        if (!inc || !inc.id || seenIds.has(inc.id)) continue;
        seenIds.add(inc.id);
        uniqueIncidents.push(inc);
      }
      const sortMode = safeValue("#action-sort", "high");
      const filtered = filterIncidents(sortIncidents(uniqueIncidents, sortMode), "action");

      if (!filtered.length) {
        container.innerHTML = `<div class="empty">No action items found matching your current filter criteria.</div>`;
      } else {
        container.innerHTML = filtered.map((i) => incidentCard(i, true)).join("");
      }
    } catch (err) {
      console.error("loadActions error:", err);
      toast(err.message, "error");
    }
  }

  async function loadFeedback() {
    const rowsEl = $("#feedback-rows");
    if (!rowsEl) return;
    const params = new URLSearchParams();
    const q = safeValue("#feedback-search").trim();
    const store = safeValue("#store-filter").trim();
    const issue = safeValue("#issue-filter").trim();

    if (q) params.set("q", q);
    if (store) params.set("store_id", store);
    if (issue) params.set("issue_type", issue);

    try {
      const d = await api("/api/feedback?" + params.toString());
      const rawRecords = Array.isArray(d) ? d : (d.records || []);
      const seenFids = new Set();
      const records = [];
      for (const r of rawRecords) {
        if (!r || !r.id || seenFids.has(r.id)) continue;
        seenFids.add(r.id);
        records.push(r);
      }

      if (!records.length) {
        rowsEl.innerHTML = `<tr><td colspan="7" class="empty-cell">No matching feedback records found. Try clearing filters.</td></tr>`;
      } else {
        rowsEl.innerHTML = records
          .map((r) => {
            const descEn = r.description_en || r.translated_text || r.original_text || r.text || "";
            const orig = r.original_text || r.text || "";
            const isTranslated = r.is_translated || (r.source_language && r.source_language !== "en" && orig !== descEn);
            const langLabel = r.source_language && r.source_language !== "en" ? r.source_language.toUpperCase() : "Regional";

            const textCellHtml = isTranslated
              ? `<div class="feedback-desc-en">
                   <span class="trans-pill" title="Translated from ${esc(langLabel)} to English">Translated</span>
                   <span class="trans-text">${esc(descEn)}</span>
                 </div>
                 <div class="feedback-orig-meta" title="Original staff feedback">
                   <span class="orig-label">Original (${esc(langLabel)}):</span> <em>${esc(orig)}</em>
                 </div>`
              : `<span class="trans-text">${esc(descEn)}</span>`;

            return `<tr>
              <td>${esc((r.timestamp || "").replace("T", " ").slice(0, 16))}</td>
              <td><strong>${esc(r.store_id)}</strong></td>
              <td><span class="channel-tag">${esc(r.channel)}</span></td>
              <td>${esc(nice(r.issue_type))}</td>
              <td><span class="pill ${esc(r.severity)}">${esc(r.severity)}</span></td>
              <td class="text-cell">${textCellHtml}</td>
              <td class="actions-cell">
                <button class="delete-feedback-btn danger-btn" data-id="${esc(r.id)}" data-snippet="${esc(descEn.slice(0, 80))}" title="Delete feedback record">
                  Delete
                </button>
              </td>
            </tr>`;
          })
          .join("");
      }

      // Populate issue-type filter dropdown
      const sel = $("#issue-filter");
      if (sel) {
        const issues = [...new Set(records.map((r) => r.issue_type).filter(Boolean))].sort();
        const prev = sel.value;
        if (!sel.dataset.populated || issues.length > sel.options.length - 1) {
          sel.innerHTML =
            '<option value="">All issue types</option>' +
            issues
              .map(
                (i) => `<option value="${esc(i)}">${esc(nice(i))}</option>`
              )
              .join("");
          sel.value = prev;
          sel.dataset.populated = "true";
        }
      }
    } catch (err) {
      console.error("loadFeedback error:", err);
      toast(err.message, "error");
    }
  }

  async function loadReport() {
    try {
      const d = await api("/api/reports/weekly");
      const metaEl = $("#report-meta");
      if (metaEl && d.period) {
        metaEl.innerHTML = `<b>Reporting Period:</b> ${esc(d.period.start.slice(0, 10))} to ${esc(d.period.end.slice(0, 10))} · <b>${d.feedback_count || 0}</b> feedback records analyzed · <span class="muted">${esc(d.basis || "Observed counts only")}</span>`;
      }

      const listEl = $("#report-list");
      if (listEl) {
        const top = Array.isArray(d.top_issues) ? d.top_issues : [];
        if (!top.length) {
          listEl.innerHTML = `<div class="empty">No feedback records found in this reporting window. Import a dataset to generate a weekly report.</div>`;
        } else {
          listEl.innerHTML = top
            .map(
              (i) => `<article class="report-item">
                <div class="report-item-header">
                  <h3>${esc(nice(i.issue_type))}</h3>
                  <span class="pill">${i.count} reports</span>
                </div>
                <p class="muted">Department Owner: <strong>${esc(i.department || "Unassigned")}</strong></p>
                <div class="report-grid">
                  <div>
                    <b>Affected Stores</b>
                    <span>${esc(Array.isArray(i.stores) ? i.stores.join(", ") : i.stores || "—")}</span>
                  </div>
                  <div>
                    <b>Recommended Action</b>
                    <span>${esc(i.recommended_action || "Investigate root cause with store manager.")}</span>
                  </div>
                  <div>
                    <b>Sample Evidence</b>
                    <span>${
                      Array.isArray(i.evidence) && i.evidence.length
                        ? i.evidence
                            .map((e) => `“${esc(e.quote)}” (${esc(e.store_id)})`)
                            .join("<br>")
                        : "No evidence in period"
                    }</span>
                  </div>
                </div>
              </article>`
            )
            .join("");
        }
      }

      const highEl = $("#report-high");
      if (highEl) {
        const highEv = Array.isArray(d.high_severity_evidence)
          ? d.high_severity_evidence
          : [];
        highEl.innerHTML =
          `<h2 style="margin:28px 0 12px">High-Severity Feedback Evidence</h2>` +
          (highEv.length
            ? highEv
                .map(
                  (x) =>
                    `<div class="quote"><b>${esc(x.store_id)} · ${esc(nice(x.issue_type))}</b>: “${esc(x.quote || "")}”</div>`
                )
                .join("")
            : `<p class="muted">No critical or high-severity feedback in this reporting period.</p>`);
      }
    } catch (err) {
      console.error("loadReport error:", err);
      toast(err.message, "error");
    }
  }

  // --- Main Application Setup on DOM Ready ---
  function initApp() {
    let pendingDeleteFeedbackId = null;

    // 1. Delegated Click Handler on Document
    document.addEventListener("click", async (e) => {
      // Navigation
      const nav = e.target.closest("[data-page]");
      if (nav && nav.dataset.page) {
        e.preventDefault();
        showPage(nav.dataset.page);
        return;
      }

      const go = e.target.closest("[data-goto]");
      if (go && go.dataset.goto) {
        e.preventDefault();
        showPage(go.dataset.goto);
        return;
      }

      // Add feedback modal triggers
      if (e.target.id === "open-ingest" || e.target.closest("#open-ingest")) {
        const m = $("#modal");
        if (m) m.classList.remove("hidden");
        return;
      }

      if (e.target.id === "close-modal" || e.target.closest("#close-modal") || e.target.id === "modal") {
        const m = $("#modal");
        if (m) m.classList.add("hidden");
        return;
      }

      // Refresh dashboard / signals
      if (e.target.id === "refresh-dashboard" || e.target.closest("#refresh-dashboard")) {
        const activePage = $(".page.visible")?.id || "overview";
        showPage(activePage);
        toast("Refreshed current view", "info");
        return;
      }

      if (e.target.id === "refresh-signals" || e.target.closest("#refresh-signals")) {
        await loadSignals();
        toast("FIRST SIGNAL detection refreshed");
        return;
      }

      // Delete feedback modal triggers
      const delBtn = e.target.closest(".delete-feedback-btn");
      if (delBtn) {
        const fid = delBtn.dataset.id;
        const snippet = delBtn.dataset.snippet;
        if (fid) {
          pendingDeleteFeedbackId = fid;
          const modal = $("#delete-modal");
          const preview = $("#delete-feedback-preview");
          if (preview) {
            preview.textContent = snippet ? `“${snippet}…” (ID: ${fid})` : `Feedback ID: ${fid}`;
          }
          const confirmBtn = $("#confirm-delete-btn");
          if (confirmBtn) {
            confirmBtn.disabled = false;
            confirmBtn.textContent = "Delete";
          }
          if (modal) modal.classList.remove("hidden");
        }
        return;
      }

      // Cancel delete feedback
      if (
        e.target.id === "cancel-delete-btn" ||
        e.target.closest("#cancel-delete-btn") ||
        e.target.id === "cancel-delete-x" ||
        e.target.closest("#cancel-delete-x") ||
        e.target.id === "delete-modal"
      ) {
        pendingDeleteFeedbackId = null;
        const modal = $("#delete-modal");
        if (modal) modal.classList.add("hidden");
        return;
      }

      // Confirm delete feedback
      if (e.target.id === "confirm-delete-btn" || e.target.closest("#confirm-delete-btn")) {
        if (!pendingDeleteFeedbackId) return;
        const confirmBtn = $("#confirm-delete-btn");
        if (confirmBtn) {
          confirmBtn.disabled = true;
          confirmBtn.textContent = "Deleting...";
        }
        const fid = pendingDeleteFeedbackId;
        try {
          const res = await api(`/api/feedback/${encodeURIComponent(fid)}`, {
            method: "DELETE",
          });
          pendingDeleteFeedbackId = null;
          const modal = $("#delete-modal");
          if (modal) modal.classList.add("hidden");
          toast(res.message || "Feedback record deleted successfully", "success");
          loadFeedback();
          loadOverview();
          loadSignals();
          loadActions();
        } catch (err) {
          toast(err.message || "Failed to delete feedback record", "error");
          if (confirmBtn) {
            confirmBtn.disabled = false;
            confirmBtn.textContent = "Delete";
          }
        }
        return;
      }

      // Problem statement detail modal close
      if (e.target.id === "close-detail" || e.target.closest("#close-detail") || e.target.id === "detail-modal") {
        const dm = $("#detail-modal");
        if (dm) dm.classList.add("hidden");
        return;
      }

      // View problem statement details
      const viewBtn = e.target.closest(".view-problem");
      if (viewBtn) {
        const id = viewBtn.dataset.id;
        if (!id) return;
        try {
          // Open detail modal and audit view
          const all = await api("/api/incidents");
          const inc = all.find((x) => x.id === id);
          if (!inc) throw new Error("Incident not found");

          // Post view audit
          await api(`/api/incidents/${encodeURIComponent(id)}/view`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ actor: "Reviewer" }),
          }).catch((err) => console.warn("View audit warning:", err));

          const seenEvModal = new Set();
          const evHtml = (inc.evidence || [])
            .filter((x) => {
              const xid = x.id || x.feedback_id;
              if (xid && seenEvModal.has(xid)) return false;
              if (xid) seenEvModal.add(xid);
              return true;
            })
            .map((x) => {
              const textEn = x.description_en || x.translated_text || x.original_text || x.text || "";
              const orig = x.original_text || x.text || "";
              const isTrans = x.is_translated || (x.source_language && x.source_language !== "en" && orig !== textEn);
              return `<div class="quote">
                <b>${esc(x.id || "")} · ${esc(x.store_id || inc.store_id)} · ${esc((x.timestamp || "").replace("T", " ").slice(0, 16))}</b>
                <p style="margin:4px 0">${esc(textEn)}</p>
                ${isTrans ? `<p class="feedback-orig-meta" style="margin:2px 0 6px"><em>Original (${esc((x.source_language || "regional").toUpperCase())}): ${esc(orig)}</em></p>` : ""}
                <span class="incident-meta">${esc(x.channel || "")} · ${esc(nice(x.issue_type || inc.issue_type))} · ${esc(x.severity || inc.severity)}</span>
              </div>`;
            })
            .join("");

          safeText("#detail-title", inc.summary || "Problem Statement");
          safeHtml(
            "#detail-content",
            `<div class="detail-meta">
              <span class="pill ${esc(inc.severity)}">${esc(inc.severity)} priority</span> 
              <span class="pill">${esc(inc.status || "Detected")}</span>
              ${inc.escalated ? `<span class="pill Critical">Escalated</span>` : ""}
            </div>
            <p><b>Summary:</b> ${esc(inc.summary || "No summary available.")}</p>
            <p><b>Why Raised:</b><br>${esc(inc.why_raised || inc.description || "Related feedback requires review.")}</p>
            <p><b>Store & Category:</b><br>${esc(inc.store_id)} · ${nice(inc.issue_type)}</p>
            <p><b>Report Count:</b> ${inc.report_count || 1} · <b>First Seen:</b> ${esc((inc.first_seen || "—").slice(0, 19))} · <b>Latest Seen:</b> ${esc((inc.latest_seen || "—").slice(0, 19))}</p>
            <p><b>Suggested Owner:</b> ${esc(inc.department || "Unassigned")} · <b>Assigned To:</b> ${esc(inc.assigned_user || "Unassigned")}</p>
            <h3 style="margin-top:18px">Original Evidence (${(inc.evidence || []).length})</h3>
            ${evHtml || "<p class='muted'>No linked evidence yet.</p>"}
            <h3 style="margin-top:18px">Investigation & Audit History</h3>
            ${
              (inc.audit || []).length
                ? inc.audit
                    .map(
                      (a) =>
                        `<div class="audit-row">
                          <b>${esc(a.action || "Update")}</b> · ${esc((a.timestamp || "").slice(0, 19))} by ${esc(a.actor || "User")}
                          <p>${esc(a.note || "")}</p>
                        </div>`
                    )
                    .join("")
                : "<p class='muted'>No audit entries recorded yet.</p>"
            }`
          );

          const dm = $("#detail-modal");
          if (dm) dm.classList.remove("hidden");
          toast("Problem statement view recorded");
        } catch (err) {
          toast(err.message, "error");
        }
        return;
      }

      // Quick action button (Acknowledge / Resolve)
      const quick = e.target.closest(".quick-action");
      if (quick) {
        const card = quick.closest(".incident-card");
        if (!card) return;
        const id = card.dataset.id;
        const next = quick.dataset.quickStatus;
        if (!id || !next) return;

        try {
          const owner = card.querySelector(".owner-input")?.value || "";
          const dept = card.querySelector(".department-select")?.value || "Unassigned";
          await api(`/api/incidents/${encodeURIComponent(id)}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              status: next,
              assigned_user: owner,
              department: dept,
              note: next === "Resolved" ? "Marked resolved from quick action" : "Acknowledged from quick action",
            }),
          });
          toast(next === "Resolved" ? "Incident marked resolved" : "Incident acknowledged", "success");
          loadSignals();
          loadActions();
          loadOverview();
        } catch (err) {
          toast(err.message, "error");
        }
        return;
      }

      // Save incident update button
      const save = e.target.closest(".save-incident");
      if (save) {
        const card = save.closest(".incident-card");
        if (!card) return;
        const id = card.dataset.id;
        if (!id) return;

        const status = card.querySelector(".status-select")?.value;
        const owner = card.querySelector(".owner-input")?.value;
        const dept = card.querySelector(".department-select")?.value;
        const note = card.querySelector(".note-input")?.value || "";

        try {
          await api(`/api/incidents/${encodeURIComponent(id)}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              status: status,
              assigned_user: owner,
              department: dept,
              resolution: note || undefined,
              note: note || "Workflow update saved",
            }),
          });
          toast("Incident update and audit log saved", "success");
          loadSignals();
          loadActions();
        } catch (err) {
          toast(err.message, "error");
        }
        return;
      }
    });

    // 2. Safe Event Listeners for Search & Submission Forms
    safeOn("#search-feedback", "click", (e) => {
      e.preventDefault();
      loadFeedback();
    });

    safeOn("#feedback-form", "submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      const submitBtn = form.querySelector("button[type='submit']") || form.querySelector("button.primary");
      if (submitBtn) {
        if (submitBtn.disabled) return;
        submitBtn.disabled = true;
        submitBtn.dataset.origText = submitBtn.textContent;
        submitBtn.textContent = "Ingesting...";
      }
      const data = Object.fromEntries(new FormData(form));
      const msgEl = $("#form-message");
      try {
        const r = await api("/api/feedback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        if (msgEl) msgEl.textContent = r.message || "Feedback saved successfully.";
        form.reset();
        toast("Feedback saved", "success");
        await Promise.all([loadOverview(), loadFeedback(), loadSignals()]);
      } catch (err) {
        if (msgEl) msgEl.textContent = err.message;
        toast(err.message, "error");
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = submitBtn.dataset.origText || "Submit feedback";
        }
      }
    });

    safeOn("#import-form", "submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      const fd = new FormData(form);
      const msgEl = $("#import-message");
      if (msgEl) msgEl.textContent = "Processing import batch...";
      try {
        const r = await api("/api/feedback/import", {
          method: "POST",
          body: fd,
        });
        let summary = `Inserted: ${r.inserted || 0}; duplicates: ${r.duplicates || 0}; invalid: ${r.invalid || 0}.`;
        if (r.errors && r.errors.length) {
          summary += ` First error: ${r.errors[0].error}`;
        }
        if (msgEl) msgEl.textContent = summary;
        toast("Import processed successfully", "success");
        loadOverview();
        loadSignals();
        loadFeedback();
      } catch (err) {
        if (msgEl) msgEl.textContent = err.message;
        toast(err.message, "error");
      }
    });

    // 3. Dropdowns & Filter Inputs (Null-Safe Binding)
    ["signal-sort", "action-sort"].forEach((id) => {
      safeOn(`#${id}`, "change", () => {
        if (id === "signal-sort") loadSignals();
        else loadActions();
      });
    });

    ["signal-search", "signal-severity", "signal-status"].forEach((id) => {
      const evt = id.endsWith("search") ? "input" : "change";
      safeOn(`#${id}`, evt, loadSignals);
    });

    ["action-search", "action-severity", "action-status"].forEach((id) => {
      const evt = id.endsWith("search") ? "input" : "change";
      safeOn(`#${id}`, evt, loadActions);
    });

    safeOn("#feedback-search", "keypress", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        loadFeedback();
      }
    });

    safeOn("#store-filter", "change", loadFeedback);
    safeOn("#issue-filter", "change", loadFeedback);

    // 4. Initial Page Display
    showPage("overview");
  }

  // --- Bootstrap ---
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initApp);
  } else {
    initApp();
  }
})();
