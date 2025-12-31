// js/autoshrink_obs.js

/**
 * Automatically reduces the font size of an element so that its content
 * fits within the visible bounding box.
 *
 * This OBS-specific version is tuned for smaller caption areas compared
 * to the hall display, with a lower default maximum font size.
 *
 * @param {HTMLElement} el
 *        Target DOM element whose font size will be adjusted
 * @param {number} maxFont
 *        Starting (maximum) font size in pixels
 * @param {number} minFont
 *        Minimum allowed font size in pixels
 */
function autoShrinkFont(el, maxFont = 48, minFont = 16) {
    // Preserve the original overflow setting (for safety / future extension)
    const originalOverflow = el.style.overflow;

    // Temporarily allow overflow so we can accurately measure content size
    el.style.overflow = "visible";

    // Start shrinking from the maximum font size
    let font = maxFont;
    el.style.fontSize = font + "px";

    // Reduce font size only while content overflows the element
    while (
        font > minFont &&
        (el.scrollWidth > el.offsetWidth || el.scrollHeight > el.offsetHeight)
    ) {
        font--;
        el.style.fontSize = font + "px";
    }

    // Note:
    // The original overflow value is intentionally not restored here,
    // as OBS overlays rely on CSS to control final clipping behavior.
}