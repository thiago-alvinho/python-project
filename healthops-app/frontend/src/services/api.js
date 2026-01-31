import axios from 'axios';

// Cria uma instância do Axios com o endereço do backend
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
});

export default api;