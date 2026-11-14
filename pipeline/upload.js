// In YouTube Studio auf .../videos/upload?d=ud ausführen (Upload-Dialog offen).
// Die drei Platzhalter (URL, TITLE, DESC in Großbuchstaben mit je zwei Unterstrichen) vorher durch JSON-Strings ersetzen.
const URL_ = __URL__, TITLE = __TITLE__, DESC = __DESC__;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const q = (s, root = document) => root.querySelector(s);
const blob = await (await fetch(URL_)).blob();
const file = new File([blob], URL_.split('/').pop(), { type: 'video/mp4' });
let inp; for (let i = 0; i < 20 && !(inp = q('ytcp-uploads-file-picker input[type=file]') || q('input[type=file][name=Filedata]')); i++) await sleep(500);
const dt = new DataTransfer(); dt.items.add(file); inp.files = dt.files; inp.dispatchEvent(new Event('change', { bubbles: true }));
let boxes = []; for (let i = 0; i < 40 && (boxes = [...document.querySelectorAll('ytcp-uploads-dialog #textbox[contenteditable="true"]')]).length < 2; i++) await sleep(500);
await sleep(1500);
function setText(el, txt) { el.focus(); document.execCommand('selectAll'); document.execCommand('delete'); document.execCommand('insertText', false, txt); el.dispatchEvent(new Event('input', { bubbles: true })); }
setText(boxes[0], TITLE); await sleep(300); setText(boxes[1], DESC); await sleep(300);
document.activeElement && document.activeElement.blur();
q('ytcp-uploads-dialog tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').click(); await sleep(500);
for (let i = 0; i < 3; i++) { q('ytcp-uploads-dialog #next-button').click(); await sleep(1500); }
q('ytcp-uploads-dialog tp-yt-paper-radio-button[name="PRIVATE"]').click(); await sleep(800);
// Warten bis Upload fertig, dann speichern (privat!)
for (let i = 0; i < 120; i++) { const s = q('ytcp-uploads-dialog .progress-label')?.innerText || ''; if (!/Wird hochgeladen|Uploading/i.test(s)) break; await sleep(1000); }
q('ytcp-uploads-dialog #done-button').click(); await sleep(4000);
const link = [...document.querySelectorAll('a')].map(a => a.href).find(h => /youtu\.be\/|\/shorts\/|\/video\//.test(h));
({ size: blob.size, title: boxes[0].innerText, link, dialog: q('ytcp-uploads-dialog')?.innerText?.slice(0, 200) })
