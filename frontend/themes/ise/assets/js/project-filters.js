(function () {
  var root = document.querySelector("[data-projects-page]");

  if (!root) {
    return;
  }

  var filters = Array.prototype.slice.call(root.querySelectorAll("[data-project-filter]"));
  var cards = Array.prototype.slice.call(root.querySelectorAll("[data-project-card]"));

  filters.forEach(function (filter) {
    filter.addEventListener("click", function () {
      var value = filter.getAttribute("data-project-filter");

      filters.forEach(function (item) {
        item.classList.toggle("is-active", item === filter);
      });

      cards.forEach(function (card) {
        card.hidden = value !== "all" && card.getAttribute("data-project-card") !== value;
      });
    });
  });
})();
