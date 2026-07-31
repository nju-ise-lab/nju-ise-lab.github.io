(function () {
  var root = document.querySelector("[data-results-page]");

  if (!root) {
    return;
  }

  var tabs = Array.prototype.slice.call(root.querySelectorAll("[data-result-tab]"));
  var panels = Array.prototype.slice.call(root.querySelectorAll("[data-result-panel]"));
  var paginatedPanels = Array.prototype.slice.call(root.querySelectorAll("[data-paginated-panel]"));

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

  function setupPagination(panel) {
    var list = panel.querySelector("[data-result-list]");
    var pager = panel.querySelector("[data-results-pagination]");
    if (!list || !pager) {
      return;
    }

    var items = Array.prototype.slice.call(list.querySelectorAll(":scope > .research-result-card"));
    var pageSize = Number(panel.getAttribute("data-page-size")) || 10;
    var pageCount = Math.ceil(items.length / pageSize);
    var previous = pager.querySelector("[data-page-prev]");
    var next = pager.querySelector("[data-page-next]");
    var numbers = pager.querySelector("[data-page-numbers]");
    var summary = pager.querySelector("[data-page-summary]");
    var currentPage = 1;

    if (pageCount <= 1) {
      pager.hidden = true;
      return;
    }

    function renderNumbers() {
      numbers.replaceChildren();
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
          showPage(token, true);
        });
        numbers.appendChild(button);
      });
    }

    function showPage(page, moveToPanel) {
      currentPage = Math.max(1, Math.min(page, pageCount));
      var start = (currentPage - 1) * pageSize;
      var end = Math.min(start + pageSize, items.length);
      items.forEach(function (item, index) {
        var visible = index >= start && index < end;
        item.hidden = !visible;
        item.setAttribute("aria-hidden", visible ? "false" : "true");
      });
      previous.disabled = currentPage === 1;
      next.disabled = currentPage === pageCount;
      summary.textContent = start + 1 + "–" + end + " / " + items.length;
      renderNumbers();

      if (moveToPanel) {
        var top = panel.getBoundingClientRect().top + window.scrollY - 110;
        window.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
      }
    }

    previous.addEventListener("click", function () {
      showPage(currentPage - 1, true);
    });
    next.addEventListener("click", function () {
      showPage(currentPage + 1, true);
    });
    pager.hidden = false;
    showPage(1, false);
  }

  function activate(name) {
    tabs.forEach(function (tab) {
      var active = tab.getAttribute("data-result-tab") === name;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });

    panels.forEach(function (panel) {
      var active = panel.getAttribute("data-result-panel") === name;
      panel.classList.toggle("is-active", active);
      panel.hidden = !active;
    });
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      activate(tab.getAttribute("data-result-tab"));
    });
  });

  paginatedPanels.forEach(setupPagination);
})();
