import { defineStore } from 'pinia';
import OperadoraService from '../services/OperadoraService';

export const useOperadoraStore = defineStore('operadora', {
  
  state: () => ({
    operadoras: [],
    total: 0,
    page: 1,
    limit: 10,
    search: '',
    loading: false,
    erro: null
  }),

  getters: {
    totalPaginas: (state) => Math.ceil(state.total / state.limit)
  },

  actions: {
    async buscarOperadoras() {
      this.loading = true;
      this.erro = null;

      try {
        const params = {
          page: this.page,
          limit: this.limit,
          search: this.search
        };

        const response = await OperadoraService.getAll(params);
        
        this.operadoras = response.data.data;
        this.total = response.data.total;
      } catch (error) {
        console.error(error);
        this.erro = 'Erro ao carregar dados.';
      } finally {
        this.loading = false;
      }
    },

    mudarPagina(novaPagina) {
      if (novaPagina >= 1 && novaPagina <= this.totalPaginas) {
        this.page = novaPagina;
        this.buscarOperadoras();
      }
    },

    filtrar(termo) {
      this.search = termo;
      this.page = 1; // Sempre volta pra primeira página ao filtrar
      this.buscarOperadoras();
    }
  }
});