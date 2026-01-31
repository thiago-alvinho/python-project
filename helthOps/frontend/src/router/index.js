import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import OperadorasView from '../views/OperadorasView.vue'
import OperadoraDetalhesView from '../views/OperadoraDetalhesView.vue'
import EstatisticasView from '../views/EstatisticasView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/operadoras',
      name: 'operadoras',
      component: OperadorasView
    },
    { 
      path: '/operadoras/:registro',
      name: 'operadora-detalhes', 
      component: OperadoraDetalhesView,
      props: true
    },
    {
      path: '/estatisticas',
      name: 'estatisticas',
      component: EstatisticasView
    }

  ],
  linkActiveClass: 'active' 
})

export default router