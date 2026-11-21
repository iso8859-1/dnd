// DnD Cards — deck builder UI. Talks to the Rust side via Tauri commands.
"use strict";

const invoke = window.__TAURI__.core.invoke;
const $ = (id) => document.getElementById(id);

const ui = {
  name: $("deck-name"), count: $("deck-count"), dirty: $("dirty"),
  search: $("search"), langChips: $("lang-chips"), typeChips: $("type-chips"), onlyDeck: $("only-deck"),
  rows: $("rows"), empty: $("empty"), preview: $("preview"),
  deckList: $("deck-list"), deckEmpty: $("deck-empty"), status: $("status"),
  buttons: ["btn-new", "btn-open", "btn-save", "btn-pdf", "btn-duplex"].map($),
};

const state = {
  cards: [],            // [{key, name, card_type, lang}]
  byKey: new Map(),
  languages: [],
  types: [],
  qty: new Map(),       // key -> quantity (>0); insertion order = deck order
  lang: null,
  type: null,
  search: "",
  onlyDeck: false,
  visible: [],
  sel: 0,
  deckPath: null,
  dirty: false,
  busy: false,
};

const details = new Map(); // key -> Promise<CardData>

// ── Helpers ─────────────────────────────────────────────────────────────────

function el(tag, props = {}, ...children) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v);
  }
  for (const c of children) if (c != null) n.append(c);
  return n;
}

/**
 * Case-insensitive fuzzy rank: 0 = prefix, 1 = word prefix, 2 = substring,
 * 3 = subsequence ("feurball" → "Feuerball"), -1 = no match.
 */
