"use strict";

// Si carica nel <head>, prima del CSS disegnato: così la pagina compare subito con il tema scelto, senza lampi.
const TEMI = { auto: "Automatico", chiaro: "Chiaro", scuro: "Scuro", quaderno: "Quaderno", terminale: "Terminale", nothing: "Nothing", ultra: "Ultra" };

function applicaTema(nome) {
  if (!TEMI[nome]) nome = "auto";
  if (nome === "auto") delete document.documentElement.dataset.tema;
  else document.documentElement.dataset.tema = nome;
  return nome;
}

let temaScelto = "auto";
try { temaScelto = applicaTema(localStorage.getItem("tema")); } catch {}
