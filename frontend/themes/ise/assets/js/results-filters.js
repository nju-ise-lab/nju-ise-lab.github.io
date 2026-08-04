(function () {
  var root = document.querySelector("[data-results-page]");

  if (!root) {
    return;
  }

  var tabs = Array.prototype.slice.call(root.querySelectorAll("[data-result-tab]"));
  var panels = Array.prototype.slice.call(root.querySelectorAll("[data-result-panel]"));

  function locationPanel() {
    var params = new URLSearchParams(window.location.search);
    return params.get("tab") || "publications";
  }

  function updateLocation(panelName, replace) {
    var url = new URL(window.location.href);

    if (panelName === "publications") {
      url.searchParams.delete("tab");
    } else {
      url.searchParams.set("tab", panelName);
    }

    url.searchParams.delete("page");

    window.history[replace ? "replaceState" : "pushState"](
      { panel: panelName },
      "",
      url.pathname + url.search + url.hash
    );
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
      updateLocation(targetName, false);
    }

    return targetName;
  }

  var requestedPanel = locationPanel();
  var initialPanel = activate(requestedPanel, { updateUrl: false });
  if (initialPanel !== requestedPanel || new URLSearchParams(window.location.search).has("page")) {
    updateLocation(initialPanel, true);
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      activate(tab.getAttribute("data-result-tab"), { updateUrl: true });
    });
  });

  window.addEventListener("popstate", function () {
    activate(locationPanel(), { updateUrl: false });
  });
})();
