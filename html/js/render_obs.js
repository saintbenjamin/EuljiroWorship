// js/render_obs.js

/**
 * Clears the main overlay container.
 * Resets visibility, CSS class, and rendered HTML content.
 *
 * @returns {HTMLElement} The cleared container element.
 */
function clearScreen() {
    const container = document.getElementById("container");
    container.style.display = "none";
    container.className = "";
    container.innerHTML = "";
    return container;
}

/**
 * Renders a completely blank overlay.
 * Used when no slide content should be visible.
 *
 * @param {*} _data Unused slide payload.
 */
function renderBlank(_data) {
    clearScreen();
}

/**
 * Renders a lyrics slide.
 * Displays background, logo, caption badge, and multiline headline text.
 * Font size is automatically reduced to prevent overflow.
 *
 * @param {Object} data Slide data object.
 * @param {string} data.headline Lyrics text (newline-separated).
 * @param {string} data.caption Caption text shown above the lyrics.
 */
function renderLyrics(data) {
    const container = clearScreen();
    container.className = "lyrics";
    container.style.display = "flex";
    container.innerHTML = `
        <div class="lyrics-bg"></div>
        <img class="lyrics-logo" src="resources/svg/thepck.svg" alt="logo" />
        <div class="lyrics-captbox">
            <div class="lyrics-caption">${String(data.caption || "")}</div>
        </div>
        <div class="lyrics-headline">${String(data.headline || "").replace(/\n/g, "<br>")}</div>
    `;
    const el = container.querySelector(".lyrics-headline");
    autoShrinkFont(el);
}

/**
 * Renders a verse (scripture) slide.
 * Text is allowed to wrap across multiple lines.
 *
 * @param {Object} data Slide data object.
 * @param {string} data.headline Verse text.
 * @param {string} data.caption Verse reference.
 */
function renderVerse(data) {
    const container = clearScreen();
    container.className = "verse";
    container.style.display = "flex";
    container.innerHTML = `
        <div class="verse-bg"></div>
        <img class="verse-logo" src="resources/svg/thepck.svg" alt="logo" />
        <div class="verse-captbox">
            <div class="verse-caption">${data.caption || ""}</div>
        </div>
        <div class="verse-headline">${String(data.headline || "").replace(/\n/g, "<br>")}</div>
    `;

    const verseEl = container.querySelector(".verse-headline");
    autoShrinkFont(verseEl);
}

/**
 * Renders a corner-style slide.
 * Used for compact headline + caption layouts.
 *
 * @param {Object} data Slide data object.
 * @param {string} data.headline Main headline text.
 * @param {string} data.caption Secondary caption text.
 */
function renderCorner(data) {
    const container = clearScreen();
    container.style.display = "block";
    container.className = "corner";
    container.innerHTML = `
        <div class="corner-box-wrapper">
            <div class="corner-box green-box">
                <img class="corner-logo" src="resources/svg/thepck.svg" alt="logo" />
                <div class="corner-headline">${data.headline || ""}</div>
            </div>
            <div class="corner-box red-box">
                <div class="corner-caption">${data.caption || ""}</div>
            </div>
        </div>
    `;
}

/**
 * Renders an anthem slide.
 * Displays choir information and anthem title in a centered layout.
 *
 * @param {Object} data Slide data object.
 * @param {string} data.headline Anthem title.
 * @param {string} data.caption Main caption.
 * @param {string} data.caption_choir Choir name(s).
 */
function renderAnthem(data) {
    const container = clearScreen();
    container.style.display = "none";
    container.innerHTML = "";

    container.className = "anthem-wrapper";
    container.style.display = "flex";
    container.innerHTML = `
        <div class="anthem-container">
            <div class="anthem-badge">
                <div class="anthem-main-caption">${data.caption || ""}</div>
                <div class="anthem-choir-caption">${data.caption_choir || ""}</div>
                <img class="anthem-logo" src="resources/svg/thepck.svg" alt="logo" />
            </div>
            <div class="anthem-headline">${data.headline || ""}</div>
        </div>
    `;
}

/**
 * Renders a prayer slide.
 * Shows a circular badge with the prayer leader and a headline text.
 *
 * @param {Object} data Slide data object.
 * @param {string} data.headline Prayer title or content.
 * @param {string} data.caption Prayer leader name.
 */
function renderPrayer(data) {
    const container = clearScreen();
    container.style.display = "none";
    container.innerHTML = "";

    container.className = "prayer-wrapper";
    container.style.display = "flex";
    container.innerHTML = `
        <div class="prayer-container">
            <div class="prayer-badge">
                <div class="prayer-caption">${data.caption || ""}</div>
                <img class="prayer-logo" src="resources/svg/thepck.svg" alt="logo" />
            </div>
            <div class="prayer-headline">${data.headline || ""}</div>
        </div>
    `;
}

