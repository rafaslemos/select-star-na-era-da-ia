/**
 * Web app do deck "SELECT * na era da IA".
 * Index.html é gerado por ../build.py a partir de ../index.html; edite lá.
 */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('SELECT * na era da IA')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
