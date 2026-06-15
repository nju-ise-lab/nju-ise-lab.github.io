(function () {
  var counters = document.querySelectorAll("[data-view-path]");

  function setCount(counter, text) {
    var countNode = counter.querySelector("[data-view-count]");
    if (countNode) {
      countNode.textContent = text;
    }
  }

  function viewApi(counter) {
    return counter.getAttribute("data-view-api") || "/api/views";
  }

  counters.forEach(function (counter) {
    var path = counter.getAttribute("data-view-path") || window.location.pathname;

    if (!window.fetch || !path) {
      setCount(counter, "暂不可用");
      return;
    }

    window.fetch(viewApi(counter), {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ path: path })
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("view counter request failed");
        }
        return response.json();
      })
      .then(function (data) {
        if (typeof data.total === "number") {
          setCount(counter, String(data.total));
          return;
        }
        setCount(counter, "暂不可用");
      })
      .catch(function () {
        setCount(counter, "暂不可用");
      });
  });
})();
