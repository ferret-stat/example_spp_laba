import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import {
  createFileDescription,
  getFileDescription,
  getFileTags,
  updateFileDescription,
  updateFileTags,
} from "../api/files";
import "./files.css";

const normalizeTag = (tag) => tag.trim().toLowerCase();

export default function FileEdit() {
  const { fileId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const file = location.state?.file ?? null;
  const isOwner = Boolean(location.state?.isOwner);

  const [description, setDescription] = useState("");
  const [tags, setTags] = useState(() => {
    const raw = file?.tags ?? [];
    if (!Array.isArray(raw)) return [];
    return raw.map((t) => String(t));
  });
  const [tagInput, setTagInput] = useState("");
  const [availableTags, setAvailableTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  const displayName = useMemo(() => {
    const name = file?.object_name || "";
    if (!name) return `Файл ${fileId}`;
    return name.replace(/\.[^/.]+$/, "");
  }, [file?.object_name, fileId]);

  const normalizedTags = useMemo(() => {
    return tags
      .map((t) => normalizeTag(t))
      .filter(Boolean)
      .filter((t, idx, arr) => arr.indexOf(t) === idx);
  }, [tags]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [page, allTags] = await Promise.all([
        getFileDescription(fileId),
        getFileTags(),
      ]);
      setDescription(page?.description ?? "");
      setAvailableTags(allTags ?? []);
    } catch (e) {
      console.error("Failed to load edit data", e);
      setError("Не удалось загрузить данные файла.");
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const addTag = (tag) => {
    const next = normalizeTag(tag);
    if (!next) return;
    setTags((prev) => {
      if (prev.some((t) => normalizeTag(t) === next)) return prev;
      return [...prev, next];
    });
  };

  const removeTag = (tag) => {
    setTags((prev) => prev.filter((t) => normalizeTag(t) !== normalizeTag(tag)));
  };

  const onTagKeyDown = (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      if (tagInput.trim()) {
        addTag(tagInput);
        setTagInput("");
      }
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    setError("");
    try {
      try {
        await updateFileDescription(fileId, { description });
      } catch (err) {
        if (err?.response?.status === 404) {
          await createFileDescription(fileId, { description });
        } else {
          throw err;
        }
      }
      await updateFileTags(fileId, normalizedTags);
      setSaved(true);
    } catch (e) {
      console.error("Save failed", e);
      setError("Не удалось сохранить изменения.");
    } finally {
      setSaving(false);
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
            <button
              className="btn btn-ghost"
              onClick={loadData}
              disabled={loading}
            >
              Обновить
            </button>
            <button
              className="btn btn-primary"
              onClick={handleSave}
              disabled={loading || saving || !isOwner}
            >
              {saving ? "Сохранение..." : "Сохранить"}
            </button>
          </div>
        </div>

        <div className="file-hero">
          <div className="file-hero-info">
            <h2 className="file-title">{displayName}</h2>
            <div className="file-hero-meta">
              <span>Редактирование описания и тегов</span>
            </div>
          </div>
        </div>

        {error && (
          <div className="state state-error">
            <div className="state-title">Что-то пошло не так</div>
            <div className="state-text">{error}</div>
          </div>
        )}

        {saved && !saving && !error && (
          <div className="state">
            <div className="state-title">Сохранено</div>
            <div className="state-text">Изменения применены.</div>
          </div>
        )}

        {!isOwner && (
          <div className="state state-error">
            <div className="state-title">Нет доступа</div>
            <div className="state-text">
              Редактирование доступно только владельцу файла.
            </div>
          </div>
        )}

        <div className="file-section">
          <h3 className="section-title">Описание</h3>
          <textarea
            className="comment-textarea"
            rows={6}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Добавьте описание..."
            disabled={loading || !isOwner}
          />
        </div>

        <div className="file-section">
          <h3 className="section-title">Теги</h3>
          <div className="tag-editor">
            <div className="tag-input-row">
              <input
                className="tag-input"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={onTagKeyDown}
                placeholder="Введите тег и нажмите Enter"
                disabled={loading || !isOwner}
              />
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  if (tagInput.trim()) {
                    addTag(tagInput);
                    setTagInput("");
                  }
                }}
                disabled={loading || !isOwner}
              >
                Добавить
              </button>
            </div>

            <div className="tag-row">
              {normalizedTags.length === 0 ? (
                <span className="section-muted">Теги не выбраны.</span>
              ) : (
                normalizedTags.map((tag) => (
                  <span key={tag} className="tag-pill">
                    <span className="tag-pill-text">{tag}</span>
                    <button
                      type="button"
                      className="tag-pill-x"
                      onClick={() => removeTag(tag)}
                      aria-label={`Удалить ${tag}`}
                      disabled={!isOwner}
                    >
                      x
                    </button>
                  </span>
                ))
              )}
            </div>

            {availableTags.length > 0 && (
              <div className="tag-suggestions">
                <div className="section-muted">Рекомендуемые</div>
                <div className="tag-row">
                  {availableTags
                    .filter((t) => !normalizedTags.includes(normalizeTag(t)))
                    .slice(0, 12)
                    .map((tag) => (
                      <button
                        key={tag}
                        type="button"
                        className="btn btn-ghost btn-chip"
                        onClick={() => addTag(tag)}
                        disabled={loading || !isOwner}
                      >
                        {tag}
                      </button>
                    ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
