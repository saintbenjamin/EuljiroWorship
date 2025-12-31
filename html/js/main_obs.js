// js/main_obs.js

/**
 * Mapping table from slide "style" keys to their corresponding render functions.
 * Each function is responsible for rendering a specific slide layout
 * into the shared #container element.
 */
const renderMap = {
    lyrics: renderLyrics,
    verse: renderVerse,
    corner: renderCorner,
    anthem: renderAnthem,
    prayer: renderPrayer,
    greet: renderGreet,
    image: renderImage,
    blank: renderBlank,
};

/**
 * Opens a WebSocket connection and listens for incoming slide data.
 * Each message is expected to be a JSON string describing:
 *   - style: slide type key (used to select a renderer)
 *   - other fields consumed by the renderer (headline, caption, etc.)
 */
connectWebSocket((raw) => {
    let data;

    // Parse incoming WebSocket payload as JSON.
    // If parsing fails, keep the current screen unchanged.
    try {
        data = JSON.parse(raw);
    } catch (e) {
        console.error("[!] JSON 파싱 실패:", e);
        return;
    }

    // Select renderer based on slide style.
    const fn = renderMap[data.style];

    // Fallback: render a blank screen for unknown styles.
    if (!fn) {
        renderBlank(data);
        return;
    }

    // Render the slide using the matched renderer.
    fn(data);
});