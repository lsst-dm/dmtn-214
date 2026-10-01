
    (function() {
        function initZoom() {
            if (typeof jQuery === 'undefined') {
                setTimeout(initZoom, 100);
                return;
            }
            jQuery(document).ready(function($) {
                // Target all images in the main content area
                $('figure img, .section img, article img').each(function() {
                    var $img = $(this);
                    // Skip if already wrapped in a link
                    if ($img.parent('a').length === 0) {
                        var src = $img.attr('src');
                        if (src) {
                            $img.wrap('<a href="' + src + '" data-lightbox="technote" data-title="' + ($img.attr('alt') || '') + '"></a>');
                            $img.css('cursor', 'zoom-in');
                        }
                    }
                });
            });
        }
        initZoom();
    })();
    