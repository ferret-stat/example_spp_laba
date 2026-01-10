import api from "./api";
import axios from "axios";

export const getFiles = async (page = 1, limit = 5) => {
  const res = await axios.get(`/api/files/?page=${page}&page_size=${limit}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const downloadFile = (id) => {
  window.location.href = `/api/files/download/${id}`;
};
