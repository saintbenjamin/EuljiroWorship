// js/main_hall.js

/**
 * Mapping table from slide "style" keys to their corresponding renderer functions.
 * Each renderer is responsible for building DOM markup under #container.
 */
const renderMap = {
    lyrics: renderLyrics,
    verse: renderVerse,
    corner: renderCorner,
    anthem: renderAnthem,
    prayer: renderPrayer,
    greet: renderGreet,
    image: renderImage,
    intro: renderIntro,
    video: renderVideo,
    blank: renderBlank,
};

/**
 * Establishes a WebSocket connection and renders incoming slide payloads.
 * The server sends a JSON string describing the slide to render.
 *
 * Expected payload schema (minimum):
 * - style: one of the keys in renderMap (e.g., "verse", "lyrics", ...)
 * - headline / caption / other fields: consumed by each renderer
 */
connectWebSocket(raw => {
    let data;

    // Parse the incoming message as JSON.
    // If parsing fails, ignore the message and keep the current screen.
    try {
        data = JSON.parse(raw);
    } catch {
        console.error("[!] JSON parse failed");
        return;
    }

    // Pick a renderer based on slide style.
    // Fallback: renderBlank() for unknown/unsupported styles.
    const fn = renderMap[data.style] || renderBlank;
    if (fn) fn(data);
});