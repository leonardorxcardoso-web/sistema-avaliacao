/**
 * Orquestrador: decide entre tela de login e painel logado, controla a
 * navegação entre Avaliação / Dashboard / Perfil (agora só pela sidebar,
 * sem tabs na página) e os elementos fixos do shell (relógio, menu de
 * usuário, sidebar).
 */
(async function init() {
  const root = document.getElementById("app");

  const ICONE_AVALIACAO =
    '<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" /><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 13.5v4.75A2.25 2.25 0 0117.25 20.5H6.75A2.25 2.25 0 014.5 18.25V7.75A2.25 2.25 0 016.75 5.5h4.75" /></svg>';
  const ICONE_DASHBOARD =
    '<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.5h6v6.75H3v-6.75zM15 3h6v17.25h-6V3zM9 8.25h6v12H9v-12z" /></svg>';

  function _perfilTexto(sessao) {
    if (sessao.eh_admin) return "Administrador";
    if (sessao.eh_supervisor) return "Supervisor";
    if (sessao.eh_aeroporto) return "Equipe Aeroporto";
    return "Avaliador";
  }

  function _telaInicial(sessao) {
    return sessao.pode_avaliar ? "avaliacao" : "dashboard";
  }

  function _telaPermitida(sessao, destino) {
    if (destino === "avaliacao") return sessao.pode_avaliar;
    if (destino === "dashboard") return sessao.pode_ver_dashboard;
    if (destino === "perfil") return true;
    return false;
  }

  function _telaDoHash(sessao) {
    const destino = window.location.hash.replace("#", "");
    return _telaPermitida(sessao, destino) ? destino : _telaInicial(sessao);
  }

  try {
    const sessao = await Api.me();
    renderPainel(sessao);
  } catch (_) {
    renderLogin();
  }

  function renderLogin() {
    window.location.hash = "";
    LoginView.render(root, (sessao) => {
      window.location.hash = _telaInicial(sessao);
      renderPainel(sessao);
    });
  }

  function renderPainel(sessao) {
    root.innerHTML = "";
    root.appendChild(Components.clonarTemplate("tpl-shell"));

    root.querySelector("#topbar-nome").textContent = sessao.nome;
    root.querySelector("#user-menu-nome").textContent = sessao.nome;
    root.querySelector("#user-menu-email").textContent = sessao.email;
    root.querySelector("#topbar-regiao").textContent = sessao.regiao || "Todas";

    const badge = root.querySelector("#perfil-badge");
    badge.textContent = _perfilTexto(sessao);
    badge.classList.add(sessao.eh_admin ? "text-amber-700" : "text-blue-700");

    iniciarRelogio(root);
    configurarMenuUsuario(root, sessao);

    root.querySelector("#btn-logout").addEventListener("click", async () => {
      await Api.logout();
      renderLogin();
    });

    const viewAvaliacao = root.querySelector("#tab-avaliacao");
    const viewDashboard = root.querySelector("#tab-dashboard");
    const viewPerfil = root.querySelector("#tab-perfil");

    let dashboardCarregado = false;

    function irPara(destino) {
      if (window.location.hash.replace("#", "") !== destino) {
        window.location.hash = destino;
      }

      viewAvaliacao.classList.toggle("hidden", destino !== "avaliacao");
      viewDashboard.classList.toggle("hidden", destino !== "dashboard");
      viewPerfil.classList.toggle("hidden", destino !== "perfil");

      if (destino === "dashboard" && !dashboardCarregado) {
        dashboardCarregado = true;
        DashboardView.render(viewDashboard);
      }
      if (destino === "perfil") {
        renderPerfil(viewPerfil, sessao, () => irPara(_telaInicial(sessao)));
      }
    }

    root.irPara = irPara;

    const telaInicialReal = _telaDoHash(sessao);
    if (sessao.pode_avaliar) {
      AvaliacaoView.render(viewAvaliacao);
    }
    irPara(telaInicialReal);

    configurarSidebar(root, sessao, irPara, viewAvaliacao);

    root.querySelector("#btn-logo-home").addEventListener("click", () => {
      const destino = _telaInicial(sessao);
      if (destino === "avaliacao" && sessao.pode_avaliar) {
        AvaliacaoView.render(viewAvaliacao);
      }
      irPara(destino);
    });

    root.querySelector("#btn-perfil").addEventListener("click", () => {
      root.querySelector("#user-menu").classList.add("hidden");
      irPara("perfil");
    });
  }

  function renderPerfil(container, sessao, onVoltar) {
    container.innerHTML = "";
    const frag = Components.clonarTemplate("tpl-perfil");
    container.appendChild(frag);

    container.querySelector("#perfil-nome").textContent = sessao.nome;
    container.querySelector("#perfil-email").textContent = sessao.email;
    container.querySelector("#perfil-tipo").textContent = _perfilTexto(sessao);
    container.querySelector("#perfil-regiao").textContent = sessao.regiao || "Todas";

    container.querySelector("#btn-perfil-voltar").addEventListener("click", onVoltar);
  }

  function iniciarRelogio(root) {
    const dateEl = root.querySelector("#clock-date");
    const timeEl = root.querySelector("#clock-time");

    function atualizar() {
      const agora = new Date();
      const dataFormatada = agora.toLocaleDateString("pt-BR", {
        timeZone: "America/Sao_Paulo",
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric",
      });
      const horaFormatada = agora.toLocaleTimeString("pt-BR", {
        timeZone: "America/Sao_Paulo",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });

      dateEl.textContent = dataFormatada.charAt(0).toUpperCase() + dataFormatada.slice(1);
      timeEl.textContent = horaFormatada;
    }

    atualizar();
    setInterval(atualizar, 1000);
  }

  function configurarMenuUsuario(root) {
    const trigger = root.querySelector("#user-menu-trigger");
    const menu = root.querySelector("#user-menu");

    trigger.addEventListener("click", (evento) => {
      evento.stopPropagation();
      menu.classList.toggle("hidden");
    });

    document.addEventListener("click", (evento) => {
      if (!menu.contains(evento.target) && !trigger.contains(evento.target)) {
        menu.classList.add("hidden");
      }
    });
  }

  function configurarSidebar(root, sessao, irPara, viewAvaliacao) {
    const drawer = root.querySelector("#drawer-navigation");
    const overlay = root.querySelector("#sidebar-overlay");
    const btnOpen = root.querySelector("#btn-sidebar-open");
    const btnClose = root.querySelector("#btn-sidebar-close");
    const nav = root.querySelector("#sidebar-nav");

    const itens = [
      { tab: "avaliacao", label: "Realizar Avaliação", icone: ICONE_AVALIACAO, visivel: sessao.pode_avaliar },
      { tab: "dashboard", label: "Dashboard Admin", icone: ICONE_DASHBOARD, visivel: sessao.pode_ver_dashboard },
    ];

    itens
      .filter((item) => item.visivel)
      .forEach((item) => {
        const frag = Components.clonarTemplate("tpl-sidebar-item");
        const botao = frag.querySelector(".sidebar-link");
        botao.dataset.tab = item.tab;
        botao.querySelector(".sidebar-link__icon").innerHTML = item.icone;
        botao.querySelector(".sidebar-link__label").textContent = item.label;
        botao.addEventListener("click", () => {
          if (item.tab === "avaliacao") {
            AvaliacaoView.render(viewAvaliacao);
          }
          irPara(item.tab);
          fecharDrawer();
        });
        nav.appendChild(frag);
      });

    function abrirDrawer() {
      drawer.classList.remove("-translate-x-full");
      overlay.classList.remove("hidden");
      btnOpen.setAttribute("aria-expanded", "true");
    }

    function fecharDrawer() {
      drawer.classList.add("-translate-x-full");
      overlay.classList.add("hidden");
      btnOpen.setAttribute("aria-expanded", "false");
    }

    btnOpen.addEventListener("click", abrirDrawer);
    btnClose.addEventListener("click", fecharDrawer);
    overlay.addEventListener("click", fecharDrawer);
    document.addEventListener("keydown", (evento) => {
      if (evento.key === "Escape") fecharDrawer();
    });
  }
})();
