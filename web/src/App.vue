<script setup lang="ts">
import { NConfigProvider, NMessageProvider } from 'naive-ui'
import { RouterView } from 'vue-router'
import AppProvider from './components/AppProvider.vue'

const themeOverrides = {
  common: {
    primaryColor: '#f97316',
    primaryColorHover: '#fb923c',
    primaryColorPressed: '#ea580c',
    primaryColorSuppl: '#fdba74',
  },
}
</script>

<template>
  <NConfigProvider :theme-overrides="themeOverrides">
    <NMessageProvider>
      <AppProvider>
        <RouterView v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </AppProvider>
    </NMessageProvider>
  </NConfigProvider>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
