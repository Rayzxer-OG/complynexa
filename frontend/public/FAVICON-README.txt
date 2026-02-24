Favicon files (generate from complyon-logo.png)
==============================================

Place these files in this folder (/public):

  favicon.ico         - Main favicon (e.g. 32x32 or multi-size ICO)
  favicon-16x16.png   - 16×16 PNG for browser tabs
  favicon-32x32.png   - 32×32 PNG for bookmarks / high-DPI
  apple-touch-icon.png - 180×180 PNG for iOS home screen

Quick way to generate (using complyon-logo.png):
- Use an online tool: https://realfavicongenerator.net/ or https://favicon.io/
- Or ImageMagick: convert complyon-logo.png -resize 32x32 favicon-32x32.png

Minimum: Add favicon.ico for browser tab icon. Others improve bookmarks and mobile.
