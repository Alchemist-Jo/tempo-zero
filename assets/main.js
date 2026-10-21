// Program-video player: the timeline shows the execution intervals of the demo's
// criteria, and the ground-truth option lights up after the deciding event.
const video = document.getElementById("demo-video");
const timeline = document.getElementById("demo-timeline");
const options = document.getElementById("demo-options");
const gallery = document.getElementById("demo-gallery");
const MAX_ROWS = 5;
let demo = null, rows = [], revealAt = 0;

const label = (task) => task.replace(/_/g, " ");

function show(index) {
  demo = DEMOS[index];
  video.src = `assets/demos/${demo.family}.mp4`;
  video.play().catch(() => {});
  document.getElementById("demo-family").textContent = demo.name;
  document.getElementById("demo-task").textContent = label(demo.task);
  document.getElementById("demo-length").textContent = `${demo.duration.toFixed(1)} s`;
  document.getElementById("demo-stem").textContent = demo.stem;
  options.innerHTML = demo.options.map((o) => `<li>${o}</li>`).join("");
  revealAt = Math.max(...demo.asked[0].intervals.map((i) => i[1]));

  // Row 1: intervals of the deciding events; then the events the answer rests on.
  const [target, ...deps] = demo.asked;
  deps.sort((a, b) => a.intervals[0][0] - b.intervals[0][0]);
  const items = [{ ...target, target: true, name: `question &middot; ${label(target.task)}` },
                 ...deps.map((c) => ({ ...c, name: c.value }))].slice(0, MAX_ROWS);
  timeline.innerHTML = items.map((c) => `
    <div class="tl-row${c.target ? " target" : ""}">
      <div class="tl-label" title="${c.target ? demo.stem : c.value}">${c.name}</div>
      <div class="tl-track">${c.intervals.map(([a, b]) =>
        `<div class="tl-band" style="left:${100 * a / demo.duration}%;width:${Math.max(0.6, 100 * (b - a) / demo.duration)}%"></div>`).join("")}</div>
    </div>`).join("") + `<div class="tl-head"><span class="tl-time"></span></div>`;
  rows = [...timeline.querySelectorAll(".tl-row")].map((el, i) => ({ el, intervals: items[i].intervals }));
  [...gallery.children].forEach((card, i) => card.classList.toggle("active", i === index));
}

function tick() {
  if (demo && video.duration) {
    const t = video.currentTime;
    const track = timeline.querySelector(".tl-track");
    const head = timeline.querySelector(".tl-head");
    if (track && head) {
      const box = track.getBoundingClientRect(), base = timeline.getBoundingClientRect();
      head.style.left = `${box.left - base.left + box.width * Math.min(t / demo.duration, 1)}px`;
      head.firstChild.textContent = `${t.toFixed(1)} s`;
    }
    rows.forEach((r) => r.el.classList.toggle("on", r.intervals.some(([a, b]) => t >= a && t <= b)));
    options.children[demo.answer]?.classList.toggle("gt", t >= revealAt);
  }
  requestAnimationFrame(tick);
}

timeline.addEventListener("click", (e) => {
  const track = timeline.querySelector(".tl-track");
  if (!track) return;
  const box = track.getBoundingClientRect();
  video.currentTime = Math.max(0, Math.min(1, (e.clientX - box.left) / box.width)) * demo.duration;
});

gallery.innerHTML = DEMOS.map((d) => `
  <button class="card"><video src="assets/demos/${d.family}.mp4" poster="assets/demos/${d.family}.jpg" muted loop playsinline preload="none"></video><span>${d.name}</span></button>`).join("");
[...gallery.children].forEach((card, i) => {
  const clip = card.querySelector("video");
  card.addEventListener("mouseenter", () => clip.play().catch(() => {}));
  card.addEventListener("mouseleave", () => clip.pause());
  card.addEventListener("click", () => show(i));
});

show(Math.max(0, DEMOS.findIndex((d) => d.family === "shell_game")));
requestAnimationFrame(tick);
