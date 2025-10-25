import api from "./api";

export async function listRecruiters() {
  const response = await api.get("/admin/users");
  return response.data;
}

export async function createRecruiter({ email, password, name }) {
  const response = await api.post("/admin/users", { email, password, name });
  return response.data;
}

export async function deleteRecruiter(email) {
  await api.delete(`/admin/users/${encodeURIComponent(email)}`);
}
