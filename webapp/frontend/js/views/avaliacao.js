/**
 * Tela de avaliação — espelha src/views/avaliacao_view.py.
 *
 * Fluxo em duas etapas, porque a lista de colaboradores/regiões varia por
 * certame (cada certame tem sua própria aba em Base.xlsx):
 * 1. Escolher o certame.
 * 2. Carregar pendências daquele certame e mostrar o formulário.
 *
 * Existem dois formulários, conforme o perfil (status.eh_aeroporto):
 * - Local: pontualidade local, proatividade, resolução.
 * - Aeroporto: pontualidade no aeroporto, facilidade de carga, resolutividade
 *   no despacho.
 * Administradores não acessam esta tela (bloqueado no backend).
 */
const AvaliacaoView = (() => {
  function render(container) {
    container.innerHTML = "";
    renderSelecaoCertame(container);
  }

  function renderSelecaoCertame(container) {
    container.innerHTML = "";
    const frag = Components.clonarTemplate("tpl-selecao-certame");
    container.appendChild(frag);

    const selectCertame = container.querySelector("#select-certame");
    const fieldCustom = container.querySelector("#field-certame-custom");
    const inputCustom = container.querySelector("#input-certame-custom");
    const btnCarregar = container.querySelector("#btn-carregar-certame");

    fieldCustom.hidden = selectCertame.value !== "Outro...";
    selectCertame.addEventListener("change", () => {
      fieldCustom.hidden = selectCertame.value !== "Outro...";
    });

    btnCarregar.addEventListener("click", () => {
      const certame =
        selectCertame.value === "Outro..." ? inputCustom.value.trim() : selectCertame.value;
      if (!certame) {
        inputCustom.focus();
        return;
      }
      carregarPendencias(container, certame);
    });
  }

  async function carregarPendencias(container, certame) {
    container.innerHTML = '<div class="skeleton"></div>';

    let status;
    try {
      status = await Api.statusAvaliacao(certame);
    } catch (erro) {
      container.innerHTML = "";
      const alerta = document.createElement("div");
      alerta.className = "rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700";
      alerta.textContent = erro.message;
      container.appendChild(alerta);
      return;
    }

    container.innerHTML = "";

    if (status.regiao_vazia) {
      container.appendChild(Components.clonarTemplate("tpl-avaliacao-vazia"));
    } else if (status.pendentes.length === 0) {
      container.appendChild(Components.clonarTemplate("tpl-avaliacao-concluida"));
    } else {
      renderFormulario(container, certame, status.pendentes, status.eh_aeroporto);
    }

    renderRestauracao(container, certame, status.minhas_avaliacoes);
  }

  function renderFormulario(container, certame, pendentes, ehAeroporto) {
    const frag = Components.clonarTemplate("tpl-avaliacao-form");
    container.appendChild(frag);

    container.querySelector("#certame-atual-label").textContent = certame;
    container.querySelector("#btn-trocar-certame").addEventListener("click", () => {
      renderSelecaoCertame(container);
    });

    const selectColaborador = container.querySelector("#select-colaborador");
    const camposLocal = container.querySelector("#campos-local");
    const camposAeroporto = container.querySelector("#campos-aeroporto");
    const form = container.querySelector("#form-avaliacao");
    const alertaErro = container.querySelector("#avaliacao-alert");
    const alertaSucesso = container.querySelector("#avaliacao-sucesso");

    camposLocal.hidden = ehAeroporto;
    camposAeroporto.hidden = !ehAeroporto;

    pendentes.forEach((colaborador) => {
      const option = document.createElement("option");
      option.value = colaborador.id;
      option.textContent = colaborador.nome;
      option.dataset.nome = colaborador.nome;
      selectColaborador.appendChild(option);
    });

    Components.inicializarRatingFields(form);

    form.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      Components.esconderAlerta(alertaErro);
      Components.esconderAlerta(alertaSucesso);

      const opcaoColaborador = selectColaborador.selectedOptions[0];
      const valoresRating = Components.lerValoresRating(form);
      const observacoes = form.querySelector("#input-observacoes").value;

      const base = {
        certame,
        id_colaborador: opcaoColaborador.value,
        nome_colaborador: opcaoColaborador.dataset.nome,
        observacoes,
      };

      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;

      try {
        if (ehAeroporto) {
          await Api.criarAvaliacaoAeroporto({
            ...base,
            pontualidade_aeroporto: valoresRating.pontualidade_aeroporto,
            facilidade_carga: valoresRating.facilidade_carga,
            resolutividade_despacho: valoresRating.resolutividade_despacho,
          });
        } else {
          await Api.criarAvaliacao({
            ...base,
            pontualidade_local: valoresRating.pontualidade_local,
            proatividade_ocorrencias: valoresRating.proatividade_ocorrencias,
            proatividade_lancamentos: valoresRating.proatividade_lancamentos,
            proatividade_respostas: valoresRating.proatividade_respostas,
            resolucao_problemas: valoresRating.resolucao_problemas,
          });
        }
        Components.mostrarAlerta(alertaSucesso, "Avaliação registrada com sucesso na nuvem!");
        setTimeout(() => carregarPendencias(container, certame), 900);
      } catch (erro) {
        Components.mostrarAlerta(alertaErro, erro.message);
        submitBtn.disabled = false;
      }
    });
  }

  function renderRestauracao(container, certame, minhasAvaliacoes) {
    if (!minhasAvaliacoes || minhasAvaliacoes.length === 0) return;

    const frag = Components.clonarTemplate("tpl-restauracao");
    container.appendChild(frag);

    const select = container.querySelector("#select-restaurar");
    minhasAvaliacoes.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.ID_Colaborador;
      option.textContent = item.Nome_Colaborador;
      select.appendChild(option);
    });

    const btnRestaurar = container.querySelector("#btn-restaurar");
    const alertaErro = container.querySelector("#restaurar-alert");
    const alertaSucesso = container.querySelector("#restaurar-sucesso");

    btnRestaurar.addEventListener("click", async () => {
      Components.esconderAlerta(alertaErro);
      Components.esconderAlerta(alertaSucesso);
      btnRestaurar.disabled = true;

      try {
        await Api.restaurarAvaliacao(certame, select.value);
        Components.mostrarAlerta(alertaSucesso, "Colaborador restaurado com sucesso!");
        setTimeout(() => carregarPendencias(container, certame), 900);
      } catch (erro) {
        Components.mostrarAlerta(alertaErro, erro.message);
        btnRestaurar.disabled = false;
      }
    });
  }

  return { render };
})();
