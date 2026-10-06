document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('figure img').forEach(function (img) {
        img.style.cursor = 'zoom-in';
        img.addEventListener('click', function () {
            var overlay = document.createElement('div');
            overlay.style.cssText = [
                'position:fixed', 'inset:0',
                'background:rgba(0,0,0,0.85)',
                'z-index:9999',
                'display:flex', 'align-items:center', 'justify-content:center',
                'cursor:zoom-out',
            ].join(';');

            var bigImg = document.createElement('img');
            bigImg.src = img.src;
            bigImg.style.cssText = [
                'max-width:90vw', 'max-height:90vh',
                'object-fit:contain',
                'box-shadow:0 0 40px rgba(0,0,0,0.5)',
            ].join(';');

            overlay.appendChild(bigImg);

            function close() { document.body.removeChild(overlay); }
            overlay.addEventListener('click', close);
            document.addEventListener('keydown', function esc(e) {
                if (e.key === 'Escape') {
                    close();
                    document.removeEventListener('keydown', esc);
                }
            });

            document.body.appendChild(overlay);
        });
    });
});
