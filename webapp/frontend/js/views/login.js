/**
 * Tela de login: envia o e-mail, e o backend valida contra Base.xlsx e
 * define o cookie de sessão.
 */
const LoginView = (() => {
  function render(container, onLoginSuccess) {
    container.innerHTML = "";
    container.appendChild(Components.clonarTemplate("tpl-login"));

    const form = container.querySelector("#login-form");
    const emailInput = container.querySelector("#login-email");
    const alerta = container.querySelector("#login-alert");

    form.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      Components.esconderAlerta(alerta);

      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;

      try {
        const sessao = await Api.login(emailInput.value);
        onLoginSuccess(sessao);
      } catch (erro) {
        Components.mostrarAlerta(alerta, erro.message || "Credenciais inválidas. Verifique seu e-mail e tente novamente.");
      } finally {
        submitBtn.disabled = false;
      }
    });

    emailInput.focus();
  }

  return { render };
})();
