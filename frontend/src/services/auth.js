import api from "./api";

export async function login(email, password) {
  const response = await api.post("/auth/login", { email, password });
  const { access_token, user } = response.data;
  localStorage.setItem("smarthire_token", access_token);
  localStorage.setItem("smarthire_user", JSON.stringify(user));
  return user;
}

export function logout() {
  localStorage.removeItem("smarthire_token");
  localStorage.removeItem("smarthire_user");
}

export function getCurrentUser() {
  const user = localStorage.getItem("smarthire_user");
  return user ? JSON.parse(user) : null;
}
