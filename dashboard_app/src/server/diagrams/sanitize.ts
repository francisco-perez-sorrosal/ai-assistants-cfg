import "server-only";

import sanitizeHtml from "sanitize-html";

// Only inline-injected SVGs need sanitization (dangerouslySetInnerHTML / interactive viewer).
// SVGs served via <img src="/api/diagram?path=..."> are opaque to the page —
// an <img>-sourced SVG cannot execute script even when it contains <script> elements,
// so those bytes are served as-is without sanitization.

// sanitize-html / htmlparser2 lowercases all tag names AND all attribute names
// before matching. SVG camelCase element names (clipPath, linearGradient,
// feDropShadow, etc.) and camelCase attribute names (viewBox, preserveAspectRatio,
// gradientTransform, markerWidth, refX, stdDeviation, etc.) must therefore be
// registered in their lowercase form in BOTH SVG_ALLOWED_TAGS and
// SVG_ALLOWED_ATTRIBUTES, or they are silently stripped. (Registering only the
// camelCase form leaves the diagram without its viewBox → it renders at intrinsic
// size with no fit-to-container — the original "diagrams render badly" defect.)
// The sanitized output carries lowercased tag/attribute names; when that markup is
// later injected via dangerouslySetInnerHTML, the HTML5 parser's foreign-content
// attribute-adjustment step restores the canonical SVG casing (viewbox → viewBox),
// so rendering is unaffected.
const SVG_ALLOWED_TAGS = [
  "svg",
  "g",
  "path",
  "rect",
  "circle",
  "ellipse",
  "line",
  "polyline",
  "polygon",
  "text",
  "tspan",
  "defs",
  "marker",
  "use",
  "symbol",
  "title",
  "desc",
  "style",
  "clippath",          // SVG: clipPath
  "mask",
  "pattern",
  "lineargradient",    // SVG: linearGradient
  "radialgradient",    // SVG: radialGradient
  "stop",
  "a",
  "image",
  "filter",
  "feblend",           // SVG: feBlend
  "fecolormatrix",     // SVG: feColorMatrix
  "fecomponenttransfer", // SVG: feComponentTransfer
  "fecomposite",       // SVG: feComposite
  "feconvolvematrix",  // SVG: feConvolveMatrix
  "fediffuselighting", // SVG: feDiffuseLighting
  "fedisplacementmap", // SVG: feDisplacementMap
  "fedropshadow",      // SVG: feDropShadow
  "feflood",           // SVG: feFlood
  "fefunca",           // SVG: feFuncA
  "fefuncb",           // SVG: feFuncB
  "fefuncg",           // SVG: feFuncG
  "fefuncr",           // SVG: feFuncR
  "fegaussianblur",    // SVG: feGaussianBlur
  "feimage",           // SVG: feImage
  "femerge",           // SVG: feMerge
  "femergenode",       // SVG: feMergeNode
  "femorphology",      // SVG: feMorphology
  "feoffset",          // SVG: feOffset
  "fespecularlighting", // SVG: feSpecularLighting
  "fetile",            // SVG: feTile
  "feturbulence",      // SVG: feTurbulence
  // <foreignObject> is included because Mermaid uses it exclusively to embed node
  // labels as HTML <div> elements. Without it, every Mermaid node renders as an
  // empty yellow box. The contents of foreignObject are sanitized by the same
  // sanitize-html pass — <script>, on* handlers, <iframe>, <object>, <embed>,
  // and javascript: hrefs are stripped just as they are outside foreignObject.
  // The risk profile is therefore equivalent to any other HTML in an allow-listed
  // SVG: CSS-injection via <style> is already accepted (allowVulnerableTags: true)
  // and script-execution vectors are covered by the existing exclusions.
  "foreignobject",      // SVG: foreignObject (htmlparser2 lowercases)
  // HTML tags Mermaid embeds inside foreignObject label divs:
  "div",
  "span",
  "p",
  "br",
  "b",
  "strong",
  "i",
  "em",
  "u",
  "s",
  "code",
  "pre",
  "a",
  "ul",
  "ol",
  "li",
  "table",
  "thead",
  "tbody",
  "tr",
  "td",
  "th",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "sub",
  "sup",
  "hr",
  "blockquote",
  "font",
  "small",
  "label",
  // Intentionally excluded from foreignObject contents: <script>, <iframe>,
  // <object>, <embed>, <form>, <input> — these can execute or exfiltrate.
  "animate",
  "animatetransform",  // SVG: animateTransform
  "mpath",
  "set"
];

