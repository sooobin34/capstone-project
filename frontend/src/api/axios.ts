import axios from 'axios'

const api = axios.create({
  baseURL: 'https://capstone-project-54l6.onrender.com',
  timeout: 10000,
})

export default api