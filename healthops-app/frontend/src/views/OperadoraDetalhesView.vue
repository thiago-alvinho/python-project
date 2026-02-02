<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import OperadoraService from '../services/OperadoraService';

const route = useRoute();
const router = useRouter();

const registro = route.params.registro;

const operadora = ref(null);
const despesas = ref([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const [opResponse, despesasResponse] = await Promise.all([
      OperadoraService.getById(registro),
      OperadoraService.getDespesas(registro)
    ]);

    operadora.value = opResponse.data;
    despesas.value = despesasResponse.data;

  } catch (error) {
    console.error("Erro ao carregar detalhes:", error);
    alert("Erro ao carregar dados. Verifique o console.");
  } finally {
    loading.value = false;
  }
});

const formatarMoeda = (valor) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
};
</script>

<template>
  <div v-if="loading" class="text-center py-5">
    <div class="spinner-border text-primary"></div>
    <p class="mt-2">Carregando informações...</p>
  </div>

  <div v-else-if="operadora">
    <button @click="router.back()" class="btn btn-outline-secondary mb-4">
      <i class="bi bi-arrow-left"></i> Voltar
    </button>

    <div class="card shadow-sm mb-4">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">
          <i class="bi bi-building"></i> {{ operadora.razao_social }}
        </h5>
      </div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-3">
            <strong>Registro ANS:</strong> <br> {{ operadora.registro_operadora }}
          </div>
          <div class="col-md-3">
            <strong>CNPJ:</strong> <br> {{ operadora.cnpj }}
          </div>
          <div class="col-md-3">
            <strong>Telefone:</strong> <br> ({{ operadora.ddd }}) {{ operadora.telefone }}
          </div>
          <div class="col-md-3">
            <strong>Modalidade:</strong> <br> {{ operadora.modalidade }}
          </div>
          
          <div class="col-md-6">
            <strong>Endereço:</strong> <br> 
            {{ operadora.logradouro }}, {{ operadora.numero }} {{ operadora.complemento }} - {{ operadora.bairro }}
          </div>
          <div class="col-md-3">
            <strong>Cidade/UF:</strong> <br> {{ operadora.cidade }} / {{ operadora.uf }}
          </div>
          <div class="col-md-3">
            <strong>CEP:</strong> <br> {{ operadora.cep }}
          </div>
          
          <div class="col-12 border-top pt-2">
            <strong>Representante:</strong> {{ operadora.representante }} 
            <span class="text-muted">({{ operadora.cargo_representante }})</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card shadow-sm">
      <div class="card-header bg-white">
        <h5 class="mb-0 text-success">
          <i class="bi bi-cash-coin"></i> Histórico de Despesas
        </h5>
      </div>
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th>Ano</th>
                <th>Trimestre</th>
                <th class="text-end">Valor Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="despesa in despesas" :key="despesa.id">
                <td>{{ despesa.ano }}</td>
                <td>{{ despesa.trimestre }}º Trimestre</td>
                <td class="text-end fw-bold text-danger">
                  {{ formatarMoeda(despesa.valor_despesas) }}
                </td>
              </tr>
              <tr v-if="despesas.length === 0">
                <td colspan="3" class="text-center py-4 text-muted">
                  Nenhuma despesa registrada para esta operadora.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>