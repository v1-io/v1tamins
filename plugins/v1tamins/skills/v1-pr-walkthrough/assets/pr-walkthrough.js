    (() => {
      const search = document.getElementById("file-search");
      const layerFilter = document.getElementById("layer-filter");
      const rows = Array.from(document.querySelectorAll("#file-table tbody tr"));
      const status = document.getElementById("control-status");
      const visibleCount = document.getElementById("visible-file-count");
      const details = Array.from(document.querySelectorAll(".layer"));
      const markdownSummary = @@MARKDOWN_SUMMARY@@;

      function updateUrl() {
        try {
          const url = new URL(window.location.href);
          search.value ? url.searchParams.set("q", search.value) : url.searchParams.delete("q");
          layerFilter.value ? url.searchParams.set("layer", layerFilter.value) : url.searchParams.delete("layer");
          window.history.replaceState(null, "", url);
        } catch (_) {
          // Local file history may be unavailable; filtering still works.
        }
      }

      function applyFilters({ announce = true } = {}) {
        const query = search.value.trim().toLowerCase();
        const layer = layerFilter.value;
        let count = 0;
        rows.forEach((row) => {
          const matchesQuery = !query || row.dataset.search.includes(query);
          const matchesLayer = !layer || row.dataset.layer === layer;
          const visible = matchesQuery && matchesLayer;
          row.classList.toggle("is-filtered", !visible);
          if (visible) count += 1;
        });
        visibleCount.textContent = String(count);
        if (announce) status.textContent = `${count} ${count === 1 ? "file" : "files"} shown.`;
        updateUrl();
      }

      const params = new URLSearchParams(window.location.search);
      search.value = params.get("q") || "";
      const requestedLayer = params.get("layer") || "";
      if (Array.from(layerFilter.options).some((option) => option.value === requestedLayer)) {
        layerFilter.value = requestedLayer;
      }
      applyFilters({ announce: false });

      search.addEventListener("input", () => applyFilters());
      layerFilter.addEventListener("change", () => applyFilters());

      document.getElementById("expand-all").addEventListener("click", () => {
        details.forEach((detail) => { detail.open = true; });
        status.textContent = "All walkthrough layers expanded.";
      });

      document.getElementById("collapse-all").addEventListener("click", () => {
        details.forEach((detail) => { detail.open = false; });
        status.textContent = "All walkthrough layers collapsed.";
      });

      async function copyText(text) {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(text);
          return;
        }
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        const copied = document.execCommand("copy");
        textarea.remove();
        if (!copied) throw new Error("Copy failed");
      }

      document.getElementById("copy-summary").addEventListener("click", async () => {
        try {
          await copyText(markdownSummary);
          status.textContent = "Markdown summary copied.";
        } catch (_) {
          status.textContent = "Copy failed. Select the summary from the Overview section instead.";
        }
      });

      document.querySelectorAll(".sort-button").forEach((button) => {
        button.addEventListener("click", () => {
          const header = button.closest("th");
          const key = button.dataset.sort;
          const nextDirection = header.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
          document.querySelectorAll("th[aria-sort]").forEach((item) => {
            item.setAttribute("aria-sort", "none");
            item.querySelector(".sort-indicator").textContent = "\u2195";
          });
          header.setAttribute("aria-sort", nextDirection);
          header.querySelector(".sort-indicator").textContent = nextDirection === "ascending" ? "\u2191" : "\u2193";
          rows.sort((a, b) => {
            const aValue = key === "path" ? a.querySelector(".path-link").textContent : a.dataset.layerLabel;
            const bValue = key === "path" ? b.querySelector(".path-link").textContent : b.dataset.layerLabel;
            const result = aValue.localeCompare(bValue);
            return nextDirection === "ascending" ? result : -result;
          });
          const body = document.querySelector("#file-table tbody");
          rows.forEach((row) => body.appendChild(row));
          status.textContent = `Sorted by ${key}, ${nextDirection}.`;
        });
      });

      function clearHighlights() {
        document.querySelectorAll(".is-highlighted").forEach((element) => element.classList.remove("is-highlighted"));
      }

      function highlightTarget(target) {
        clearHighlights();
        const row = document.getElementById(target);
        if (row) row.classList.add("is-highlighted");
        document.querySelectorAll(`.flow-node-link[data-target="${CSS.escape(target)}"]`).forEach((node) => node.classList.add("is-highlighted"));
      }

      document.querySelectorAll(".flow-node-link").forEach((node) => {
        node.addEventListener("mouseenter", () => highlightTarget(node.dataset.target));
        node.addEventListener("focusin", () => highlightTarget(node.dataset.target));
        node.addEventListener("mouseleave", clearHighlights);
        node.addEventListener("focusout", clearHighlights);
      });

      rows.forEach((row) => {
        row.addEventListener("mouseenter", () => highlightTarget(row.id));
        row.addEventListener("focusin", () => highlightTarget(row.id));
        row.addEventListener("mouseleave", clearHighlights);
        row.addEventListener("focusout", clearHighlights);
      });

      document.querySelectorAll("time[data-local-time]").forEach((time) => {
        const value = new Date(time.dateTime);
        if (!Number.isNaN(value.getTime())) {
          time.textContent = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(value);
        }
      });
    })();
