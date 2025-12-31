// js/lyrics_utils_hall.js

/**
 * Splits raw lyric lines into display-ready segments.
 *
 * Rules:
 * - Empty lines force a segment break.
 * - "(간주)" (instrumental interlude) becomes its own standalone segment.
 * - Normal lyrics are grouped into pairs of lines (2 lines per slide).
 *
 * @param {string[]} lines
 *        Array of raw lyric lines
 * @returns {string[][]}
 *        Array of lyric segments, each segment being an array of lines
 */
function segmentLyrics(lines) {
    const segments = [];
    let buffer = [];

    for (const rawLine of lines) {
        const trimmed = rawLine.trim();

        // Empty line → flush current buffer as a segment
        if (trimmed === "") {
            if (buffer.length) segments.push(buffer.splice(0));
            continue;
        }

        // Instrumental marker → standalone slide
        if (trimmed === "(간주)") {
            if (buffer.length) segments.push(buffer.splice(0));
            segments.push([trimmed]);
            continue;
        }

        // Normal lyric line
        buffer.push(trimmed);

        // Group lyrics into pairs (2 lines per segment)
        if (buffer.length === 2) segments.push(buffer.splice(0));
    }

    // Flush remaining lines, if any
    if (buffer.length) segments.push(buffer);

    return segments;
}

/**
 * Splits a single lyric line into two visually balanced parts.
 *
 * Behavior:
 * - Attempts to split the line into two parts with similar text length.
 * - Preserves "아멘" as a separate trailing line if present.
 *
 * @param {string} line
 *        A single lyric line
 * @returns {string[]}
 *        Array of split lines (1–3 lines depending on content)
 */
function splitBalanced(line) {
    let words = line.trim().split(/\s+/);

    // Detect and temporarily remove trailing "아멘"
    let hasAmen = words.at(-1) === "아멘";
    if (hasAmen) words.pop();

    // Short lines do not need balancing
    if (words.length < 2) {
        return hasAmen ? [words.join(" "), "아멘"] : [words.join(" ")];
    }

    // Find the split point that minimizes length difference
    let best = 1;
    let diff = Infinity;

    for (let i = 1; i < words.length; i++) {
        const d = Math.abs(
            words.slice(0, i).join(" ").length -
            words.slice(i).join(" ").length
        );
        if (d < diff) {
            diff = d;
            best = i;
        }
    }

    // Construct balanced result
    const res = [
        words.slice(0, best).join(" "),
        words.slice(best).join(" ")
    ];

    // Re-attach "아멘" as its own line if it was present
    if (hasAmen) res.push("아멘");

    return res;
}