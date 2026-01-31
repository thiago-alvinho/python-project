<script setup>

</script>

<template>
  <div class="d-flex flex-column flex-shrink-0 p-3 bg-body-tertiary border-end" style="width: 280px; min-height: 100vh;">
    
    <router-link to="/" class="d-flex align-items-center mb-3 mb-md-0 me-md-auto link-body-emphasis text-decoration-none">
      <i class="bi bi-h-circle-fill fs-4 me-2"></i>
      <span class="fs-4">Healthops</span>
    </router-link>
    
    <hr>
    
    <ul class="nav nav-pills flex-column mb-auto">
      <li class="nav-item">
        <router-link to="/" class="nav-link" aria-current="page">
          <i class="bi bi-house me-2"></i>
          Home
        </router-link>
      </li>
      <li>
        <router-link to="/operadoras" class="nav-link link-body-emphasis">
          <i class="bi bi-table me-2"></i>
          Operadoras
        </router-link>
      </li>
      <li>
        <router-link to="/estatisticas" class="nav-link link-body-emphasis">
          <i class="bi bi-bar-chart-line me-2"></i>
          Estatísticas
        </router-link>
      </li>
      
    </ul>
    
    <hr>
    <a href="https://www.linkedin.com/in/thiago-alves-da-silva-a62127223/">
    <i class="bi bi-linkedin"></i>
    </a>

  </div>
</template>