/**
 * Renders a greeting slide.
 * Used for welcome messages or announcements.
 *
 * @param {Object} data Slide data object.
 * @param {string} data.headline Greeting text.
 * @param {string} data.caption Short caption label.
 */
function renderGreet(data) {
    const container = clearScreen();
    container.className = "greet";
    container.style.display = "flex";
    container.innerHTML = `
        <div class="greet-bg"></div>
        <img class="greet-logo" src="resources/svg/thepck.svg" alt="logo" />
        <div class="greet-captbox">
            <div class="greet-caption">${data.caption || ""}</div>
        </div>
        <div class="greet-headline">${String(data.headline || "").replace(/\n/g, "<br>")}</div>
    `;

    const textEl = container.querySelector(".greet-headline");
    autoShrinkFont(textEl, 48, 5);
}

/**
 * Renders an image-only slide.
 * Displays an image anchored to the lower-right corner.
 *
 * @param {Object} data Slide data object.
 * @param {string} data.headline Image URL.
 */
function renderImage(data) {
    const container = clearScreen();
    container.style.display = "block";
    container.className = "image";
    container.innerHTML = `
        <div class="image-show">
            <img src="${data.headline || ""}" alt="Image" />
        </div>
    `;
}

/**
 * Renders video slides (HTML5) with strict aspect-ratio preservation.
 *
 * - Uses data.headline as the video URL/path.
 * - No caption/headline text is shown on screen.
 * - Video is centered, letterboxed as needed (object-fit: contain).
 * - Optional hover controls (play/pause, stop, -5s, +5s) appear on mouse move.
 *
 * @param {Object} data - Slide data containing video URL in `headline`.
 */
function renderVideo(data) {
  const container = clearScreen();
  container.className = "video";
  container.style.display = "flex";

  const src = data.headline || "";

  container.innerHTML = `
    <div class="video-box" style="
      position: relative;
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #000;
      overflow: hidden;
    ">
      <video class="video-player" style="
        width: 100%;
        height: 100%;
        object-fit: contain;     /* keep original aspect ratio, letterbox if needed */
        object-position: center; /* always centered */
        background: #000;
      "
        src="${src}"
        autoplay
        muted
        playsinline
        preload="metadata"
      ></video>

      <div class="video-controls" style="
        position: absolute;
        left: 50%;
        bottom: 24px;
        transform: translateX(-50%);
        display: flex;
        gap: 10px;
        padding: 10px 12px;
        border-radius: 12px;
        background: rgba(0,0,0,0.55);
        opacity: 0;
        pointer-events: none;
        transition: opacity 160ms ease;
        user-select: none;
      ">
        <button data-act="toggle" style="padding:8px 10px; border-radius:10px;">▶︎/❚❚</button>
        <button data-act="stop"   style="padding:8px 10px; border-radius:10px;">■</button>
        <button data-act="back"   style="padding:8px 10px; border-radius:10px;">-5s</button>
        <button data-act="fwd"    style="padding:8px 10px; border-radius:10px;">+5s</button>
      </div>
    </div>
  `;

  const box = container.querySelector(".video-box");
  const video = container.querySelector(".video-player");
  const controls = container.querySelector(".video-controls");

  // If autoplay is blocked, try to start on first click.
  video.addEventListener("click", async () => {
    try { await video.play(); } catch (_) {}
  });

  let hideTimer = null;
  const showControls = () => {
    controls.style.opacity = "1";
    controls.style.pointerEvents = "auto";
    if (hideTimer) clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      controls.style.opacity = "0";
      controls.style.pointerEvents = "none";
    }, 1400);
  };

  box.addEventListener("mousemove", showControls);
  box.addEventListener("mouseenter", showControls);
  box.addEventListener("mouseleave", () => {
    if (hideTimer) clearTimeout(hideTimer);
    controls.style.opacity = "0";
    controls.style.pointerEvents = "none";
  });

  controls.addEventListener("click", async (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    const act = btn.getAttribute("data-act");

    try {
      if (act === "toggle") {
        if (video.paused) await video.play();
        else video.pause();
      } else if (act === "stop") {
        video.pause();
        video.currentTime = 0;
      } else if (act === "back") {
        video.currentTime = Math.max(0, (video.currentTime || 0) - 5);
      } else if (act === "fwd") {
        video.currentTime = Math.min(video.duration || Infinity, (video.currentTime || 0) + 5);
      }
    } catch (_) {}
    showControls();
  });
}