function fuzzyRank(query, text) {
  if (!query) return 0;
  const q = query.toLowerCase();
  const t = text.toLowerCase();
  const at = t.indexOf(q);
  if (at === 0) return 0;
  if (at > 0) return /[\s(\-]/.test(t[at - 1]) ? 1 : 2;
  let i = 0;
  for (const ch of t) if (ch === q[i] && ++i === q.length) return 3;
  return -1;
}

function setStatus(msg, kind = "") {
  ui.status.textContent = msg;
  ui.status.className = kind;
}

function deckEntries() {
  return [...state.qty.entries()].filter(([, q]) => q > 0);
}

function total() {
  let n = 0;
  for (const q of state.qty.values()) n += q;
  return n;
}

function markDirty(d = true) {
  state.dirty = d;
  ui.dirty.hidden = !d;
}

/** Short layout hint for the card list, or null for a plain one-card layout. */
function layoutBadge(card) {
  if (!card) return null;
  if (!card.layout) {
    return el("span", { class: "lbadge bad", text: "not printable", title: card.error || "" });
  }
  const l = card.layout;
  if (l.cards > 1) return el("span", { class: "lbadge", text: `${l.cards} cards`, title: describeLayout(l) });
  if (l.uses_back) return el("span", { class: "lbadge", text: "back", title: describeLayout(l) });
  if (l.font_size < 6) return el("span", { class: "lbadge", text: "small", title: describeLayout(l) });
  return null;
}

function describeLayout(l) {
  const parts = [l.font_size < 6 ? `Text at ${l.font_size}pt` : "Text at 6pt"];
  if (l.uses_back) parts.push("continues on the back");
  if (l.cards > 1) parts.push(`printed on ${l.cards} cards`);
  return parts.join(", ");
}

function printedCount() {
  let n = 0;
  for (const [key, q] of state.qty) n += q * (state.byKey.get(key)?.layout?.cards ?? 1);
  return n;
}

function typeLabel(t) {
  return t.replace(/_/g, " ");
}

// ── Rendering ───────────────────────────────────────────────────────────────

function computeVisible() {
  const ranked = [];
  for (const c of state.cards) {
    if (state.lang && c.lang !== state.lang) continue;
    if (state.type && c.card_type !== state.type) continue;
    if (state.onlyDeck && !state.qty.has(c.key)) continue;
    const rank = fuzzyRank(state.search, c.name);
    if (rank >= 0) ranked.push([rank, c]);
  }
  // Stable sort keeps the key order within each rank.
  ranked.sort((a, b) => a[0] - b[0]);
  state.visible = ranked.map(([, c]) => c);
  state.sel = Math.min(state.sel, Math.max(0, state.visible.length - 1));
}

function stepper(key) {
  const q = state.qty.get(key) || 0;
  const card = state.byKey.get(key);
  const blocked = card && !card.layout;
  return el("div", { class: "stepper" },
    el("button", { text: "−", title: "Remove one", tabindex: "-1", onclick: (e) => { e.stopPropagation(); changeQty(key, -1); } }),
    el("span", { class: "q" + (q ? "" : " zero"), text: String(q) }),
    blocked
      ? el("button", { text: "+", title: "This card can't be printed", tabindex: "-1", disabled: "" })
      : el("button", { text: "+", title: "Add one", tabindex: "-1", onclick: (e) => { e.stopPropagation(); changeQty(key, +1); } }),
  );
}

function renderRows() {
  const frag = document.createDocumentFragment();
  state.visible.forEach((c, i) => {
    const row = el("div", {
      class: "row" + (i === state.sel ? " sel" : "") + (state.qty.has(c.key) ? " in-deck" : ""),
      "data-i": String(i),
      onclick: () => select(i),
      ondblclick: () => changeQty(c.key, +1),
    },
      el("span", { class: "name-cell" }, el("span", { class: "name", text: c.name, title: c.key }), layoutBadge(c)),
      el("span", { class: "type" }, el("span", { class: "dot " + c.card_type }), typeLabel(c.card_type)),
      stepper(c.key),
    );
    frag.append(row);
  });
  ui.rows.replaceChildren(frag);
  ui.empty.hidden = state.visible.length > 0;
  scrollSelIntoView();
}

function updateRow(key) {
  const i = state.visible.findIndex((c) => c.key === key);
  if (i < 0) return;
  const row = ui.rows.children[i];
  row.classList.toggle("in-deck", state.qty.has(key));
  row.replaceChild(stepper(key), row.lastChild);
}

function renderChips() {
  const counts = (prop) => state.cards.reduce((m, c) => m.set(c[prop], (m.get(c[prop]) || 0) + 1), new Map());
  const typeCounts = counts("card_type");

  ui.langChips.replaceChildren(...(state.languages.length > 1 ? state.languages : []).map((l) =>
    el("button", { class: "chip", "aria-pressed": String(state.lang === l), onclick: () => toggleLang(l) }, l.toUpperCase())));

  ui.typeChips.replaceChildren(...state.types.map((t, i) =>
    el("button", {
      class: "chip", "aria-pressed": String(state.type === t),
      title: i < 9 ? `Alt+${i + 1}` : "", onclick: () => toggleType(t),
    }, typeLabel(t), el("span", { class: "n", text: String(typeCounts.get(t) || 0) }))));
}

function renderDeck() {
  const entries = deckEntries();
  const printed = printedCount();
  ui.count.textContent = `${total()} card${total() === 1 ? "" : "s"}` + (printed !== total() ? ` · ${printed} printed` : "");
  ui.deckEmpty.hidden = entries.length > 0;
  ui.deckList.replaceChildren(...entries.map(([key, q]) => {
    const card = state.byKey.get(key);
    return el("li", { class: card ? "" : "missing", title: card ? key : `${key} — not in the card data` },
      el("span", { class: "name", onclick: () => reveal(key) },
        el("span", { class: "dot " + (card ? card.card_type : "") }), card ? card.name : key, layoutBadge(card)),
      stepper(key));
  }));
}

function renderAll() {
  computeVisible();
  renderChips();
  renderRows();
  renderDeck();
  showPreview();
}

function scrollSelIntoView() {
  const row = ui.rows.children[state.sel];
  if (row) row.scrollIntoView({ block: "nearest" });
}

// ── Preview ─────────────────────────────────────────────────────────────────

let previewToken = 0;

async function showPreview(key = state.visible[state.sel]?.key) {
  const token = ++previewToken;
  if (!key) {
    ui.preview.className = "preview-card empty-preview";
    ui.preview.textContent = "Select a card to preview it.";
    return;
  }
  if (!details.has(key)) details.set(key, invoke("card_details", { key }));
  let card;
  try {
    card = await details.get(key);
  } catch (err) {
    if (token !== previewToken) return;
    details.delete(key);
    ui.preview.className = "preview-card";
    ui.preview.replaceChildren(
      el("h3", { text: state.byKey.get(key)?.name || key }),
      el("div", { class: "preview-error", text: `Can't be printed: ${err}` }));
    return;
  }
  if (token !== previewToken) return;

  const body = el("div", { class: "body" });
  if (card.type === "spell") {
    body.append(el("p", { class: "meta", text: `Stufe ${card.level ?? ""} · ${card.school ?? ""}` }));
    const dl = el("dl");
    for (const [label, v] of [["Zeit", card.casting_time], ["Reichweite", card.range], ["Komp.", card.components], ["Dauer", card.duration]]) {
      dl.append(el("dt", { text: label }), el("dd", { text: v ?? "" }));
    }
    body.append(dl);
  } else if (card.type === "class_feature") {
    const line = card.level != null ? `${card.class ?? ""} · Stufe ${card.level}` : (card.class ?? "");
    body.append(el("p", { class: "meta", text: line + (card.subclass ? ` (${card.subclass})` : "") }));
  } else if (card.typ) {
    body.append(el("p", { class: "meta", text: card.typ }));
  }
  body.append(el("p", { class: "desc", text: card.description }));
  if (card.source_book) body.append(el("p", { class: "src", text: card.source_book }));
  const layout = state.byKey.get(key)?.layout;
  if (layout) body.append(el("p", { class: "layout", text: "Print: " + describeLayout(layout) }));

  ui.preview.className = "preview-card " + card.type;
  ui.preview.replaceChildren(el("h3", { text: card.name }), body);
}

// ── Actions ─────────────────────────────────────────────────────────────────

function select(i) {
  if (!state.visible.length) return;
  i = Math.max(0, Math.min(i, state.visible.length - 1));
  ui.rows.children[state.sel]?.classList.remove("sel");
  state.sel = i;
  ui.rows.children[i]?.classList.add("sel");
  scrollSelIntoView();
  showPreview();
}

function changeQty(key, delta) {
  const card = state.byKey.get(key);
  if (delta > 0 && card && !card.layout) {
    setStatus(`${card.name} can't be printed: ${card.error}`, "error");
    return;
  }
  const q = Math.max(0, (state.qty.get(key) || 0) + delta);
  if (q === (state.qty.get(key) || 0)) return;
  if (q === 0) state.qty.delete(key);
  else state.qty.set(key, q);
  markDirty();
  if (state.onlyDeck && q === 0) {
    computeVisible();
    renderRows();
  } else {
    updateRow(key);
  }
  renderDeck();
}

function clearQty(key) {
  if (!state.qty.has(key)) return;
  changeQty(key, -state.qty.get(key));
}

/** Show a deck card in the list, relaxing filters if needed. */
function reveal(key) {
  let i = state.visible.findIndex((c) => c.key === key);
  if (i < 0) {
    const card = state.byKey.get(key);
    if (!card) return showPreview(key);
    state.search = ui.search.value = "";
    state.type = null;
    if (state.lang && state.lang !== card.lang) state.lang = card.lang;
    renderAll();
    i = state.visible.findIndex((c) => c.key === key);
  }
  select(i);
}

function toggleLang(l) {
  state.lang = state.lang === l ? null : l;
  state.sel = 0;
  renderAll();
}

function toggleType(t) {
  state.type = state.type === t ? null : t;
  state.sel = 0;
  renderAll();
}

function confirmDiscard() {
  return !state.dirty || window.confirm("Discard unsaved changes to this deck?");
}

function applyDeck(deck) {
  state.qty = new Map(deck.cards.filter(([, q]) => q > 0));
  state.deckPath = deck.path;
  ui.name.value = deck.name;
  markDirty(false);
  renderAll();
  const missing = deck.cards.filter(([k]) => !state.byKey.has(k)).length;
  if (missing) setStatus(`Opened ${deck.path} — ${missing} card(s) not found in the data store.`, "error");
  else setStatus(`Opened ${deck.path}`, "ok");
}

async function run(label, fn) {
  if (state.busy) return;
  state.busy = true;
  ui.buttons.forEach((b) => (b.disabled = true));
  setStatus(label + "…");
  try {
    await fn();
  } catch (err) {
    setStatus(String(err), "error");
  } finally {
    state.busy = false;
    ui.buttons.forEach((b) => (b.disabled = false));
  }
}

function newDeck() {
  if (!confirmDiscard()) return;
  state.qty = new Map();
  state.deckPath = null;
  ui.name.value = "";
  markDirty(false);
  renderAll();
  setStatus("New deck.");
  ui.name.focus();
}

const openDeck = () => run("Opening", async () => {
  if (!confirmDiscard()) return setStatus("");
  const deck = await invoke("open_deck");
  if (deck) applyDeck(deck);
  else setStatus("");
});

const saveDeck = (saveAs = false) => run("Saving", async () => {
  if (!ui.name.value.trim()) {
    ui.name.focus();
    throw new Error("Please give the deck a name first.");
  }
  const path = await invoke("save_deck", {
    path: state.deckPath, saveAs, name: ui.name.value, cards: deckEntries(),
  });
  if (!path) return setStatus("");
  state.deckPath = path;
  markDirty(false);
  setStatus(`Saved ${total()} cards → ${path}`, "ok");
});

const generate = (duplex) => run(duplex ? "Generating duplex PDF" : "Generating PDF", async () => {
  const path = await invoke("generate_pdf", { name: ui.name.value, cards: deckEntries(), duplex });
  setStatus(path ? `PDF → ${path}` : "", path ? "ok" : "");
});

// ── Events ──────────────────────────────────────────────────────────────────

$("btn-new").addEventListener("click", newDeck);
$("btn-open").addEventListener("click", openDeck);
$("btn-save").addEventListener("click", (e) => saveDeck(e.shiftKey));
$("btn-pdf").addEventListener("click", () => generate(false));
$("btn-duplex").addEventListener("click", () => generate(true));

ui.name.addEventListener("input", () => markDirty());
ui.name.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === "Escape") { e.preventDefault(); ui.search.focus(); }
});

