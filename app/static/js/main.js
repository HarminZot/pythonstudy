
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
window.apiFetch = async function(url, options = {}) {
    const headers = new Headers(options.headers || {});
    if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
        headers.set('Content-Type', 'application/json');
    }
    headers.set('X-CSRFToken', csrfToken);
    return fetch(url, {...options, headers});
};

document.querySelector('.menu-toggle')?.addEventListener('click', () => {
    document.querySelector('.main-nav')?.classList.toggle('open');
});

for (const flash of document.querySelectorAll('.flash')) {
    setTimeout(() => flash.classList.add('fade'), 7000);
}
