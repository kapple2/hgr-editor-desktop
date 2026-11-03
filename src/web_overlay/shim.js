/*
 * HGRTool Desktop shim. Loaded before the editor script.
 *
 * 1. Emulates the browser File System Access API (showOpenFilePicker / showSaveFilePicker) on
 *    top of the Python bridge, so the editor's own open/save code runs unchanged but uses
 *    native dialogs and writes real files.
 * 2. Provides window.__hgrStore, a synchronous settings object (replaces localStorage) that is
 *    pre-filled from /settings.js and written back through the bridge.
 * 3. Draws the large "current color" indicator in the palette panel.
 */
(function () {
    "use strict";

    // ---- bridge readiness -------------------------------------------------------------
    const ready = new Promise((resolve) => {
        if (window.pywebview && window.pywebview.api) {
            resolve();
        } else {
            window.addEventListener("pywebviewready", () => resolve(), { once: true });
        }
    });
    const api = () => window.pywebview.api;

    // ---- base64 helpers ---------------------------------------------------------------
    function b64ToBytes(b64) {
        const bin = atob(b64);
        const out = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
        return out;
    }
    function bytesToB64(bytes) {
        let bin = "";
        const CHUNK = 0x8000;
        for (let i = 0; i < bytes.length; i += CHUNK) {
            bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
        }
        return btoa(bin);
    }
    async function toBytes(data) {
        if (data && data.type === "write" && "data" in data) data = data.data;   // WriteParams
        if (data instanceof Uint8Array) return data;
        if (data instanceof ArrayBuffer) return new Uint8Array(data);
        if (ArrayBuffer.isView(data)) return new Uint8Array(data.buffer, data.byteOffset, data.byteLength);
        if (data instanceof Blob) return new Uint8Array(await data.arrayBuffer());
        if (typeof data === "string") return new TextEncoder().encode(data);
        throw new TypeError("unsupported data type for write()");
    }

    // ---- FileSystemFileHandle emulation -----------------------------------------------
    class DesktopFileHandle {
        constructor(path, name, bytes) {
            this.kind = "file";
            this.path = path;
            this.name = name;
            this._bytes = bytes;     // contents at open time (may be undefined for save-as targets)
        }
        async getFile() {
            return new File([this._bytes || new Uint8Array(0)], this.name, { type: "application/octet-stream" });
        }
        async createWritable() {
            const handle = this;
            let chunks = [];
            return {
                async truncate(size) {
                    if (size === 0) chunks = [];
                },
                async write(data) {
                    chunks.push(await toBytes(data));
                },
                async close() {
                    let total = 0;
                    for (const c of chunks) total += c.length;
                    const all = new Uint8Array(total);
                    let off = 0;
                    for (const c of chunks) { all.set(c, off); off += c.length; }
                    await ready;
                    const r = await api().write_file(handle.path, bytesToB64(all));
                    if (!r || !r.ok) {
                        throw new Error((r && r.error) || "write failed");
                    }
                    handle._bytes = all;
                },
            };
        }
    }
    window.__hgrMakeHandle = (path, name, bytes) => new DesktopFileHandle(path, name, bytes);

    window.showOpenFilePicker = async function (/* options */) {
        await ready;
        const files = await api().open_dialog();
        if (!files || files.length === 0) {
            throw new DOMException("The user aborted a request.", "AbortError");
        }
        return files.map((f) => new DesktopFileHandle(f.path, f.name, b64ToBytes(f.data)));
    };

    window.showSaveFilePicker = async function (options) {
        await ready;
        const r = await api().save_dialog((options && options.suggestedName) || "");
        if (!r) {
            throw new DOMException("The user aborted a request.", "AbortError");
        }
        return new DesktopFileHandle(r.path, r.name, undefined);
    };

    // ---- settings store (replaces localStorage) ----------------------------------------
    const initial = window.__hgrInitialSettings || {};
    window.__hgrStore = new Proxy(Object.assign({}, initial), {
        set(target, key, value) {
            target[key] = String(value);
            ready.then(() => api().save_settings(JSON.stringify(target))).catch(() => {});
            return true;
        },
    });

    // ---- current color indicator in the palette panel ----------------------------------
    window.__hgrDrawCurrent = function (pic) {
        const hgr = window.__hgr;
        const canvas = document.getElementById("palette-current");
        if (!hgr || !canvas || !hgr.picker || hgr.picker.currentPat === undefined) return;
        canvas.width = canvas.clientWidth || 176;
        canvas.height = canvas.clientHeight || 40;
        const ctx = canvas.getContext("2d");
        hgr.picker.drawColorSwatch(ctx, hgr.picker.currentPat, pic ? pic.useMono : false);
    };

    // ---- startup: open files given on the command line; no browser context menu -------
    document.addEventListener("contextmenu", (e) => {
        if (!window.__hgrDebug) e.preventDefault();
    });
    // Tell Python whether there are unsaved edits (it asks before closing the window).
    let lastDirty = false;
    setInterval(() => {
        if (!window.__hgr) return;
        const d = !!window.__hgr.isDirty();
        if (d !== lastDirty) {
            lastDirty = d;
            ready.then(() => api().set_dirty(d)).catch(() => {});
        }
    }, 300);

    window.addEventListener("DOMContentLoaded", async () => {
        // Hover hints on the palette swatches.
        document.querySelectorAll("#hgr-color-body .swatch-button").forEach((b, i) => { b.title = "Solid " + i; });
        document.querySelectorAll("#hgr-dither-body .swatch-button").forEach((b, i) => { b.title = "Pattern " + i; });
        await ready;
        try {
            const files = await api().get_startup_files();
            for (const f of files || []) {
                const handle = new DesktopFileHandle(f.path, f.name, b64ToBytes(f.data));
                await window.__hgr.editor.loadFile(await handle.getFile(), handle);
            }
        } catch (e) {
            console.log("startup files failed: " + e);
        }
    });
})();
