// Gigantic Journeys mockups (M0-DSGN-01): query-parameter switches shared by every screen.
//   bg=bright|dark|table   stand-in scan behind the UI (also picks the auto scrim)
//   img=URL                a real scan frame behind the UI (use with the matching bg= for the scrim pick)
//   scrim=auto|charcoal|cream   auto = charcoal over bright scans, cream over dark (DESIGN_SYSTEM §2)
//   surface=glass|flat     flat = the Reduce Transparency twin (§10)
//   hc=1                   Increase Contrast (§10: scrims to 90 %, thicker outlines)
//   cvd=deuteranopia|protanopia|tritanopia   simulation (Machado et al. 2009, severity 1.0, linear RGB)
//   annot=1                touch targets, safe areas, HUD band (AT-4)
//   ui=0                   hide the UI
//   hidescrim=1            hide every scrim and its contents (what lies under each scrim, for contrast measurement)
//   state=...              screen-specific state
(function () {
  const q = new URLSearchParams(location.search);
  const bg = q.get("bg") || "bright";
  const autoScrim = bg === "dark" ? "cream" : "charcoal";
  const scrim = q.get("scrim") && q.get("scrim") !== "auto" ? q.get("scrim") : autoScrim;
  const state = q.get("state") || document.body.dataset.defaultState || "default";
  const body = document.body;
  const SPRITE = `<svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;width:0;height:0"><defs>
<symbol id="i-pause" viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor"/><rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor"/></symbol>
<symbol id="i-sparkle" viewBox="0 0 24 24"><path d="M12 2 13.8 10.2 22 12 13.8 13.8 12 22 10.2 13.8 2 12 10.2 10.2Z" fill="currentColor"/></symbol>
<symbol id="i-sparkle-o" viewBox="0 0 24 24"><path d="M12 3.5 13.5 10.5 20.5 12 13.5 13.5 12 20.5 10.5 13.5 3.5 12 10.5 10.5Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></symbol>
<symbol id="i-jump" viewBox="0 0 24 24"><path d="M5 16 12 8.5 19 16" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-vault" viewBox="0 0 24 24"><path d="M3 19h18" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M5 15C7 6 16 5 19 13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M15.5 12.5 19.2 13.4 20 9.6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-flag" viewBox="0 0 24 24"><path d="M6 21V3M6 4h12l-3.5 4.5L18 13H6" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-share" viewBox="0 0 24 24"><path d="M12 15V3M7 8l5-5 5 5M5 12v8h14v-8" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-close" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></symbol>
<symbol id="i-check" viewBox="0 0 24 24"><path d="M4 12.5 9.5 18 20 6.5" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-chev" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-alert" viewBox="0 0 24 24"><path d="M12 3 22 20H2Z" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"/><path d="M12 10v4.5M12 17.2v.3" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></symbol>
<symbol id="i-lamp" viewBox="0 0 24 24"><path d="M8 3h8l3 8H5ZM12 11v8M8 21h8" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/></symbol>
<symbol id="i-hand" viewBox="0 0 24 24"><path d="M8 13V5.5a1.5 1.5 0 0 1 3 0V12M11 11V4a1.5 1.5 0 0 1 3 0v7M14 11V5.5a1.5 1.5 0 0 1 3 0V14c0 4-2.5 7-6 7-2.5 0-4-1.3-5.5-3.5L3.8 15a1.5 1.5 0 0 1 2.5-1.6L8 15.5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-assist" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M8 12.5l3 3 5-6" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
</defs></svg>`;
  document.body.insertAdjacentHTML("afterbegin", SPRITE);
  body.classList.add(q.get("surface") === "flat" ? "flat" : "glass");
  if (q.get("hc") === "1") body.classList.add("hc");
  if (q.get("annot") === "1") body.classList.add("annot-on");
  if (q.get("ui") === "0") body.classList.add("ui-off");
  if (q.get("hidescrim") === "1") body.classList.add("hidescrim");
  const device = document.querySelector(".device");
  device.classList.add("bg-" + bg);
  // img=<url or path>: put a real scan render behind the UI instead of the CSS stand-in (AT-2 on the real scans)
  const img = q.get("img");
  if (img) {
    document.querySelectorAll(".scene").forEach((sc) => {
      sc.style.background = `center / cover no-repeat url("${img}")`;
      [...sc.children].forEach((c) => (c.style.display = c.matches(".beam, .avatar, .steps") ? "" : "none"));
    });
  }
  document.querySelectorAll(".scrim.auto").forEach((el) => el.classList.add(scrim));
  document.querySelectorAll("[data-state]").forEach((el) => {
    if (!el.dataset.state.split(" ").includes(state)) el.style.display = "none";
  });
  document.querySelectorAll("[data-state-not]").forEach((el) => {
    if (el.dataset.stateNot.split(" ").includes(state)) el.style.display = "none";
  });
  window.GJ = { bg, scrim, state, q };
  if (typeof window.screenSetup === "function") window.screenSetup(window.GJ);

  const M = {
    deuteranopia: "0.367322 0.860646 -0.227968 0 0 0.280085 0.672501 0.047413 0 0 -0.011820 0.042940 0.968881 0 0 0 0 0 1 0",
    protanopia: "0.152286 1.052583 -0.204868 0 0 0.114503 0.786281 0.099216 0 0 -0.003882 -0.048116 1.051998 0 0 0 0 0 1 0",
    tritanopia: "1.255528 -0.076749 -0.178779 0 0 -0.078411 0.930809 0.147602 0 0 0.004733 0.691367 0.303900 0 0 0 0 0 1 0",
  };
  const cvd = q.get("cvd");
  if (M[cvd]) {
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("width", "0");
    svg.setAttribute("height", "0");
    svg.style.position = "absolute";
    svg.innerHTML = `<filter id="cvd" color-interpolation-filters="linearRGB"><feColorMatrix type="matrix" values="${M[cvd]}"/></filter>`;
    body.appendChild(svg);
    device.style.filter = "url(#cvd)";
  }

  // Annotation layer: touch targets from [data-target] (value = minimum pt: 44 or 56), plus safe areas.
  const annot = document.createElement("div");
  annot.className = "annot";
  device.appendChild(annot);
  const d = device.getBoundingClientRect();
  const targets = [];
  document.querySelectorAll("[data-target]").forEach((el) => {
    if (!el.offsetParent && el.style.position !== "fixed") return;
    const r = el.getBoundingClientRect();
    if (r.width === 0) return;
    const hit = el.dataset.hit ? parseFloat(el.dataset.hit) : 0;
    const w = Math.max(r.width, hit), h = Math.max(r.height, hit);
    const x = r.left - d.left - (w - r.width) / 2, y = r.top - d.top - (h - r.height) / 2;
    const min = parseFloat(el.dataset.target);
    const ok = Math.min(w, h) >= min - 0.01;
    const box = document.createElement("div");
    box.className = "a-target" + (y + h > d.height - 20 ? " up" : "");
    Object.assign(box.style, { left: x + "px", top: y + "px", width: w + "px", height: h + "px" });
    if (!ok) box.style.borderColor = "#ff0000";
    box.innerHTML = `<span>${el.dataset.name || ""} ${Math.round(w)}×${Math.round(h)} pt${ok ? "" : " < " + min}</span>`;
    annot.appendChild(box);
    targets.push({ name: el.dataset.name || el.className, w: Math.round(w), h: Math.round(h), min, ok });
  });
  const add = (cls, style, html) => {
    const e = document.createElement("div");
    e.className = cls;
    Object.assign(e.style, style);
    if (html) e.innerHTML = html;
    annot.appendChild(e);
  };
  const insets = JSON.parse(device.dataset.safe || "[0,0,0,0]"); // top right bottom left
  const [t, rr, b, l] = insets;
  add("a-safe", { left: l + "px", top: t + "px", right: rr + "px", bottom: b + "px" });
  add("a-label", { left: l + 4 + "px", bottom: b + 4 + "px" }, `safe area ${t}/${rr}/${b}/${l} pt`);
  if (device.classList.contains("landscape") && device.dataset.hud === "1") {
    const band = d.height * 0.08;
    add("a-band", { top: 0, height: band + "px" });
    add("a-label cyan", { left: "40%", top: band + 2 + "px" }, `HUD band: top 8 % = ${band.toFixed(1)} pt`);
    add("a-safe", { left: "64px", top: "16px", right: rr + 16 + "px", bottom: b + 16 + "px", borderColor: "#00ff88" });
    add("a-label", { left: "68px", top: "36%", background: "#00ff88" }, "controls inset 16 pt from island and corners");
  }
  if (device.classList.contains("duo")) {
    add("a-band", { top: "340px", height: "40px", borderTop: "1.5px solid #00e5ff" });
    add("a-label cyan", { left: "24px", top: "344px" }, "fold division (reserved region, ~40 pt, assumed)");
  }

  // Contrast-measurement export: every [data-m] element with its foreground and nearest painted ancestor.
  const parse = (c) => (c.match(/[\d.]+/g) || []).map(Number);
  const out = [];
  document.querySelectorAll("[data-m]").forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || getComputedStyle(el).visibility === "hidden") return;
    const fg = parse(getComputedStyle(el).color);
    // data-m-bg: measure against a named ancestor (e.g. a progress fill against its scrim, not its track)
    let p = el.dataset.mBg ? el.closest(el.dataset.mBg) : el, bgc = null, glass = false, surface = "";
    while (p && p !== device) {
      const cs = getComputedStyle(p);
      const c = parse(cs.backgroundColor);
      if (c.length === 4 ? c[3] > 0 : c.length === 3) {
        bgc = c.length === 3 ? [...c, 1] : c;
        glass = (cs.backdropFilter || cs.webkitBackdropFilter || "none") !== "none";
        surface = p.className;
        break;
      }
      p = p.parentElement;
    }
    out.push({
      id: el.dataset.mid || el.textContent.trim().slice(0, 32),
      kind: el.dataset.m,
      fgToken: el.dataset.token || "",
      fg,
      bg: bgc,
      glass,
      surface,
      rect: [r.left - d.left, r.top - d.top, r.width, r.height].map((v) => Math.round(v * 10) / 10),
    });
  });
  const pre = document.createElement("pre");
  pre.id = "gj-measure";
  pre.style.display = "none";
  pre.textContent = JSON.stringify({ bg, scrim, state, surface: body.classList.contains("flat") ? "flat" : "glass", items: out, targets });
  body.appendChild(pre);
})();
