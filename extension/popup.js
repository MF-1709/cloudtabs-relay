const API = "http://127.0.0.1:47823/tabs";
const t = (key) => chrome.i18n.getMessage(key);
const list = document.getElementById("list");
const status = document.getElementById("status");
const search = document.getElementById("search");
let data = null;

function favicon(url) {
  const u = new URL(chrome.runtime.getURL("/_favicon/"));
  u.searchParams.set("pageUrl", url);
  u.searchParams.set("size", "32");
  return u.toString();
}

function host(url) {
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return url; }
}

function open(url, background) {
  chrome.tabs.create({ url, active: !background });
}

function el(tag, props = {}, children = []) {
  const node = Object.assign(document.createElement(tag), props);
  node.append(...children);
  return node;
}

function message(text, code) {
  list.replaceChildren(el("div", { className: "empty" }, [text, ...(code ? [el("code", { textContent: code })] : [])]));
}

function render() {
  if (!data) return;
  if (data.error === "down") return message(t("errDown"));
  if (data.error === "permission")
    return message(t("errPermission"), data.binary);
  if (data.error) return message(data.message || t("errRead"));

  const q = search.value.trim().toLowerCase();
  const frag = document.createDocumentFragment();
  let shown = 0;

  for (const device of data.devices) {
    const tabs = device.tabs.filter(
      (tab) => !q || tab.title.toLowerCase().includes(q) || tab.url.toLowerCase().includes(q)
    );
    if (!tabs.length) continue;
    shown += tabs.length;

    const all = el("button", { textContent: `${t("openAll")} (${tabs.length})` });
    all.onclick = () => tabs.forEach((tab) => open(tab.url, true));
    frag.append(el("div", { className: "device" }, [el("h2", { textContent: device.name }), all]));

    for (const tab of tabs) {
      const row = el("div", { className: "tab", title: tab.url }, [
        el("img", { src: favicon(tab.url), alt: "" }),
        el("div", { className: "txt" }, [
          el("div", { className: "title", textContent: tab.title }),
          el("div", { className: "host", textContent: host(tab.url) }),
        ]),
      ]);
      // Click = open and switch to it; Cmd+click = open in background.
      row.onclick = (e) => open(tab.url, e.metaKey || e.ctrlKey);
      frag.append(row);
    }
  }

  if (!shown) return message(q ? t("noMatch") : t("noTabs"));
  list.replaceChildren(frag);
  status.textContent = t("footer");
}

async function refresh() {
  try {
    const res = await fetch(API, { cache: "no-store" });
    data = await res.json();
  } catch {
    data = { error: "down" };
  }
  render();
  chrome.runtime.sendMessage("refresh").catch(() => {}); // also refreshes the badge
}

search.placeholder = t("searchPlaceholder");
search.addEventListener("input", render);
search.addEventListener("keydown", (e) => {
  if (e.key === "Enter") list.querySelector(".tab")?.click();
});

// Show cached data instantly, then refresh every 3 s while the popup is open.
chrome.storage.local.get("last").then(({ last }) => {
  if (last && !data) { data = last; render(); }
});
refresh();
setInterval(refresh, 3000);
