$(function () {
  // ==========================
  // New Quote button handler
  // ==========================
  $('#btn-new').on('click', function () {
    const slug = $(this).data('slug');
    if (!slug) return;

    $.getJSON(`/api/quote/${slug}`, function (res) {
      if (res.ok) {
        // Update quote text (may include <br> for two lines)
        $('#quote-text').html(res.quote.content);

        // Build footer: Author — from "Song" — View on Genius
        let footer = res.quote.author || '';

        if (res.quote.song) {
          footer += ` — from “${res.quote.song}”`;
        }

        if (res.quote.url) {
          footer += ` — <a href="${res.quote.url}" target="_blank" rel="noopener">View on Genius</a>`;
        }

        $('#quote-author').html(footer);
      } else {
        alert('Error fetching quote.');
      }
    }).fail(() => alert('Network error.'));
  });

  // ==========================
  // TTS voice selection
  // ==========================
  let preferredVoice = null;

  function pickPreferredVoice() {
    if (!('speechSynthesis' in window)) return;

    const voices = window.speechSynthesis.getVoices();
    if (!voices || !voices.length) return;

    // Each celebrity template can set window.preferredVoiceName, e.g.:
    //  - "Microsoft Zira - English (United States)"  (Taylor Swift)
    //  - "Microsoft David - English (United States)" (Joji, Finneas)
    //  - "Microsoft Mark - English (United States)"  (Travis Scott)
    if (window.preferredVoiceName) {
      preferredVoice = voices.find(v => v.name === window.preferredVoiceName) || null;
    }

    // Fallback: pick any English voice, or first available
    if (!preferredVoice) {
      preferredVoice =
        voices.find(v => v.lang && v.lang.toLowerCase().startsWith('en')) ||
        voices[0] ||
        null;
    }
  }

  if ('speechSynthesis' in window) {
    // Voices may load asynchronously
    window.speechSynthesis.onvoiceschanged = pickPreferredVoice;
    // Try once immediately too
    pickPreferredVoice();
  }

  // ==========================
  // TTS (Speak) button handler
  // ==========================
  $('#btn-tts').on('click', function () {
    if (!('speechSynthesis' in window)) {
      alert('Sorry, your browser does not support text-to-speech.');
      return;
    }

    // Stop any previous speech
    window.speechSynthesis.cancel();

    // Only read the lyrics, not the footer
    const quoteText = $('#quote-text').text().trim();
    if (!quoteText) {
      console.log('No quote text to speak.');
      return;
    }

    const utterance = new SpeechSynthesisUtterance(quoteText);
    utterance.lang = 'en-US';
    utterance.rate = 1.0;

    // Apply the chosen voice if we have one
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    window.speechSynthesis.speak(utterance);
  });
});
