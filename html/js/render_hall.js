// js/render_hall.js

/**
 * Clears the main container and hides optional background layers.
 * This is the common entry point before rendering any slide type.
 *
 * @returns {HTMLElement} The cleared container element.
 */
function clearScreen() {
  const container = document.getElementById("container");

  // Hide and reset the main container
  container.style.display = "none";
  container.className = "";
  container.innerHTML = "";

  // Hide the cover background if it exists (used in intro slides)
  const coverBg = document.getElementById("cover-background");
  if (coverBg) coverBg.style.display = "none";

  return container;
}

/**
 * Renders a completely blank screen.
 * Intentionally leaves only the fixed background logo visible.
 */
function renderBlank() {
  clearScreen();
  // Do nothing else on purpose
}

/**
 * Renders hymn/lyrics slides.
 * Handles verse segmentation, interlude markers, and balanced line splitting.
 *
 * @param {Object} data - Slide data containing headline and caption.
 */
function renderLyrics(data) {
    const container = clearScreen();
    container.className = "lyrics";
    container.style.display = "flex";

    // Split raw lyrics text into individual lines
    const lines = String(data.headline || "").split("\n");

    // Segment lyrics into logical groups (verses, interludes, etc.)
    const segments = segmentLyrics(lines);

    // Convert each segment into HTML
    const processedHTML = segments.map((group, index) => {
        const sublines = [];

        for (const line of group) {
            // Split long lines into visually balanced parts
            const split = splitBalanced(line);
            for (const part of split) {
                sublines.push(`<div>${part}</div>`);
            }
        }

        // Note:
        // Amen handling logic is intentionally conservative here.
        // Any higher-level logic should be handled upstream.
        return `<div class="lyrics-headline">${sublines.join("")}</div>`;
    }).join("");

    // Inject final lyrics HTML structure
    container.innerHTML = `
    <div class="lyrics-box">
        <div class="lyrics-bg"></div>
        <img class="lyrics-logo" src="resources/svg/thepck.svg" alt="logo" />
        <div class="lyrics-captbox">
        <div class="lyrics-caption">${String(data.caption || "")}</div>
        </div>
        ${processedHTML}
    </div>
    `;

    // Auto-shrink only the last visible lyrics block if needed
    const elList = container.querySelectorAll(".lyrics-headline");
    if (elList.length > 0) {
        autoShrinkFont(elList[elList.length - 1]);
    }
}

/**
 * Renders Bible verse slides.
 * Newlines are preserved as explicit <br> elements.
 *
 * @param {Object} data - Slide data containing headline and caption.
 */
function renderVerse(data) {
    const container = clearScreen();
    container.className = "verse";
    container.style.display = "flex";

    container.innerHTML = `
    <div class="verse-box">
    <div class="verse-bg"></div>
        <img class="verse-logo" src="resources/svg/thepck.svg" alt="logo" />  
        <div class="verse-captbox">
            <div class="verse-caption">${data.caption || ""}</div>
        </div>
        <div class="verse-headline">${String(data.headline || '').replace(/\n/g, "<br>")}</div></div>
    `;

    // Automatically reduce font size if verse text overflows
    const verseEl = container.querySelector(".verse-headline");
    autoShrinkFont(verseEl, 100, 5);
}

/**
 * Renders corner-style slides (title + subtitle layout).
 *
 * @param {Object} data - Slide data containing headline and caption.
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
 * Renders anthem slides (choir-focused layout).
 *
 * @param {Object} data - Slide data including main title, choir, and captions.
 */
function renderAnthem(data) {
    const container = clearScreen();

    // Explicitly remove any previous fixed elements
    container.style.display = "none";
    container.innerHTML = "";

    container.className = "anthem-wrapper";
    container.style.display = "flex";

    container.innerHTML = `
    <div class="anthem-container">
        <img class="anthem-logo" src="resources/svg/thepck.svg" alt="logo" />
        <div class="anthem-badge">
            <div class="anthem-main-caption">${data.caption || ""}</div>
            <div class="anthem-choir-caption">${data.caption_choir || ""}</div>
        </div>
        <div class="anthem-headline">${data.headline || ""}</div>
    </div>
    `;
}

/**
 * Renders prayer slides.
 *
 * @param {Object} data - Slide data containing prayer leader and title.
 */
function renderPrayer(data) {
    const container = clearScreen();

    // Remove any previously displayed slide artifacts
    container.style.display = "none";
    container.innerHTML = "";

    container.className = "prayer-wrapper";
    container.style.display = "flex";

    container.innerHTML = `
    <div class="prayer-container">
        <img class="prayer-logo" src="resources/svg/thepck.svg" alt="logo" />
        <div class="prayer-badge">
            <div class="prayer-caption">${data.caption || ""}</div>
        </div>
        <div class="prayer-headline">${data.headline || ""}</div>
    </div>
    `;

    // Auto-shrink prayer headline to fit pill container
    const textEl = container.querySelector(".prayer-headline");
    autoShrinkFont(textEl, 100, 5);
}

/**
 * Renders greeting slides (welcome / announcements).
 *
 * @param {Object} data - Slide data containing headline and caption.
 */
function renderGreet(data) {
    const container = clearScreen();
    container.className = "greet";
    container.style.display = "flex";

    container.innerHTML = `
    <div class="greet-box">
    <div class="greet-bg"></div>
    <img class="greet-logo" src="resources/svg/thepck.svg" alt="logo" />
    <div class="greet-captbox">
        <div class="greet-caption">${data.caption || ""}</div>
    </div>
    <div class="greet-headline">${String(data.headline || '').replace(/\n/g, "<br>")}</div></div>
    `;

    // Adjust font size if greeting text overflows
    const textEl = container.querySelector(".greet-headline");
    autoShrinkFont(textEl, 100, 5);
}

/**
 * Renders the intro slide shown before worship begins.
 *
 * @param {Object} data - Slide data containing headline and caption.
 */
function renderIntro(data) {
    const container = clearScreen();
    container.style.display = "block";
    container.className = "intro";

    container.innerHTML = `
    <div class="intro-headline">${data.headline || ""}</div>
    <div class="intro-caption">${data.caption || ""}</div>
    <div class="intro-fixed-message">
        • 기도로 예배를 준비합니다.<br>
        • 예배를 위하여 핸드폰을 끄시거나 진동으로 합니다.
    </div>
    `;

    // Show background overlay during intro
    const coverBg = document.getElementById("cover-background");
    if (coverBg) coverBg.style.display = "block";

    // Auto-shrink intro headline if necessary
    const textEl = container.querySelector(".intro-headline");
    if (textEl) autoShrinkFont(textEl, 100, 5);
}

/**
 * Renders image slides with a caption overlay.
 *
 * @param {Object} data - Slide data containing image URL and caption.
 */
function renderImage(data) {
    const container = clearScreen();
    container.className = "image";
    container.style.display = "flex";
    
    container.innerHTML = `
    <div class="image-box">
        <div class="image-bg"></div>
        <img class="image-logo" src="resources/svg/thepck.svg" alt="logo" />  
        <div class="image-captbox">
            <div class="image-caption">${data.caption || ""}</div>
        </div>
        <div class="image-headline">
            <img src="${data.headline || ''}" alt="Image" />
        </div>
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