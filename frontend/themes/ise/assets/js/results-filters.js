(function () {
  var root = document.querySelector("[data-results-page]");

  if (!root) {
    return;
  }

  var tabs = Array.prototype.slice.call(root.querySelectorAll("[data-result-tab]"));
  var panels = Array.prototype.slice.call(root.querySelectorAll("[data-result-panel]"));
  var paginatedPanels = Array.prototype.slice.call(root.querySelectorAll("[data-paginated-panel]"));
  var paginationByPanel = {};

  function pageTokens(currentPage, pageCount) {
    var pages = [1, currentPage - 1, currentPage, currentPage + 1, pageCount]
      .filter(function (page) {
        return page >= 1 && page <= pageCount;
      })
      .filter(function (page, index, values) {
        return values.indexOf(page) === index;
      })
      .sort(function (a, b) {
        return a - b;
      });
    var tokens = [];
    pages.forEach(function (page, index) {
      if (index > 0 && page - pages[index - 1] > 1) {
        tokens.push("ellipsis");
      }
      tokens.push(page);
    });
    return tokens;
  }

  function locationState() {
    var params = new URLSearchParams(window.location.search);
    var requestedPage = Number(params.get("page"));
    return {
      panel: params.get("tab") || "publications",
      page: Number.isFinite(requestedPage) && requestedPage > 0 ? requestedPage : 1,
    };
  }

  function updateLocation(panelName, page, replace) {
    var url = new URL(window.location.href);

    if (panelName === "publications") {
      url.searchParams.delete("tab");
    } else {
      url.searchParams.set("tab", panelName);
    }

    if (page > 1) {
      url.searchParams.set("page", String(page));
    } else {
      url.searchParams.delete("page");
    }

    window.history[replace ? "replaceState" : "pushState"](
      { panel: panelName, page: page },
      "",
      url.pathname + url.search + url.hash
    );
  }

  function directResultCards(list) {
    return Array.prototype.filter.call(list.children, function (item) {
      return item.classList && item.classList.contains("research-result-card");
    });
  }

  function setupPagination(panel, initialState) {
    var panelName = panel.getAttribute("data-result-panel");
    var list = panel.querySelector("[data-result-list]");
    var pager = panel.querySelector("[data-results-pagination]");
    if (!panelName || !list || !pager) {
      return;
    }

    var items = directResultCards(list);
    var pageSize = Number(panel.getAttribute("data-page-size")) || 10;
    var pageCount = Math.max(1, Math.ceil(items.length / pageSize));
    var previous = pager.querySelector("[data-page-prev]");
    var next = pager.querySelector("[data-page-next]");
    var numbers = pager.querySelector("[data-page-numbers]");
    var summary = pager.querySelector("[data-page-summary]");
    var currentPage = panelName === initialState.panel ? initialState.page : 1;

    function clearNumbers() {
      while (numbers.firstChild) {
        numbers.removeChild(numbers.firstChild);
      }
    }

    function renderNumbers() {
      clearNumbers();
      pageTokens(currentPage, pageCount).forEach(function (token) {
        if (token === "ellipsis") {
          var ellipsis = document.createElement("span");
          ellipsis.className = "results-pagination__ellipsis";
          ellipsis.textContent = "…";
          ellipsis.setAttribute("aria-hidden", "true");
          numbers.appendChild(ellipsis);
          return;
        }

        var button = document.createElement("button");
        button.type = "button";
        button.textContent = String(token);
        button.setAttribute("aria-label", "第 " + token + " 页");
        button.className = "results-pagination__page";
        if (token === currentPage) {
          button.classList.add("is-active");
          button.setAttribute("aria-current", "page");
        }
        button.addEventListener("click", function () {
          showPage(token, { moveToPanel: true, updateUrl: true });
        });
        numbers.appendChild(button);
      });
    }

    function showPage(page, options) {
      var settings = options || {};
      currentPage = Math.max(1, Math.min(Number(page) || 1, pageCount));
      var start = (currentPage - 1) * pageSize;
      var end = Math.min(start + pageSize, items.length);

      items.forEach(function (item, index) {
        var visible = index >= start && index < end;
        item.hidden = !visible;
        item.setAttribute("aria-hidden", visible ? "false" : "true");
      });

      previous.disabled = currentPage === 1;
      next.disabled = currentPage === pageCount;
      summary.textContent = items.length ? start + 1 + "–" + end + " / " + items.length : "0 / 0";
      renderNumbers();

      if (settings.updateUrl) {
        updateLocation(panelName, currentPage, false);
      }

      if (settings.moveToPanel) {
        var top = panel.getBoundingClientRect().top + window.scrollY - 110;
        window.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
      }
    }

    previous.addEventListener("click", function () {
      showPage(currentPage - 1, { moveToPanel: true, updateUrl: true });
    });
    next.addEventListener("click", function () {
      showPage(currentPage + 1, { moveToPanel: true, updateUrl: true });
    });

    paginationByPanel[panelName] = {
      currentPage: function () {
        return currentPage;
      },
      showPage: showPage,
    };

    pager.hidden = pageCount <= 1;
    showPage(currentPage, { moveToPanel: false, updateUrl: false });
  }

  function hasPanel(name) {
    return panels.some(function (panel) {
      return panel.getAttribute("data-result-panel") === name;
    });
  }

  function activate(name, options) {
    var settings = options || {};
    var targetName = hasPanel(name) ? name : "publications";

    tabs.forEach(function (tab) {
      var active = tab.getAttribute("data-result-tab") === targetName;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
      tab.setAttribute("tabindex", active ? "0" : "-1");
    });

    panels.forEach(function (panel) {
      var active = panel.getAttribute("data-result-panel") === targetName;
      panel.classList.toggle("is-active", active);
      panel.hidden = !active;
    });

    if (settings.updateUrl) {
      var pagination = paginationByPanel[targetName];
      updateLocation(targetName, pagination ? pagination.currentPage() : 1, false);
    }

    return targetName;
  }

  var initialState = locationState();
  paginatedPanels.forEach(function (panel) {
    setupPagination(panel, initialState);
  });

  var initialPanel = activate(initialState.panel, { updateUrl: false });
  var initialPagination = paginationByPanel[initialPanel];
  var normalizedPage = initialPagination ? initialPagination.currentPage() : 1;
  if (initialPanel !== initialState.panel || normalizedPage !== initialState.page) {
    updateLocation(initialPanel, normalizedPage, true);
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      activate(tab.getAttribute("data-result-tab"), { updateUrl: true });
    });
  });

  window.addEventListener("popstate", function () {
    var state = locationState();
    var panelName = activate(state.panel, { updateUrl: false });
    var pagination = paginationByPanel[panelName];
    if (pagination) {
      pagination.showPage(state.page, { moveToPanel: false, updateUrl: false });
    }
  });
})();
