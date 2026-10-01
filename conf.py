# See the Documenteer docs for how to customize conf.py:
# https://documenteer.lsst.io/technotes/

from documenteer.conf.technote import *  # noqa F401 F403

# Add sphinxcontrib.images to the extensions list
# (Using extend to ensure we don't overwrite the list)
# Sphinx will have 'extensions' in the global scope at runtime from the import above.
extensions.extend(["sphinxcontrib.images"])

# Configure sphinxcontrib.images to override the default image directive
# and use the LightBox2 backend for click-to-zoom functionality.
images_config = {
    "override_image_directive": True,
    "backend": "LightBox2",
    "default_group": "default",
}

# Add custom JS to handle click-to-zoom for figures as well, 
# since override_image_directive might not catch all figure-wrapped images.
def setup(app):
    app.add_js_file(None, body="""
        $(document).ready(function() {
            $('figure img').each(function() {
                var $img = $(this);
                if ($img.parent('a').length === 0) {
                    var src = $img.attr('src');
                    $img.wrap('<a href="' + src + '" data-lightbox="default" data-title="' + ($img.attr('alt') || '') + '"></a>');
                }
            });
        });
    """)
