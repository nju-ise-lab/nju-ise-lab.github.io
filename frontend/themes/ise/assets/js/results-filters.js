(function () {
  var root = document.querySelector("[data-results-page]");

  if (!root) {
    return;
  }

  var tabs = Array.prototype.slice.call(root.querySelectorAll("[data-result-tab]"));
  var panels = Array.prototype.slice.call(root.querySelectorAll("[data-result-panel]"));

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
})();
