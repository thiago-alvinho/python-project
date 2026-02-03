<script setup>
import { ref, onMounted } from 'vue';
import OperadoraService from '../services/OperadoraService';

import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement
} from 'chart.js';
import { Bar, Doughnut } from 'vue-chartjs';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

const loading = ref(true);
const stats = ref(null);

const chartTop5Data = ref(null);
const chartUFData = ref(null);

const barOptions = {
  responsive: true,
  plugins: {
    legend: { display: false },
    title: { display: true, text: 'Top 5 - Maiores Despesas' }
  }
};

const doughnutOptions = {
  responsive: true,
  plugins: {
    legend: { position: 'right' }
  }
};

const formatarMoeda = (valor) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
};

onMounted(async () => {
  try {
    const response = await OperadoraService.getEstatisticas();
    stats.value = response.data;

    // --- MONTAGEM DO GRÁFICO DE BARRAS (TOP 5) ---
    chartTop5Data.value = {
      labels: stats.value.top_5_operadoras.map(op => {
         // Corta nomes muito grandes para caber no gráfico
         return op.razao_social.length > 20 ? op.razao_social.substring(0, 20) + '...' : op.razao_social
      }),
      datasets: [{
        label: 'Valor Total (R$)',
        backgroundColor: '#0d6efd',
        data: stats.value.top_5_operadoras.map(op => op.valor_total)
      }]
    };

    // --- MONTAGEM DO GRÁFICO POR UF ---
    // os 5 maiores estados para o gráfico não ficar polúido
    const ufsPrincipais = stats.value.despesas_por_uf.slice(0, 5);
    // Restante como "Outros"
    const outrosTotal = stats.value.despesas_por_uf.slice(5).reduce((acc, curr) => acc + Number(curr.total), 0);
    
    const labelsUF = ufsPrincipais.map(u => u.uf);
    const dataUF = ufsPrincipais.map(u => u.total);
    
    if (outrosTotal > 0) {
        labelsUF.push('Outros');
        dataUF.push(outrosTotal);
    }

    chartUFData.value = {
      labels: labelsUF,
      datasets: [{
        backgroundColor: ['#198754', '#ffc107', '#0dcaf0', '#dc3545', '#6610f2', '#adb5bd'],
        data: dataUF
      }]
    };

  } catch (error) {
    console.error("Erro ao carregar estatísticas", error);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div v-if="loading" class="text-center py-5">
    <div class="spinner-border text-primary"></div>
  </div>

  <div v-else class="container-fluid">
    <h2 class="mb-4 text-primary"><i class="bi bi-bar-chart-line"></i> Dashboard Financeiro</h2>

    <div class="row g-4 mb-4">
      <div class="col-md-6">
        <div class="card shadow-sm border-start border-primary border-4">
          <div class="card-body">
            <h6 class="text-muted text-uppercase mb-2">Total de Despesas</h6>
            <h3 class="fw-bold text-primary">{{ formatarMoeda(stats.total_despesas) }}</h3>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card shadow-sm border-start border-success border-4">
          <div class="card-body">
            <h6 class="text-muted text-uppercase mb-2">Média por Operadora</h6>
            <h3 class="fw-bold text-success">{{ formatarMoeda(stats.media_despesas) }}</h3>
          </div>
        </div>
      </div>
    </div>

    <div class="row g-4">
      
      <div class="col-lg-8">
        <div class="card shadow-sm h-100">
          <div class="card-header bg-white font-weight-bold">
            Maiores Despesas por Operadora
          </div>
          <div class="card-body">
            <Bar v-if="chartTop5Data" :data="chartTop5Data" :options="barOptions" />
          </div>
        </div>
      </div>

      <div class="col-lg-4">
        <div class="card shadow-sm h-100">
          <div class="card-header bg-white font-weight-bold">
            Distribuição por Estado (UF)
          </div>
          <div class="card-body d-flex align-items-center justify-content-center">
            <div style="max-height: 300px; width: 100%;">
              <Doughnut v-if="chartUFData" :data="chartUFData" :options="doughnutOptions" />
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>