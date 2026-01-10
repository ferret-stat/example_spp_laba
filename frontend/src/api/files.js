import api from "./api";

export const getFiles = async (
  page = 1,
  limit = 10,
  { sortBy = "last_modified", sortDir = "desc", tags = [] } = {}
) => {
  const params = new URLSearchParams();

  params.set("page", String(page));
  params.set("page_size", String(limit));

  if (sortBy) params.set("sort_by", sortBy);
  if (sortDir) params.set("sort_dir", sortDir);
  if (Array.isArray(tags) && tags.length > 0) {
    tags.forEach((t) => {
      if (t) params.append("tags", t);
    });
  }

  const res = await api.get(`/files/?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });

  return res.data;
};

export const getFileTags = async () => {
  const res = await api.get("/files/tags", {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  const arr = Array.isArray(res.data) ? res.data : [];
  return arr
    .map((x) => x?.name)
    .filter(Boolean)
    .sort((a, b) => String(a).localeCompare(String(b), "ru"));
};

export const downloadFile = (id) => {
  window.location.href = `/api/files/download/${id}`;
};
