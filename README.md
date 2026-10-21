# Tempo-Zero project page

Project page of **Tempo-Zero: Recursive Self-Play in Executable Worlds for Video Reasoning**, served by GitHub Pages at <https://alchemist-jo.github.io/tempo-zero/>.

The page is static: `index.html`, `assets/style.css` and `assets/main.js`, with no build step.

## Assets

- `assets/demos/` holds one program video per environment family, with its canonical question and the execution intervals of its criteria in `demos.js`. `scripts/render_demos.py` produces the directory from the Tempo-Zero release code:

  ```bash
  python3 -I scripts/render_demos.py <tempo-zero-source> assets/demos
  ```

  The script renders every simulation tick between the first and the last sampled frame and encodes the ticks on the model clock, so the intervals in `demos.js` match the video time. It needs `ffmpeg` with `libx264`.

- `assets/method/` holds the two method videos.
- The result tables in `index.html` are parsed from the experiments section of the manuscript:

  ```bash
  python3 scripts/build_tables.py <paper>/sections/05-experiments.tex index.html
  ```