ui.search.addEventListener("input", () => {
  state.search = ui.search.value.trim();
  state.sel = 0;
  computeVisible();
  renderRows();
  showPreview();
});

ui.onlyDeck.addEventListener("change", () => {
  state.onlyDeck = ui.onlyDeck.checked;
  state.sel = 0;
  renderAll();
});

document.addEventListener("keydown", (e) => {
  const ctrl = e.ctrlKey || e.metaKey;
  const k = e.key.toLowerCase();

  if (ctrl) {
    const actions = { o: openDeck, n: newDeck, g: () => generate(false), d: () => generate(true), s: () => saveDeck(e.shiftKey) };
    if (actions[k]) { e.preventDefault(); actions[k](); }
    return;
  }
  if (e.altKey && /^[1-9]$/.test(e.key)) {
    const t = state.types[Number(e.key) - 1];
    if (t) { e.preventDefault(); toggleType(t); }
    return;
  }
  if (e.target === ui.name || e.target === ui.onlyDeck || e.altKey) return;

  const cur = state.visible[state.sel];
  const page = Math.max(1, Math.floor(ui.rows.clientHeight / 34) - 1);
  switch (e.key) {
    case "ArrowDown": e.preventDefault(); select(state.sel + 1); return;
    case "ArrowUp": e.preventDefault(); select(state.sel - 1); return;
    case "PageDown": e.preventDefault(); select(state.sel + page); return;
    case "PageUp": e.preventDefault(); select(state.sel - page); return;
    case "+": case "=": case "Enter":
      e.preventDefault(); if (cur) changeQty(cur.key, +1); return;
    case "-": case "_":
      e.preventDefault(); if (cur) changeQty(cur.key, -1); return;
    case "Delete":
      if (cur && (e.target !== ui.search || !ui.search.value)) { e.preventDefault(); clearQty(cur.key); }
      return;
    case "Escape":
      e.preventDefault();
      if (ui.search.value) { ui.search.value = ""; ui.search.dispatchEvent(new Event("input")); }
      else if (state.type) toggleType(state.type);
      return;
  }
  // Any other printable key goes to the search box.
  if (e.key.length === 1 && e.target !== ui.search) ui.search.focus();
});

// ── Startup ─────────────────────────────────────────────────────────────────

(async () => {
  try {
    const cat = await invoke("catalog");
    state.cards = cat.cards;
    state.byKey = new Map(cat.cards.map((c) => [c.key, c]));
    state.languages = cat.languages;
    state.types = cat.types;
    state.lang = cat.languages[0] ?? null;
    renderAll();
    setStatus(`${cat.cards.length} cards loaded from ${cat.data_dir}`);
    const deck = await invoke("initial_deck");
    if (deck) applyDeck(deck);
  } catch (err) {
    setStatus(String(err), "error");
  }
  ui.search.focus();
})();
