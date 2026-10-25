# Diagram sources

The `.svg` files here are the editable source. They were written by hand as plain SVG, so any of these can edit them:

- **Figma**: drag the `.svg` onto a canvas. Text stays editable.
- **Inkscape or Illustrator**: open the file directly.
- **A text editor**: every label is a `<text>` element, and every colour is set in the `<style>` block at the top.

## Fonts

Labels use Be Vietnam Pro and JetBrains Mono (Google Fonts, open licence). Install both before editing in a design tool, or text falls back to a system font.

## Colours

Each colour is written as `var(--dg-name, fallback)`. Opened on its own, a diagram uses the fallback, which is the Task Board dark theme. Inlined in the guide, it picks up the page's theme, so it also works in the light theme.

## Exporting PNGs

`node tools/render.js` from the repository root exports each SVG to a 2x PNG with the brand fonts loaded, and reprints `guide.pdf`.

## Dated facts

Each diagram carries a "LAST VERIFIED" line, as the brand kit asks for graphics with facts that can expire. Update it with `tools/data.json` when the guide is re-checked.
