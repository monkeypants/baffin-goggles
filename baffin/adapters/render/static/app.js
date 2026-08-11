// Progressive enhancement: a lightbox with keyboard navigation.
// With JS off, every thumbnail is already a plain link to a real image, so
// nothing here is load-bearing — this only upgrades the experience.
"use strict";

(function () {
  function ready(fn) {
    if (document.readyState !== "loading") {
      fn();
    } else {
      document.addEventListener("DOMContentLoaded", fn);
    }
  }

  ready(function () {
    var gallery = document.getElementById("gallery");
    if (!gallery) {
      return;
    }
    var links = Array.prototype.slice.call(gallery.querySelectorAll("a.cell"));
    if (!links.length) {
      return;
    }

    var overlay = document.createElement("div");
    overlay.className = "lightbox";
    overlay.hidden = true;
    var image = document.createElement("img");
    overlay.appendChild(image);
    document.body.appendChild(overlay);

    var index = -1;

    function show(i) {
      index = (i + links.length) % links.length;
      image.src = links[index].getAttribute("href");
      overlay.hidden = false;
    }

    function close() {
      overlay.hidden = true;
      index = -1;
    }

    links.forEach(function (link, i) {
      link.addEventListener("click", function (event) {
        // Videos keep their native behaviour (download / play).
        if (link.dataset.video) {
          return;
        }
        event.preventDefault();
        show(i);
      });
    });

    overlay.addEventListener("click", close);

    document.addEventListener("keydown", function (event) {
      if (overlay.hidden) {
        return;
      }
      if (event.key === "Escape") {
        close();
      } else if (event.key === "ArrowRight") {
        show(index + 1);
      } else if (event.key === "ArrowLeft") {
        show(index - 1);
      }
    });
  });
})();
