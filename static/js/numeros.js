/* Recomendaciones de QA · Campos numéricos: no se puede escribir ni pegar «e», «E», «+» ni «-».
   El navegador los acepta en <input type="number"> (notación científica: 1e2 = 100). Ningún campo del
   sistema admite negativos: los ajustes de inventario eligen «Aumentar» o «Disminuir». El servidor también
   rechaza la «e» (catalogos/campos.py); esto solo evita escribirla. */
(function () {
  "use strict";
  var PROHIBIDAS = ["e", "E", "+", "-"];

  function esNumerico(elemento) {
    return elemento && elemento.tagName === "INPUT" && elemento.type === "number";
  }

  document.addEventListener("keydown", function (evento) {
    if (esNumerico(evento.target) && PROHIBIDAS.indexOf(evento.key) !== -1) {
      evento.preventDefault();
    }
  });

  document.addEventListener("paste", function (evento) {
    if (!esNumerico(evento.target)) return;
    var texto = (evento.clipboardData || window.clipboardData).getData("text");
    if (/[eE+\-]/.test(texto)) evento.preventDefault();
  });

  document.addEventListener("drop", function (evento) {
    if (esNumerico(evento.target)) evento.preventDefault();
  });
})();
