import api from './api';

export default {
  // Função para buscar a lista paginada
  // Recebe params como: { page: 1, limit: 10, search: 'Unimed' }
  getAll(params) {
    return api.get('/operadoras', { params });
  },

  // Função para buscar detalhes pelo ID (Registro ou CNPJ)
  getById(id) {
    return api.get(`/operadoras/${id}`);
  },

  // Função para buscar despesas
  getDespesas(id) {
    return api.get(`/operadoras/${id}/despesas`);
  },

  // Função para buscar estatísticas
  getEstatisticas() {
    return api.get('/estatisticas');
  }
};