$(function () {
  $('#btn-new').on('click', function () {
    const slug = $(this).data('slug');

    $.getJSON(`/api/quote/${slug}`, function (res) {
      if (res.ok) {
        // Update lyric text (may include <br>)
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
});
