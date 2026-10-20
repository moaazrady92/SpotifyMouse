// ==UserScript==
// @name         SpotifyMouse: YouTube Music volume
// @namespace    https://github.com/moaazrady92/SpotifyMouse
// @version      1.0
// @description  Lets SpotifyMouse move YouTube Music's own volume slider when you scroll while holding a side mouse button.
// @match        https://music.youtube.com/*
// @grant        GM_xmlhttpRequest
// @grant        unsafeWindow
// @connect      127.0.0.1
// @inject-into  auto
// @run-at       document-idle
// @noframes
// @downloadURL  https://raw.githubusercontent.com/moaazrady92/SpotifyMouse/master/ytmusic/spotify-mouse-ytmusic.user.js
// @updateURL    https://raw.githubusercontent.com/moaazrady92/SpotifyMouse/master/ytmusic/spotify-mouse-ytmusic.user.js
// ==/UserScript==

(function () {
  'use strict';

  // SpotifyMouse's local server; it only listens on this PC
  const SERVER = 'http://127.0.0.1:47821';

  // The slider's value is a property of YouTube Music's own code, so reach
  // it through the page's window, not the userscript sandbox
  const page = typeof unsafeWindow !== 'undefined' ? unsafeWindow : window;

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  function send(method, path, body) {
    return new Promise((resolve) => {
      GM_xmlhttpRequest({
        method,
        url: SERVER + path,
        headers: { 'X-SpotifyMouse': '1', 'Content-Type': 'application/json' },
        data: body ? JSON.stringify(body) : undefined,
        timeout: 30000,
        onload: (response) => resolve(response.status === 200 ? response.responseText : null),
        onerror: () => resolve(null),
        ontimeout: () => resolve(null),
      });
    });
  }

  function isPlaying() {
    const video = document.querySelector('video');
    return !!video && !video.paused;
  }

  // Move the slider the same way dragging it does: YouTube Music then
  // applies the volume, unmutes, and remembers the level
  function changeVolume(step) {
    const slider = page.document.querySelector('ytmusic-player-bar #volume-slider');
    if (!slider) return null;

    const level = Math.max(0, Math.min(100, Math.round(Number(slider.value) + step)));
    slider.value = level;
    slider.dispatchEvent(new CustomEvent('change', { bubbles: true, composed: true }));
    return level;
  }

  async function listen() {
    for (;;) {
      const text = await send('GET', '/ytmusic/next?playing=' + (isPlaying() ? 1 : 0));

      if (text === null) {
        await sleep(5000); // SpotifyMouse isn't running; try again later
        continue;
      }
      if (!text) continue; // no command this round

      const command = JSON.parse(text);
      const level = changeVolume(command.volume);
      send('POST', '/ytmusic/volume', { id: command.id, level });
    }
  }

  // Let SpotifyMouse know right away when playback starts or stops, so
  // it knows whether scrolling should go to YouTube Music
  const reportState = () => send('POST', '/ytmusic/state', { playing: isPlaying() });
  document.addEventListener('play', reportState, true);
  document.addEventListener('pause', reportState, true);

  listen();
})();
