"use strict";

// Scritte a punti 5×7 per il tema «Nothing» (le stesse dei widget Android, vedi PuntiMatrice.kt). Niente font da scaricare: è SVG.
const PUNTI = Object.fromEntries(Object.entries({
  0: " ### |#   #|#  ##|# # #|##  #|#   #| ### ", 1: "  #  | ##  |  #  |  #  |  #  |  #  | ### ",
  2: " ### |#   #|    #|   # |  #  | #   |#####", 3: "#####|   # |  #  |   # |    #|#   #| ### ",
  4: "   # |  ## | # # |#  # |#####|   # |   # ", 5: "#####|#    |#### |    #|    #|#   #| ### ",
  6: "  ## | #   |#    |#### |#   #|#   #| ### ", 7: "#####|    #|   # |  #  | #   | #   | #   ",
  8: " ### |#   #|#   #| ### |#   #|#   #| ### ", 9: " ### |#   #|#   #| ####|    #|   # | ##  ",
  A: " ### |#   #|#   #|#####|#   #|#   #|#   #", B: "#### |#   #|#   #|#### |#   #|#   #|#### ",
  C: " ### |#   #|#    |#    |#    |#   #| ### ", D: "###  |#  # |#   #|#   #|#   #|#  # |###  ",
  E: "#####|#    |#    |#### |#    |#    |#####", F: "#####|#    |#    |#### |#    |#    |#    ",
  G: " ### |#   #|#    |# ###|#   #|#   #| ####", H: "#   #|#   #|#   #|#####|#   #|#   #|#   #",
  I: " ### |  #  |  #  |  #  |  #  |  #  | ### ", J: "  ###|   # |   # |   # |   # |#  # | ##  ",
  K: "#   #|#  # |# #  |##   |# #  |#  # |#   #", L: "#    |#    |#    |#    |#    |#    |#####",
  M: "#   #|## ##|# # #|# # #|#   #|#   #|#   #", N: "#   #|#   #|##  #|# # #|#  ##|#   #|#   #",
  O: " ### |#   #|#   #|#   #|#   #|#   #| ### ", P: "#### |#   #|#   #|#### |#    |#    |#    ",
  Q: " ### |#   #|#   #|#   #|# # #|#  # | ## #", R: "#### |#   #|#   #|#### |# #  |#  # |#   #",
  S: " ####|#    |#    | ### |    #|    #|#### ", T: "#####|  #  |  #  |  #  |  #  |  #  |  #  ",
  U: "#   #|#   #|#   #|#   #|#   #|#   #| ### ", V: "#   #|#   #|#   #|#   #|#   #| # # |  #  ",
  W: "#   #|#   #|#   #|# # #|# # #|# # #| # # ", X: "#   #|#   #| # # |  #  | # # |#   #|#   #",
  Y: "#   #|#   #| # # |  #  |  #  |  #  |  #  ", Z: "#####|    #|   # |  #  | #   |#    |#####",
  "-": "     |     |     | ### |     |     |     ", "+": "     |  #  |  #  |#####|  #  |  #  |     ",
  "/": "    #|    #|   # |  #  | #   |#    |#    ", "?": " ### |#   #|    #|   # |  #  |     |  #  ",
  "%": "##   |##  #|   # |  #  | #   |#  ##|   ##", ":": " | |#| | |#| ", ".": " | | | | | |#", ",": "  |  |  |  |  | #|# ",
  "!": "#|#|#|#|#| |#", " ": "   |   |   |   |   |   |   ",
}).map(([k, v]) => [k, v.split("|")]));

// La scritta come SVG: i puntini accesi nel colore del testo, quelli spenti appena visibili.
function puntini(testo, passo = 4) {
  const pulito = String(testo).toUpperCase().normalize("NFD").replace(/\p{M}/gu, "").replace(/[–—]/g, "-");
  const glifi = [...pulito].map((c) => PUNTI[c] || PUNTI["?"]);
  let x = 0, cerchi = "";
  glifi.forEach((righe, i) => {
    const larghezza = righe[0].length + (i < glifi.length - 1 ? 1 : 0);
    for (let y = 0; y < 7; y++) for (let k = 0; k < larghezza; k++) {
      const acceso = righe[y][k] === "#";
      cerchi += `<circle cx="${(x + k + 0.5) * passo}" cy="${(y + 0.5) * passo}" r="${passo * 0.38}"${acceso ? "" : ' opacity=".13"'}/>`;
    }
    x += larghezza;
  });
  return `<svg class="punti" viewBox="0 0 ${x * passo} ${7 * passo}" width="${x * passo}" height="${7 * passo}" fill="currentColor" aria-hidden="true">${cerchi}</svg>`;
}
