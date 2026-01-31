<script setup>

</script>

<template>
  <div class="px-4 py-5 my-5 text-center">
    <i class="bi bi-h-circle-fill text-primary d-block mx-auto mb-4" style="font-size: 4rem;"></i>
    
    <h1 class="display-5 fw-bold text-body-emphasis">Bem-vindo ao Healthops</h1>
    <div class="col-lg-6 mx-auto">
      <p class="lead mb-4">
        Gerencie operadoras de planos de saúde, visualize estatísticas e acompanhe despesas 
        de forma rápida e intuitiva. O sistema utiliza a API da ANS para fornecer dados atualizados.
      </p>
      <div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
        <router-link to="/operadoras" class="btn btn-primary btn-lg px-4 gap-3">
          Ver Operadoras
        </router-link>
      </div>
    </div>
  </div>
</template>