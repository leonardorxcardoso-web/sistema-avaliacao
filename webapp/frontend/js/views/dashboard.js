/**
 * Painel administrativo: filtro por certame, ranking geral e detalhamento
 * por colaborador — espelha src/views/dashboard_view.py.
 */
const DashboardView = (() => {
  const OPCAO_TODOS = "Todos (Histórico Completo)";
  const OPCAO_RANKING = "Visão Geral (Ranking)";

  async function render(container) {
    container.innerHTML = '<div class="skeleton"></div>';

    let certames;
    try {
      certames = await Api.certames();
    } catch (erro) {
      renderErro(container, erro.message);
      return;
    }

    container.innerHTML = "";
    const frag = Components.clonarTemplate("tpl-dashboard");
    container.appendChild(frag);

    if (certames.length === 0) {
      const info = document.createElement("div");
      info.className = "rounded-md bg-blue-50 border border-blue-200 px-4 py-3 text-sm text-blue-800";
      info.textContent = "Ainda não há avaliações registradas no sistema.";
      container.querySelector("#dashboard-conteudo").appendChild(info);
      return;
    }

    const filtrosEl = container.querySelector("#dashboard-filtros");
    const selectCertame = criarSelect("Filtrar por Projeto", [OPCAO_TODOS, ...certames]);
    filtrosEl.appendChild(selectCertame.field);

    const conteudoEl = container.querySelector("#dashboard-conteudo");

    async function atualizarConteudo() {
      const certameAtual = selectCertame.select.value === OPCAO_TODOS ? null : selectCertame.select.value;
      await renderRankingOuIndividual(conteudoEl, certameAtual, filtrosEl, selectCertame.select.value);
    }

    selectCertame.select.addEventListener("change", atualizarConteudo);
    await atualizarConteudo();
  }

  function renderErro(container, mensagem) {
    container.innerHTML = "";
    const alerta = document.createElement("div");
    alerta.className = "rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700";
    alerta.textContent = mensagem;
    container.appendChild(alerta);
  }

  function criarSelect(rotulo, opcoes) {
    const field = document.createElement("label");
    field.className = "block";

    const label = document.createElement("span");
    label.className = "block text-sm font-medium text-gray-700";
    label.textContent = rotulo;

    const select = document.createElement("select");
    select.className =
      "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600";
    opcoes.forEach((opcao) => {
      const option = document.createElement("option");
      option.value = opcao;
      option.textContent = opcao;
      select.appendChild(option);
    });

    field.appendChild(label);
    field.appendChild(select);
    return { field, select };
  }

  async function renderRankingOuIndividual(conteudoEl, certame, filtrosEl, filtroLabel) {
    let ranking;
    try {
      ranking = await Api.ranking(certame);
    } catch (erro) {
      renderErro(conteudoEl, erro.message);
      return;
    }

    conteudoEl.innerHTML = "";

    if (ranking.length === 0) {
      const aviso = document.createElement("div");
      aviso.className = "rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700";
      aviso.textContent = "Nenhuma avaliação encontrada para este certame.";
      conteudoEl.appendChild(aviso);
      return;
    }

    // Remove seletor de colaborador anterior, se houver, e recria.
    let selectPesquisa = filtrosEl.querySelector("#dashboard-pesquisa-wrapper");
    if (selectPesquisa) selectPesquisa.remove();

    const nomes = ranking.map((r) => r.Nome_Colaborador);
    const { field, select } = criarSelect("Buscar painel individual", [OPCAO_RANKING, ...nomes]);
    field.id = "dashboard-pesquisa-wrapper";
    filtrosEl.appendChild(field);

    function renderEscolha() {
      conteudoEl.innerHTML = "";
      if (select.value === OPCAO_RANKING) {
        renderRankingGeral(conteudoEl, ranking, filtroLabel, certame);
      } else {
        renderPainelIndividual(conteudoEl, ranking, select.value, filtroLabel, certame);
      }
    }

    select.addEventListener("change", renderEscolha);
    renderEscolha();
  }

  function renderRankingGeral(conteudoEl, ranking, filtroLabel, certame) {
    const card = document.createElement("div");
    card.className = "rounded-lg bg-white p-5 shadow sm:p-6";

    const titulo = document.createElement("h3");
    titulo.className = "text-base font-semibold text-gray-800";
    titulo.textContent = `Ranking Geral de Colaboradores (${filtroLabel})`;
    card.appendChild(titulo);

    const btnExport = document.createElement("a");
    btnExport.className =
      "mt-4 inline-flex items-center gap-2 rounded-md bg-blue-950 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-900";
    btnExport.href = Api.exportUrl(certame);
    btnExport.innerHTML = `
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
      </svg>
      Baixar Relatório em Excel
    `;
    card.appendChild(btnExport);

    const tableWrap = document.createElement("div");
    tableWrap.className = "mt-5 overflow-x-auto rounded-md border border-gray-200";

    const table = document.createElement("table");
    table.className = "min-w-full divide-y divide-gray-200 text-sm";
    table.innerHTML = `
      <thead class="bg-gray-50">
        <tr>
          <th class="px-4 py-2 text-left font-medium text-gray-500">#</th>
          <th class="px-4 py-2 text-left font-medium text-gray-500">Colaborador</th>
          <th class="px-4 py-2 text-left font-medium text-gray-500">Nota Geral</th>
          <th class="px-4 py-2 text-left font-medium text-gray-500">Pont. Aeroporto</th>
          <th class="px-4 py-2 text-left font-medium text-gray-500">Facilidade Carga</th>
          <th class="px-4 py-2 text-left font-medium text-gray-500">Resol. Despacho</th>
          <th class="px-4 py-2 text-left font-medium text-gray-500">Pont. Local</th>
          <th class="px-4 py-2 text-left font-medium text-gray-500">Respostas</th>
          <th class="px-4 py-2 text-left font-medium text-gray-500">Resolutividade</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100 bg-white"></tbody>
    `;

    const tbody = table.querySelector("tbody");
    ranking.forEach((linha, indice) => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-gray-50";
      tr.innerHTML = `
        <td class="px-4 py-2">${rankPill(indice)}</td>
        <td class="px-4 py-2 font-medium text-gray-900">${escapeHtml(linha.Nome_Colaborador)}</td>
        <td class="px-4 py-2 text-gray-700">${formatarNota(linha.Nota_Geral_Projeto)}</td>
        <td class="px-4 py-2 text-gray-700">${formatarNota(linha.Pontualidade_Aeroporto)}</td>
        <td class="px-4 py-2 text-gray-700">${formatarNota(linha.Facilidade_Carga)}</td>
        <td class="px-4 py-2 text-gray-700">${formatarNota(linha.Resolutividade_Despacho)}</td>
        <td class="px-4 py-2 text-gray-700">${formatarNota(linha.Pontualidade_Local)}</td>
        <td class="px-4 py-2 text-gray-700">${formatarNota(linha.Proatividade_Respostas)}</td>
        <td class="px-4 py-2 text-gray-700">${formatarNota(linha.Resolucao_Problemas)}</td>
      `;
      tbody.appendChild(tr);
    });

    tableWrap.appendChild(table);
    card.appendChild(tableWrap);
    conteudoEl.appendChild(card);
  }

  function rankPill(indice) {
    const posicao = indice + 1;
    const classes = ["", "rank-pill--gold", "rank-pill--silver", "rank-pill--bronze"];
    const classe = classes[posicao] || "";
    return `<span class="rank-pill ${classe}">${posicao}</span>`;
  }

  async function renderPainelIndividual(conteudoEl, ranking, nomeColaborador, filtroLabel, certame) {
    const dados = ranking.find((r) => r.Nome_Colaborador === nomeColaborador);

    const card = document.createElement("div");
    card.className = "space-y-4 rounded-lg bg-white p-5 shadow sm:p-6";

    const titulo = document.createElement("h3");
    titulo.className = "text-base font-semibold text-blue-950";
    titulo.textContent = `Desempenho: ${nomeColaborador}`;

    const caption = document.createElement("p");
    caption.className = "text-sm text-gray-500";
    caption.innerHTML = `Dados filtrados por: <strong>${escapeHtml(filtroLabel)}</strong>`;

    const mediaAeroporto = mediaDe([
      dados.Pontualidade_Aeroporto,
      dados.Facilidade_Carga,
      dados.Resolutividade_Despacho,
    ]);
    const mediaLocal = mediaDe([
      dados.Pontualidade_Local,
      dados.Proatividade_Ocorrencias,
      dados.Proatividade_Lancamentos,
      dados.Proatividade_Respostas,
      dados.Resolucao_Problemas,
    ]);

    const metrics = document.createElement("div");
    metrics.className = "grid grid-cols-1 gap-4 sm:grid-cols-3";
    metrics.innerHTML = `
      ${metricCard("Nota Geral Média", `${formatarNota(dados.Nota_Geral_Projeto)} / 5.0`)}
      ${metricCard("Média Aeroporto", formatarNota(mediaAeroporto))}
      ${metricCard("Média Local/Proatividade", formatarNota(mediaLocal))}
    `;

    card.appendChild(titulo);
    card.appendChild(caption);
    card.appendChild(metrics);

    const obsTitulo = document.createElement("h4");
    obsTitulo.className = "text-sm font-semibold text-gray-800";
    obsTitulo.textContent = "Histórico de Observações";
    card.appendChild(obsTitulo);

    try {
      const observacoes = await Api.observacoes(nomeColaborador, certame);
      if (observacoes.length === 0) {
        const vazio = document.createElement("p");
        vazio.className = "text-sm text-gray-500";
        vazio.textContent = "Nenhuma observação registrada.";
        card.appendChild(vazio);
      } else {
        observacoes.forEach((obs) => {
          const alerta = document.createElement("div");
          alerta.className = "rounded-md bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800";
          alerta.innerHTML = `<strong>Projeto:</strong> ${escapeHtml(obs.Certame)} | <strong>Em:</strong> ${escapeHtml(
            obs.Data
          )} | <strong>Por:</strong> ${escapeHtml(obs.Email_Avaliador)}<br/><br/>${escapeHtml(obs.Observacoes)}`;
          card.appendChild(alerta);
        });
      }
    } catch (erro) {
      const alertaErro = document.createElement("div");
      alertaErro.className = "rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700";
      alertaErro.textContent = erro.message;
      card.appendChild(alertaErro);
    }

    conteudoEl.appendChild(card);
  }

  function metricCard(rotulo, valor) {
    return `
      <div class="metric-card">
        <div class="metric-card__label">${escapeHtml(rotulo)}</div>
        <div class="metric-card__value">${escapeHtml(valor)}</div>
      </div>
    `;
  }

  function formatarNota(valor) {
    return valor === null || valor === undefined || Number.isNaN(valor) ? "-" : Number(valor).toFixed(1);
  }

  function mediaDe(valores) {
    const validos = valores.filter((v) => v !== null && v !== undefined && !Number.isNaN(v));
    if (validos.length === 0) return null;
    return validos.reduce((soma, v) => soma + v, 0) / validos.length;
  }

  function escapeHtml(valor) {
    const div = document.createElement("div");
    div.textContent = valor ?? "";
    return div.innerHTML;
  }

  return { render };
})();
