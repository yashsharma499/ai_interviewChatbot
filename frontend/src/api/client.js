import axios from "axios";

const client = axios.create({
  baseURL: "https://interview-scheduler-backend-67r8.onrender.com",
  headers: {
    "Content-Type": "application/json"
  }
});

export default client;
