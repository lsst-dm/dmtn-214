# See the Documenteer docs for how to customize conf.py:
# https://documenteer.lsst.io/technotes/

from documenteer.conf.technote import *  # noqa F401 F403

# Add sphinxcontrib.images and sphinxcontrib-jquery to the extensions list
# (Using extend to ensure we don't overwrite the list)
extensions.extend(["sphinxcontrib.images", "sphinxcontrib.jquery"])

# Configure sphinxcontrib.images
images_config = {
    "override_image_directive": True,
    "backend": "LightBox2",
    "default_group": "default",
}

# Add custom JS to ensure all figures are clickable even if the extension misses them
def setup(app):
    import os
    # Create _static directory in the build source if it doesn't exist
    static_path = os.path.join(app.srcdir, '_static')
    if not os.path.exists(static_path):
        os.makedirs(static_path)
    
    js_content = """
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
    """
    js_file = os.path.join(static_path, 'lightbox_init.js')
    with open(js_file, 'w') as f:
        f.write(js_content)
    
    app.add_js_file('lightbox_init.js')

# Ensure _static is in html_static_path
if '_static' not in html_static_path:
    html_static_path.append('_static')
