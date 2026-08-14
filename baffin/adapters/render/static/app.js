// Progressive enhancement: a lightbox with on-screen controls and keyboard nav.
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

  function tiersFor(link) {
    try {
      return JSON.parse(link.dataset.tiers || "[]");
    } catch (e) {
      return [];
    }
  }

  function tierByLabel(tiers, label) {
    for (var i = 0; i < tiers.length; i++) {
      if (tiers[i].label === label) {
        return tiers[i];
      }
    }
    return null;
  }

  function tierByUrl(tiers, url) {
    for (var i = 0; i < tiers.length; i++) {
      if (tiers[i].url === url) {
        return tiers[i];
      }
    }
    return null;
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
    var tierbar = el("div", "lb-tiers");
    var download = el("a", "lb-download", "⭳ Download full size");
    download.setAttribute("download", "");

    var bar = el("div", "lb-bar");
    bar.appendChild(counter);
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
    var preferred = null; // remember the label (S/M/Full) across photos
    var moved = false; // a pan drag just happened; suppress the trailing click

    // "Full" shows the image at natural size (1:1) in a pannable figure; the
    // smaller tiers fit the viewport. That is what makes the tiers look
    // different — otherwise both are scaled down to the same on-screen size.
    function applyMode(label) {
      var actual = label === "Full";
      figure.classList.toggle("is-actual", actual);
    }

    function centerPan() {
      if (figure.classList.contains("is-actual")) {
        figure.scrollLeft = (figure.scrollWidth - figure.clientWidth) / 2;
        figure.scrollTop = (figure.scrollHeight - figure.clientHeight) / 2;
      }
    }
    image.addEventListener("load", centerPan);

    function display(tier, fallbackUrl) {
      image.src = tier ? tier.url : fallbackUrl;
      applyMode(tier ? tier.label : null);
    }

    function buildTierbar(tiers, activeLabel) {
      tierbar.textContent = "";
      tiers.forEach(function (tier) {
        var btn = el("button", "lb-tier", tier.label);
        if (tier.label === activeLabel) {
          btn.classList.add("is-active");
        }
        btn.addEventListener("click", function (event) {
          event.stopPropagation();
          preferred = tier.label;
          display(tier, tier.url);
          Array.prototype.forEach.call(tierbar.children, function (c) {
            c.classList.toggle("is-active", c === btn);
          });
        });
        tierbar.appendChild(btn);
      });
      tierbar.hidden = tiers.length === 0;
    }

    function show(i) {
      index = (i + links.length) % links.length;
      var link = links[index];
      var tiers = tiersFor(link);
      var href = link.getAttribute("href");
      // Prefer the last-picked label; else the tier matching the default link.
      var chosen = null;
      if (preferred) {
        chosen = tierByLabel(tiers, preferred);
      }
      if (!chosen) {
        chosen = tierByUrl(tiers, href);
      }
      counter.textContent = index + 1 + " / " + links.length;
      buildTierbar(tiers, chosen ? chosen.label : null);
      display(chosen, href);
      if (link.dataset.full) {
        download.href = link.dataset.full;
        download.hidden = false;
      } else {
        download.hidden = true;
      }
      overlay.hidden = false;
    }

    function closeBox() {
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

    // Clicking the backdrop closes; clicks on controls/image do not, and a
    // click that merely ends a pan drag must not close either.
    overlay.addEventListener("click", function (event) {
      if (moved) {
        moved = false;
        return;
      }
      var fitMode = !figure.classList.contains("is-actual");
      if (event.target === overlay || (event.target === figure && fitMode)) {
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

    // Drag to pan when viewing the full image at 1:1. `moved` records that a
    // drag happened, so the trailing click doesn't close the lightbox.
    var dragging = false;
    var startX = 0;
    var startY = 0;
    var startLeft = 0;
    var startTop = 0;
    figure.addEventListener("pointerdown", function (event) {
      if (!figure.classList.contains("is-actual")) {
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
