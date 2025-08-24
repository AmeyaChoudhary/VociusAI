export function clearLastResult() {
  [
    "vocius_last_result",
    "vocius_last_result_text",
    "vocius_last_result_blob",
  ].forEach((k) => localStorage.removeItem(k));
}
