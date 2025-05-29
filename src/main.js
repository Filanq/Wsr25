import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import Vuetify from 'vuetify/lib/framework'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.use(Vuetify)

app.mount('#app')
