// Progressive enhancement: a lightbox with a resolution switcher, panning, and
// keyboard navigation. With JS off, every thumbnail is already a plain link to
// a real image; this layer only adds to that.
//
// Display model: the box opens in "Fit" (image scaled to the window, no
// scroll). The switcher offers Fit plus each built tier (S / M / Full);
// selecting a tier shows that file at native pixel size — centered when it
// fits, pannable on both axes when it overflows. The page behind the box is
// scroll-locked while it is open.
"use strict";

(function () {
  function ready(fn) {
    if (document.readyState !== "loading") {
      fn();
    } else {
      document.addEventListener("DOMContentLoaded", fn);
    }
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text) {
      node.textContent = text;
    }
    return node;
  }

  // The switcher entries for a cell: a "Fit" view over the default image, then
  // one native-size entry per built tier (S / M / Full).
  function entriesFor(link) {
    var tiers = [];
    try {
      tiers = JSON.parse(link.dataset.tiers || "[]");
    } catch (e) {
      tiers = [];
    }
    var entries = [{ label: "Fit", url: link.getAttribute("href"), native: false }];
    tiers.forEach(function (tier) {
      entries.push({ label: tier.label, url: tier.url, native: true });
    });
    return entries;
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

    // Build the overlay chrome once.
    var overlay = el("div", "lightbox");
    overlay.hidden = true;
    var figure = el("figure", "lb-figure");
    var image = el("img");
    figure.appendChild(image);

    var prev = el("button", "lb-nav lb-prev", "‹");
    var next = el("button", "lb-nav lb-next", "›");
    var close = el("button", "lb-close", "✕");
    var counter = el("span", "lb-counter");
    var name = el("span", "lb-name");
    var tierbar = el("div", "lb-tiers");
    var download = el("a", "lb-download", "⭳ Download full size");
    download.setAttribute("download", "");

    var bar = el("div", "lb-bar");
    bar.appendChild(counter);
    bar.appendChild(name);
    bar.appendChild(close);
    var foot = el("div", "lb-foot");
    foot.appendChild(tierbar);
    foot.appendChild(download);

    overlay.appendChild(bar);
    overlay.appendChild(prev);
    overlay.appendChild(figure);
    overlay.appendChild(next);
    overlay.appendChild(foot);
    document.body.appendChild(overlay);

    var index = -1;
    var preferred = "Fit"; // remember the chosen view across photos
    var moved = false; // a pan drag just happened; suppress the trailing click
    var lockedAt = 0; // page scroll position captured while the box is open

    function pannable() {
      return (
        figure.scrollWidth > figure.clientWidth ||
        figure.scrollHeight > figure.clientHeight
      );
    }

    // Native images larger than the viewport open centered rather than pinned
    // to a corner.
    function centerPan() {
      if (figure.classList.contains("is-native")) {
        figure.scrollLeft = (figure.scrollWidth - figure.clientWidth) / 2;
        figure.scrollTop = (figure.scrollHeight - figure.clientHeight) / 2;
      }
    }
    image.addEventListener("load", centerPan);

    function applyEntry(entry) {
      figure.classList.toggle("is-native", entry.native);
      image.src = entry.url;
    }

    function buildSwitcher(entries, activeLabel) {
      tierbar.textContent = "";
      entries.forEach(function (entry) {
        var btn = el("button", "lb-tier", entry.label);
        if (entry.label === activeLabel) {
          btn.classList.add("is-active");
        }
        btn.addEventListener("click", function (event) {
          event.stopPropagation();
          preferred = entry.label;
          applyEntry(entry);
          Array.prototype.forEach.call(tierbar.children, function (c) {
            c.classList.toggle("is-active", c === btn);
          });
        });
        tierbar.appendChild(btn);
      });
    }

    function show(i) {
      index = (i + links.length) % links.length;
      var link = links[index];
      var entries = entriesFor(link);
      var chosen = entries[0]; // Fit, unless a remembered view is available
      entries.forEach(function (entry) {
        if (entry.label === preferred) {
          chosen = entry;
        }
      });
      counter.textContent = index + 1 + " / " + links.length;
      name.textContent = link.dataset.name || "";
      buildSwitcher(entries, chosen.label);
      applyEntry(chosen);
      if (link.dataset.full) {
        download.href = link.dataset.full;
        download.hidden = false;
      } else {
        download.hidden = true;
      }
      openBox();
    }

    // Lock the page behind the box without losing the reader's place: pin the
    // body at its current offset (plain `overflow: hidden` on the root would
    // jump the page to the top), and restore the position on close.
    function lockScroll(on) {
      var body = document.body;
      if (on) {
        lockedAt = window.scrollY || document.documentElement.scrollTop || 0;
        body.style.position = "fixed";
        body.style.top = -lockedAt + "px";
        body.style.left = "0";
        body.style.right = "0";
        body.style.overflow = "hidden";
      } else {
        body.style.position = "";
        body.style.top = "";
        body.style.left = "";
        body.style.right = "";
        body.style.overflow = "";
        window.scrollTo(0, lockedAt);
      }
    }

    function openBox() {
      overlay.hidden = false;
      lockScroll(true);
    }

    function closeBox() {
      overlay.hidden = true;
      lockScroll(false);
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

    // The backdrop dismisses; controls and the image do not, and a click that
    // merely ends a pan drag must not dismiss either.
    overlay.addEventListener("click", function (event) {
      if (moved) {
        moved = false;
        return;
      }
      if (event.target === overlay || (event.target === figure && !pannable())) {
        closeBox();
      }
    });
    close.addEventListener("click", function (event) {
      event.stopPropagation();
      closeBox();
    });
    prev.addEventListener("click", function (event) {
      event.stopPropagation();
      show(index - 1);
    });
    next.addEventListener("click", function (event) {
      event.stopPropagation();
      show(index + 1);
    });

    // Drag to pan a native image. Active whenever the figure is a native-size
    // scroll container, so it works the moment the image overflows.
    var dragging = false;
    var startX = 0;
    var startY = 0;
    var startLeft = 0;
    var startTop = 0;
    figure.addEventListener("pointerdown", function (event) {
      if (!figure.classList.contains("is-native")) {
        return;
      }
      dragging = true;
      startX = event.clientX;
      startY = event.clientY;
      startLeft = figure.scrollLeft;
      startTop = figure.scrollTop;
      figure.setPointerCapture(event.pointerId);
      event.preventDefault();
    });
    figure.addEventListener("pointermove", function (event) {
      if (!dragging) {
        return;
      }
      if (event.clientX !== startX || event.clientY !== startY) {
        moved = true;
      }
      figure.scrollLeft = startLeft - (event.clientX - startX);
      figure.scrollTop = startTop - (event.clientY - startY);
    });
    figure.addEventListener("pointerup", function () {
      dragging = false;
    });

    document.addEventListener("keydown", function (event) {
      if (overlay.hidden) {
        return;
      }
      if (event.key === "Escape") {
        closeBox();
      } else if (event.key === "ArrowRight") {
        show(index + 1);
      } else if (event.key === "ArrowLeft") {
        show(index - 1);
      }
    });
  });
})();
