// Refreshes the badge (number of iCloud tabs) and the popup cache in the background.
const API = "http://127.0.0.1:47823/tabs";

async function refresh() {
  try {
    const res = await fetch(API, { cache: "no-store" });
    const data = await res.json();
    await chrome.storage.local.set({ last: data });
    if (data.error) {
      chrome.action.setBadgeText({ text: "!" });
      chrome.action.setBadgeBackgroundColor({ color: "#d93025" });
      return;
    }
    const n = data.devices.reduce((sum, d) => sum + d.tabs.length, 0);
    chrome.action.setBadgeText({ text: n ? String(n) : "" });
    chrome.action.setBadgeBackgroundColor({ color: "#0a84ff" });
  } catch {
    await chrome.storage.local.set({ last: { error: "down" } });
    chrome.action.setBadgeText({ text: "!" });
    chrome.action.setBadgeBackgroundColor({ color: "#d93025" });
  }
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("refresh", { periodInMinutes: 0.5 });
  refresh();
});
chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create("refresh", { periodInMinutes: 0.5 });
  refresh();
});
chrome.alarms.onAlarm.addListener((a) => a.name === "refresh" && refresh());
chrome.runtime.onMessage.addListener((msg) => msg === "refresh" && refresh());
