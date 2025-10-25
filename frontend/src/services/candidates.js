import api from "./api";

export const fetchCandidateBoard = async () => {
  const response = await api.get("/candidates/board");
  return response.data;
};

export const updateCandidateStatus = async (candidateId, status) => {
  const response = await api.patch(`/candidates/${candidateId}/status`, { status });
  return response.data;
};

export const deleteCandidate = async (candidateId) => {
  const response = await api.delete(`/candidates/${candidateId}`);
  return response.data;
};

export const deleteCandidatesByStatus = async (status) => {
  const response = await api.delete("/candidates", { params: { status } });
  return response.data;
};