// NOTE: all attribute names below are LOWERCASE — htmlparser2 lowercases attribute
// names before matching (see the block comment above SVG_ALLOWED_TAGS). A camelCase
// entry here matches nothing and the attribute is silently dropped.
const SVG_ALLOWED_ATTRIBUTES: sanitizeHtml.IOptions["allowedAttributes"] = {
  "*": [
    // Identity and presentation
    "id",
    "class",
    "style",
    // Geometry
    "d",
    "points",
    "x",
    "y",
    "x1",
    "y1",
    "x2",
    "y2",
    "cx",
    "cy",
    "r",
    "rx",
    "ry",
    "width",
    "height",
    "viewbox",            // SVG: viewBox
    "preserveaspectratio", // SVG: preserveAspectRatio
    "transform",
    // Data attributes the diagram-normalization step adds to the root <svg>
    "data-aspect",
    "data-vb-w",
    "data-vb-h",
    // Fill and stroke
    "fill",
    "fill-opacity",
    "fill-rule",
    "stroke",
    "stroke-width",
    "stroke-dasharray",
    "stroke-dashoffset",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-miterlimit",
    "stroke-opacity",
    "opacity",
    "visibility",
    "display",
    "clip-path",
    "clip-rule",
    "color",
    "color-interpolation",
    "color-interpolation-filters",
    // Text
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "font-variant",
    "text-anchor",
    "dominant-baseline",
    "dx",
    "dy",
    "rotate",
    "letter-spacing",
    "word-spacing",
    "text-decoration",
    // Markers
    "marker-start",
    "marker-mid",
    "marker-end",
    "markerwidth",        // SVG: markerWidth
    "markerheight",       // SVG: markerHeight
    "markerunits",        // SVG: markerUnits
    "orient",
    "refx",               // SVG: refX
    "refy",               // SVG: refY
    // Gradients and stops
    "offset",
    "stop-color",
    "stop-opacity",
    "gradientunits",      // SVG: gradientUnits
    "gradienttransform",  // SVG: gradientTransform
    "patternunits",       // SVG: patternUnits
    "patterntransform",   // SVG: patternTransform
    "patterncontentunits", // SVG: patternContentUnits
    "spreadmethod",       // SVG: spreadMethod
    "fx",
    "fy",
    // Filters
    "filter",
    "filterunits",        // SVG: filterUnits
    "primitiveunits",     // SVG: primitiveUnits
    "result",
    "in",
    "in2",
    "stddeviation",       // SVG: stdDeviation
    "flood-color",
    "flood-opacity",
    "mode",
    "type",
    "values",
    "k1",
    "k2",
    "k3",
    "k4",
    "operator",
    "order",
    "divisor",
    "bias",
    "kernelmatrix",       // SVG: kernelMatrix
    "basefrequency",      // SVG: baseFrequency
    "numoctaves",         // SVG: numOctaves
    "seed",
    "stitchtiles",        // SVG: stitchTiles
    "fractalNoise",
    // Masks and clips
    "maskunits",          // SVG: maskUnits
    "maskcontentunits",   // SVG: maskContentUnits
    // Definitions and linking
    "href",
    "xlink:href",
    "xmlns",
    "xmlns:xlink",
    "version",
    // Use element
    "xlink:type",
    // Accessibility
    "role",
    "aria-label",
    "aria-labelledby",
    "aria-roledescription",
    // Data attributes used by Mermaid for edge metadata
    "data-edge",
    "data-et",
    "data-id",
    "data-look",
    "data-points",
    // foreignObject HTML content attributes.
    // Mermaid wraps labels in <div xmlns="http://www.w3.org/1999/xhtml" class="nodeLabel">.
    // The xmlns attribute is required for valid foreignObject embedding; class/style/id
    // are already present above and apply here too.
    // Table layout attributes used by some diagram generators:
    "align",
    "valign",
    "bgcolor",
    "colspan",
    "rowspan",
    "cellpadding",
    "cellspacing",
    "border",
    "nowrap",
    "dir",
    "lang",
    "title",
    // Animation (SMIL — non-scriptable)
    "attributename",      // SVG: attributeName
    "attributetype",      // SVG: attributeType
    "begin",
    "dur",
    "end",
    "from",
    "to",
    "by",
    "repeatcount",        // SVG: repeatCount
    "repeatdur",          // SVG: repeatDur
    "calcmode",           // SVG: calcMode
    "keytimes",           // SVG: keyTimes
    "keysplines",         // SVG: keySplines
    "additive",
    "accumulate"
  ]
};

export function sanitizeSvg(raw: string): string {
  return sanitizeHtml(raw, {
    allowedTags: SVG_ALLOWED_TAGS,
    allowedAttributes: SVG_ALLOWED_ATTRIBUTES,
    // Restrict href/xlink:href to safe schemes only — block javascript: URIs
    allowedSchemesByTag: {
      a: ["http", "https"],
      image: ["http", "https", "data"]
    },
    disallowedTagsMode: "discard",
    // <style> is in the allowlist because LikeC4 / D2 / Mermaid embed their styling
    // there. sanitize-html warns on every call that <style> is "vulnerable", flooding
    // the dashboard server log. The real XSS vectors (<script>, on* handlers, javascript:
    // URIs) are already stripped above, and the SVGs come from the project's own
    // diagrams/ (trusted generators), so the CSS-injection risk a bare <style> carries
    // is acceptable here. Acknowledge it explicitly to silence the warning rather than
    // dropping <style> (which would break diagram styling).
    allowVulnerableTags: true,
    // Do not strip style= attribute values — they are in the allowlist above and
    // carry visual-only CSS; parsing them as security surface is unnecessary overhead.
    parseStyleAttributes: false
  });
}
