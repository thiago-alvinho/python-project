<script setup>
import Sidebar from './components/Sidebar.vue';
</script>

<template>
  <div class="d-flex min-vh-100 w-100">
    
    <Sidebar />

    <main class="flex-grow-1 bg-light">
      <div class="container-fluid p-4">
        <router-view />
      </div>
    </main>

  </div>
</template>

<style>
body { margin: 0; background-color: #f8f9fa; }
</style>