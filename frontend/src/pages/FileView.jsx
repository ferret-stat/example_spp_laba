import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import {
  createFileComment,
  getCommentLike,
  getFileDescription,
  getFileLike,
  listFileComments,
  toggleCommentLike,
  toggleFileLike,
} from "../api/files";
import api from "../api/api";
import "./files.css";

const formatDate = (iso) => {
  if (!iso) return "-";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "-";
  return d.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const formatSize = (bytes) => {
  if (bytes === null || bytes === undefined) return "-";
  const b = Number(bytes);
  if (Number.isNaN(b)) return "-";
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  if (b < 1024 * 1024 * 1024) return `${(b / (1024 * 1024)).toFixed(2)} MB`;
  return `${(b / (1024 * 1024 * 1024)).toFixed(2)} GB`;
};

const normalizeTags = (maybeTags) => {
  if (!maybeTags) return [];
  if (!Array.isArray(maybeTags)) return [];
  return maybeTags
    .map((t) => {
      if (typeof t === "string") return t;
      return t?.name ?? t?.tag ?? t?.value ?? "";
    })
    .filter(Boolean);
};

export default function FileView() {
  const { fileId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [file] = useState(location.state?.file ?? null);
  const isOwner = Boolean(location.state?.isOwner);
  const [description, setDescription] = useState("");
  const [fileLike, setFileLike] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [comments, setComments] = useState([]);
  const [commentLikes, setCommentLikes] = useState({});
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [commentBody, setCommentBody] = useState("");
  const [postingComment, setPostingComment] = useState(false);
  const [likeBusy, setLikeBusy] = useState(false);

  const displayName = useMemo(() => {
    const name = file?.object_name || "";
    if (!name) return `Файл ${fileId}`;
    return name.replace(/\.[^/.]+$/, "");
  }, [file?.object_name, fileId]);

  const tags = useMemo(() => normalizeTags(file?.tags), [file?.tags]);

  const loadDescription = useCallback(async () => {
    const data = await getFileDescription(fileId);
    setDescription(data?.description ?? "");
  }, [fileId]);

  const loadLike = useCallback(async () => {
    const res = await getFileLike(fileId);
    setFileLike(res?.my_like ?? null);
  }, [fileId]);

  const loadComments = useCallback(async () => {
    setCommentsLoading(true);
    try {
      const data = await listFileComments(fileId, { limit: 50, offset: 0 });
      setComments(Array.isArray(data) ? data : []);
    } finally {
      setCommentsLoading(false);
    }
  }, [fileId]);

  const loadCommentLikes = useCallback(async (list) => {
    if (!Array.isArray(list) || list.length === 0) return;
    const entries = await Promise.all(
      list.map(async (c) => {
        try {
          const res = await getCommentLike(c.id);
          return [c.id, res?.my_like ?? null];
        } catch {
          return [c.id, null];
        }
      })
    );
    setCommentLikes((prev) => {
      const next = { ...prev };
      entries.forEach(([id, val]) => {
        next[id] = val;
      });
      return next;
    });
  }, []);

  const loadFile = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      await Promise.all([loadDescription(), loadLike(), loadComments()]);
    } catch (e) {
      console.error("Failed to load file view", e);
      setError("Не удалось загрузить данные файла.");
    } finally {
      setLoading(false);
    }
  }, [loadComments, loadDescription, loadLike]);

  useEffect(() => {
    loadFile();
  }, [loadFile]);

  useEffect(() => {
    loadCommentLikes(comments);
  }, [comments, loadCommentLikes]);

  const handleDownload = async () => {
    if (!file?.id) return;
    try {
      const res = await api.get(`/files/download/${file.id}`, {
        responseType: "blob",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      const cd = res.headers?.["content-disposition"] || "";
      const match = cd.match(/filename\*?=(?:UTF-8''|")?([^";\n]+)"?/i);
      const filename = match
        ? decodeURIComponent(match[1])
        : file.object_name || "file";

      const url = window.URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Download failed", e);
      alert("Не удалось скачать файл.");
    }
  };

  const toggleLike = async () => {
    if (likeBusy) return;
    setLikeBusy(true);
    try {
      const res = await toggleFileLike(fileId, true);
      setFileLike(res?.my_like ?? null);
    } catch (e) {
      console.error("Like failed", e);
    } finally {
      setLikeBusy(false);
    }
  };

  const submitComment = async (e) => {
    e.preventDefault();
    const body = commentBody.trim();
    if (!body) return;
    setPostingComment(true);
    try {
      const res = await createFileComment(fileId, { body });
      setComments((prev) => [res, ...prev]);
      setCommentBody("");
    } catch (e) {
      console.error("Comment create failed", e);
      alert("Не удалось отправить комментарий.");
    } finally {
      setPostingComment(false);
    }
  };

  const toggleLikeComment = async (commentId) => {
    const prevLike = commentLikes[commentId] === true;
    try {
      const res = await toggleCommentLike(commentId, true);
      const nextLike = res?.my_like === true;
      setCommentLikes((prev) => ({ ...prev, [commentId]: res?.my_like ?? null }));
      if (prevLike !== nextLike) {
        setComments((prev) =>
          prev.map((c) => {
            if (c.id !== commentId) return c;
            const delta = (nextLike ? 1 : 0) - (prevLike ? 1 : 0);
            return { ...c, likes_count: Math.max(0, c.likes_count + delta) };
          })
        );
      }
    } catch (e) {
      console.error("Comment like failed", e);
    }
  };

  return (
    <div className="files-page">
      <div className="files-card file-card">
        <div className="file-header">
          <div>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => navigate(-1)}
            >
              Назад
            </button>
          </div>
          <div className="file-header-actions">
            <button className="btn btn-ghost" onClick={loadFile} disabled={loading}>
              Обновить
            </button>
            <button
              className={`btn ${fileLike ? "btn-primary" : "btn-ghost"}`}
              onClick={toggleLike}
              disabled={loading || likeBusy}
            >
              {fileLike ? "Нравится" : "Лайк"}
            </button>
          </div>
        </div>

        {error ? (
          <div className="state state-error">
            <div className="state-title">Что-то пошло не так</div>
            <div className="state-text">{error}</div>
            <button className="btn" onClick={loadFile} disabled={loading}>
              Повторить
            </button>
          </div>
        ) : loading ? (
          <div className="state">
            <div className="skeleton-line w-60" />
            <div className="skeleton-line w-80" />
            <div className="skeleton-table">
              <div className="skeleton-row" />
              <div className="skeleton-row" />
            </div>
          </div>
        ) : (
          <>
            <div className="file-hero">
              <div className="file-hero-info">
                <h2 className="file-title">{displayName}</h2>
                <div className="file-hero-meta">
                  <span>{formatSize(file?.size)}</span>
                  <span className="file-meta-sep">|</span>
                  <span>{formatDate(file?.last_modified)}</span>
                  {file?.author && (
                    <>
                      <span className="file-meta-sep">|</span>
                      <span>{file.author}</span>
                    </>
                  )}
                </div>
                {tags.length > 0 && (
                  <div className="tag-row">
                    {tags.map((tag) => (
                      <span key={tag} className="tag-pill">
                        <span className="tag-pill-text">{tag}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="file-hero-actions">
                <button
                  className="btn btn-primary"
                  onClick={handleDownload}
                  disabled={!file?.id}
                >
                  Скачать
                </button>
                {isOwner && (
                  <button
                    className="btn btn-ghost"
                    onClick={() =>
                      navigate(`/files/${fileId}/edit`, {
                        state: { file, isOwner: true },
                      })
                    }
                  >
                    Редактировать
                  </button>
                )}
              </div>
            </div>

            <div className="file-section">
              <h3 className="section-title">Описание</h3>
              {description ? (
                <p className="file-description">{description}</p>
              ) : (
                <div className="section-muted">Описание пока отсутствует.</div>
              )}
            </div>

            <div className="file-section">
              <div className="section-head">
                <h3 className="section-title">Комментарии</h3>
                <span className="section-muted">Всего: {comments.length}</span>
              </div>

              <form className="comment-form" onSubmit={submitComment}>
                <textarea
                  className="comment-textarea"
                  value={commentBody}
                  onChange={(e) => setCommentBody(e.target.value)}
                  placeholder="Напишите комментарий..."
                  rows={3}
                  disabled={postingComment}
                />
                <div className="comment-actions">
                  <button className="btn btn-primary" disabled={postingComment}>
                    Отправить
                  </button>
                </div>
              </form>

              {commentsLoading ? (
                <div className="state">
                  <div className="skeleton-line w-60" />
                  <div className="skeleton-line w-80" />
                </div>
              ) : comments.length === 0 ? (
                <div className="section-muted">Комментариев пока нет.</div>
              ) : (
                <div className="comment-list">
                  {comments.map((comment) => {
                    const liked = commentLikes[comment.id] === true;
                    return (
                      <div key={comment.id} className="comment-card">
                        <div className="comment-head">
                          <span className="comment-author">
                            {comment.author || "Аноним"}
                          </span>
                          <span className="comment-date">
                            {formatDate(comment.created_at)}
                          </span>
                        </div>
                        <div className="comment-body">{comment.body}</div>
                        <div className="comment-footer">
                          <button
                            type="button"
                            className={`btn btn-ghost ${liked ? "is-liked" : ""}`}
                            onClick={() => toggleLikeComment(comment.id)}
                          >
                            {liked ? "Нравится" : "Лайк"} | {comment.likes_count}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}



