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