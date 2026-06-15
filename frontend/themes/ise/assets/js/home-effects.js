(function () {
  document.documentElement.classList.add("home-effects-ready");

  var revealItems = Array.prototype.slice.call(document.querySelectorAll("[data-reveal]"));
  var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function show(item) {
    item.classList.add("is-visible");
  }

  if (!revealItems.length) {
    return;
  }

  if (reducedMotion || !("IntersectionObserver" in window)) {
    revealItems.forEach(show);
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) {
        return;
      }

      show(entry.target);
      observer.unobserve(entry.target);
    });
  }, {
    rootMargin: "0px 0px -12% 0px",
    threshold: 0.12
  });

  revealItems.forEach(function (item) {
    observer.observe(item);
  });
})();
