<script setup>
import { onMounted, ref } from 'vue';
import { useOperadoraStore } from '../stores/operadoraStore';

const store = useOperadoraStore();

const termoBusca = ref(store.search); 

const realizarBusca = () => {
  store.filtrar(termoBusca.value);
};

onMounted(() => {
  
  if (store.operadoras.length === 0) {
    store.buscarOperadoras();
  }
});
</script>

<template>
  <div class="card shadow-sm mb-3">
    
    <div class="card-header bg-white py-3">
      <div class="row g-3 align-items-center justify-content-between">
        <div class="col-md-4">
          <h5 class="mb-0 text-primary">Operadoras</h5>
        </div>
        
        <div class="col-md-6">
          <form @submit.prevent="realizarBusca" class="d-flex gap-2">
            <input 
              v-model="termoBusca" 
              type="text" 
              class="form-control" 
              placeholder="Buscar por Razão Social ou CNPJ..."
            >
            <button class="btn btn-primary" type="submit">
              <i class="bi bi-search"></i>
            </button>
            <button 
              v-if="termoBusca" 
              @click="termoBusca = ''; realizarBusca()" 
              class="btn btn-outline-secondary" 
              type="button"
            >
              Limpar
            </button>
          </form>
        </div>
      </div>
    </div>

    <div class="card-body p-0">
      
      <div v-if="store.loading" class="text-center py-5">
        <div class="spinner-border text-primary"></div>
      </div>
      
      <div v-else class="table-responsive">
        <table class="table table-striped table-hover mb-0 align-middle">
          <thead class="table-dark">
            <tr>
              <th>Registro</th>
              <th>CNPJ</th>
              <th>Razão Social</th>
              <th class="text-center">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="op in store.operadoras" :key="op.registro_operadora">
              <td>{{ op.registro_operadora }}</td>
              <td>{{ op.cnpj }}</td>
              <td>{{ op.razao_social }}</td>
              <td class="text-center">
                <router-link :to="{ name: 'operadora-detalhes', params: { registro: op.registro_operadora } }" 
                class="btn btn-sm btn-outline-primary"> Detalhes
                </router-link>
              </td>
            </tr>
            <tr v-if="store.operadoras.length === 0">
              <td colspan="4" class="text-center py-4 text-muted">
                Nenhuma operadora encontrada para "{{ store.search }}".
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <nav v-if="store.totalPaginas > 1" class="mt-3">
    <ul class="pagination justify-content-center">
      <li class="page-item" :class="{ disabled: store.page === 1 }">
        <button class="page-link" @click="store.mudarPagina(store.page - 1)">Anterior</button>
      </li>
      <li class="page-item disabled">
        <span class="page-link text-dark">Página {{ store.page }} de {{ store.totalPaginas }}</span>
      </li>
      <li class="page-item" :class="{ disabled: store.page === store.totalPaginas }">
        <button class="page-link" @click="store.mudarPagina(store.page + 1)">Próximo</button>
      </li>
    </ul>
  </nav>
</template>