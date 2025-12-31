// js/autoshrink_hall.js

/**
 * Automatically reduces the font size of an element until its content
 * fits within the element's visible width and height.
 *
 * This function is typically used for hall overlays where text length
 * varies but must never overflow the background container.
 *
 * @param {HTMLElement} el
 *        Target element whose font size will be adjusted
 * @param {number} maxFont
 *        Initial (maximum) font size in pixels
 * @param {number} minFont
 *        Lower bound for font size in pixels
 */
function autoShrinkFont(el, maxFont = 80, minFont = 16) {
    // Allow content to expand naturally while measuring overflow
    el.style.overflow = "visible";

    // Start from the maximum font size
    let font = maxFont;
    el.style.fontSize = font + "px";

    // Gradually decrease font size until content fits
    while (
        font > minFont &&
        (el.scrollWidth > el.offsetWidth || el.scrollHeight > el.offsetHeight)
    ) {
        font--;
        el.style.fontSize = font + "px";
    }
}