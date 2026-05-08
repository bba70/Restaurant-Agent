import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/results',
      name: 'results',
      component: () => import('../views/ResultsView.vue'),
      beforeEnter: (to, _from, next) => {
        if (!to.query.q) {
          next({ name: 'home' })
        } else {
          next()
        }
      },
    },
  ],
})

export default router
