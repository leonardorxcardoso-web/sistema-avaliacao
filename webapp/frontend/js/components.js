/**
 * Helpers pequenos e reutilizados entre views: clonar templates, montar
 * campos de estrelas e exibir/ocultar alertas de forma consistente.
 */
const Components = (() => {
  function clonarTemplate(id) {
    const tpl = document.getElementById(id);
    return tpl.content.cloneNode(true);
  }

  function montarCampoEstrelas(container, name) {
    const stars = document.createElement("div");
    stars.className = "rating-field__stars";

    for (let valor = 1; valor <= 5; valor += 1) {
      const wrapper = document.createElement("span");
      wrapper.className = "star-option";

      const input = document.createElement("input");
      input.type = "radio";
      input.name = name;
      input.value = String(valor);
      input.id = `${name}-${valor}`;
      if (valor === 3) input.checked = true;

      const label = document.createElement("label");
      label.setAttribute("for", input.id);
      label.textContent = String(valor);

      wrapper.appendChild(input);
      wrapper.appendChild(label);
      stars.appendChild(wrapper);
    }

    container.appendChild(stars);
  }

  function inicializarRatingFields(escopo) {
    escopo.querySelectorAll(".rating-field").forEach((campo) => {
      const nomeCampo = campo.dataset.field;
      const rotulo = campo.dataset.label;

      const label = document.createElement("span");
      label.className = "rating-field__label";
      label.textContent = rotulo;
      campo.appendChild(label);

      montarCampoEstrelas(campo, nomeCampo);
    });
  }

  function lerValoresRating(escopo) {
    const valores = {};
    escopo.querySelectorAll(".rating-field").forEach((campo) => {
      const nomeCampo = campo.dataset.field;
      const selecionado = campo.querySelector(`input[name="${nomeCampo}"]:checked`);
      valores[nomeCampo] = selecionado ? Number(selecionado.value) : 3;
    });
    return valores;
  }

  function mostrarAlerta(elemento, mensagem) {
    elemento.textContent = mensagem;
    elemento.classList.remove("hidden");
  }

  function esconderAlerta(elemento) {
    elemento.classList.add("hidden");
    elemento.textContent = "";
  }

  return {
    clonarTemplate,
    inicializarRatingFields,
    lerValoresRating,
    mostrarAlerta,
    esconderAlerta,
  };
})();
