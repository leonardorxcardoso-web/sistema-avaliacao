/**
 * Cliente HTTP fino sobre fetch. Sessão trafega via cookie HTTPOnly
 * (credentials: "include"), nunca em localStorage — evita exposição a XSS.
 */
const Api = (() => {
  async function request(path, options = {}) {
    const res = await fetch(path, {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      ...options,
    });

    if (!res.ok) {
      let detail = `Erro ${res.status}`;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch (_) {
        /* corpo não era JSON */
      }
      throw new ApiError(detail, res.status);
    }

    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return res.json();
    }
    return res;
  }

  return {
    login: (email) => request("/api/login", { method: "POST", body: JSON.stringify({ email }) }),
    logout: () => request("/api/logout", { method: "POST" }),
    me: () => request("/api/me"),
    statusAvaliacao: (certame) =>
      request(`/api/avaliacoes/status?certame=${encodeURIComponent(certame)}`),
    criarAvaliacao: (payload) =>
      request("/api/avaliacoes", { method: "POST", body: JSON.stringify(payload) }),
    criarAvaliacaoAeroporto: (payload) =>
      request("/api/avaliacoes/aeroporto", { method: "POST", body: JSON.stringify(payload) }),
    restaurarAvaliacao: (certame, idColaborador) =>
      request("/api/avaliacoes/restaurar", {
        method: "POST",
        body: JSON.stringify({ certame, id_colaborador: idColaborador }),
      }),
    certames: () => request("/api/dashboard/certames"),
    ranking: (certame) =>
      request(`/api/dashboard/ranking${certame ? `?certame=${encodeURIComponent(certame)}` : ""}`),
    observacoes: (nomeColaborador, certame) =>
      request(
        `/api/dashboard/colaborador/${encodeURIComponent(nomeColaborador)}/observacoes${
          certame ? `?certame=${encodeURIComponent(certame)}` : ""
        }`
      ),
    exportUrl: (certame) =>
      `/api/dashboard/export${certame ? `?certame=${encodeURIComponent(certame)}` : ""}`,
  };
})();

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}
