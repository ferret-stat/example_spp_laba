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

export const getMyFiles = async (
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

  const res = await api.get(`/files/my_books?${params.toString()}`, {
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

export const deleteFile = async (fileId) => {
  const res = await api.delete(`/files/${fileId}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const getAdminMe = async () => {
  const res = await api.get("/admin/me", {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const getUserStats = async () => {
  const res = await api.get("/admin/users/stats", {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const getAdminUsers = async (days = 7) => {
  const res = await api.get("/admin/users", {
    params: { days },
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const setUserActive = async (userId, isActive) => {
  const res = await api.patch(
    `/admin/users/${userId}/active`,
    { is_active: isActive },
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    }
  );
  return res.data;
};

export const getFileDescription = async (fileId) => {
  const res = await api.get(`/files/${fileId}/description`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const createFileDescription = async (fileId, payload) => {
  const res = await api.post(`/files/${fileId}/description`, payload, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const updateFileDescription = async (fileId, payload) => {
  const res = await api.patch(`/files/${fileId}/description`, payload, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const updateFileTags = async (fileId, tags) => {
  const res = await api.put(
    `/files/${fileId}/tags`,
    { tags },
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    }
  );
  return res.data;
};

export const getFileLike = async (fileId) => {
  const res = await api.get(`/files/${fileId}/like`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const toggleFileLike = async (fileId, isLike = true) => {
  const res = await api.post(
    `/files/${fileId}/like`,
    { is_like: isLike },
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    }
  );
  return res.data;
};

export const listFileComments = async (fileId, { limit = 50, offset = 0 } = {}) => {
  const res = await api.get(`/files/${fileId}/comments`, {
    params: { limit, offset },
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const createFileComment = async (fileId, payload) => {
  const res = await api.post(`/files/${fileId}/comments`, payload, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const updateFileComment = async (commentId, payload) => {
  const res = await api.patch(`/comments/${commentId}`, payload, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const deleteFileComment = async (commentId) => {
  const res = await api.delete(`/comments/${commentId}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const getCommentLike = async (commentId) => {
  const res = await api.get(`/comments/${commentId}/like`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.data;
};

export const toggleCommentLike = async (commentId, isLike = true) => {
  const res = await api.post(
    `/comments/${commentId}/like`,
    { is_like: isLike },
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    }
  );
  return res.data;
};

const normalizeToken = (t) => {
  if (!t) return "";
  return t.startsWith("Bearer ") ? t.slice(7) : t;
};

const getFilenameFromContentDisposition = (cd) => {
  if (!cd) return null;
  const mStar = cd.match(/filename\*\s*=\s*UTF-8''([^;]+)/i);
  if (mStar) {
    try {
      return decodeURIComponent(mStar[1]);
    } catch {
      return mStar[1];
    }
  }
  const m = cd.match(/filename\s*=\s*"([^"]+)"/i);
  if (m) return m[1];

  return null;
};

export const downloadFile = async (id, token) => {
  const pure = normalizeToken(token);

  const res = await fetch(`/api/files/download/${id}`, {
    headers: { Authorization: `Bearer ${pure}` },
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`Download failed: ${res.status} ${txt}`);
  }

  const cd = res.headers.get("content-disposition");
  const filename = getFilenameFromContentDisposition(cd) || id;

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();

  window.URL.revokeObjectURL(url);
};
