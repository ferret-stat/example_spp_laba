import { useCallback, useEffect, useMemo, useState } from "react";
import { getFiles, downloadFile } from "../api/files";
import api from "../api/api";
import "./files.css";

const formatSize = (bytes) => {
  if (bytes === null || bytes === undefined) return "—";
  const b = Number(bytes);
  if (Number.isNaN(b)) return "—";

  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  if (b < 1024 * 1024 * 1024) return `${(b / (1024 * 1024)).toFixed(2)} MB`;
  return `${(b / (1024 * 1024 * 1024)).toFixed(2)} GB`;
};

const formatDate = (iso) => {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";

  return d.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
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

function SortSelect({ value, onChange, disabled }) {
  const [open, setOpen] = useState(false);

  const options = [
    { value: "last_modified", label: "Дате" },
    { value: "object_name", label: "Имени" },
    { value: "size", label: "Размеру" },
  ];

  const current = options.find((o) => o.value === value) ?? options[0];

  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    const onClickOutside = (e) => {
      if (!e.target.closest?.(".sort-dd")) setOpen(false);
    };
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("mousedown", onClickOutside);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("mousedown", onClickOutside);
    };
  }, []);

  return (
    <div className="sort-dd">
      <button
        type="button"
        className="btn btn-ghost sort-dd-btn"
        onClick={() => setOpen((v) => !v)}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        {current.label}
        <span
          className={`sort-dd-caret ${open ? "is-open" : ""}`}
          aria-hidden="true"
        >
          ▾
        </span>
      </button>

      {open && !disabled && (
        <div
          className="sort-dd-menu"
          role="listbox"
          aria-label="Сортировать по"
        >
          {options.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`sort-dd-item ${
                opt.value === value ? "is-active" : ""
              }`}
              onClick={() => {
                onChange(opt.value);
                setOpen(false);
              }}
              role="option"
              aria-selected={opt.value === value}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function TagsMultiSelect({
  options,
  value,
  onChange,
  disabled,
  placeholder,
  onOpen,
}) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");

  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    const onClickOutside = (e) => {
      if (!e.target.closest?.(".tags-dd")) setOpen(false);
    };
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("mousedown", onClickOutside);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("mousedown", onClickOutside);
    };
  }, []);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return options;
    return options.filter((t) => String(t).toLowerCase().includes(s));
  }, [options, q]);

  const toggle = (tag) => {
    if (value.includes(tag)) onChange(value.filter((x) => x !== tag));
    else onChange([...value, tag]);
  };

  const clear = () => onChange([]);

  const buttonText =
    value.length > 0 ? `Выбрано: ${value.length}` : placeholder;

  return (
    <div className="tags-dd">
      <button
        type="button"
        className="btn btn-ghost tags-dd-btn"
        onClick={() => {
          setOpen((v) => {
            const next = !v;
            if (next && onOpen) onOpen();
            return next;
          });
        }}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        {buttonText}
        <span
          className={`tags-dd-caret ${open ? "is-open" : ""}`}
          aria-hidden="true"
        >
          ▾
        </span>
      </button>

      {open && !disabled && (
        <div className="tags-dd-menu" role="listbox" aria-label="Теги">
          <div className="tags-dd-top">
            <input
              className="tags-dd-search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Поиск по тегам…"
              autoFocus
            />
            <button
              type="button"
              className="btn btn-ghost tags-dd-clear"
              onClick={clear}
              disabled={value.length === 0}
              title="Сбросить"
            >
              Сбросить
            </button>
          </div>

          <div className="tags-dd-list">
            {filtered.length === 0 ? (
              <div className="tags-dd-empty">Ничего не найдено</div>
            ) : (
              filtered.map((tag) => {
                const checked = value.includes(tag);
                return (
                  <button
                    key={tag}
                    type="button"
                    className={`tags-dd-item ${checked ? "is-active" : ""}`}
                    onClick={() => toggle(tag)}
                    role="option"
                    aria-selected={checked}
                  >
                    <span className="tags-dd-check" aria-hidden="true">
                      {checked ? "✓" : ""}
                    </span>
                    <span className="tags-dd-text">{tag}</span>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Files() {
  const [files, setFiles] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [sortBy, setSortBy] = useState("last_modified");
  const [sortDir, setSortDir] = useState("desc");

  const [selectedTags, setSelectedTags] = useState([]);

  const [availableTags, setAvailableTags] = useState([]);
  const [tagsLoading, setTagsLoading] = useState(false);

  const limit = 10;

  const canPrev = page > 1 && !loading;
  const canNext = page < totalPages && !loading;

  const pageTitle = useMemo(() => {
    if (loading) return "Загрузка…";
    if (error) return "Ошибка";
    return "Библиотека";
  }, [loading, error]);

  const removeTag = (tag) => {
    setSelectedTags((prev) => prev.filter((t) => t !== tag));
  };

  const loadFiles = useCallback(
    async (pageNumber) => {
      try {
        setError("");
        setLoading(true);

        const data = await getFiles(pageNumber, limit, {
          sortBy,
          sortDir,
          tags: selectedTags,
        });

        const list = data.files ?? [];
        setFiles(list);
        setTotal(data.total ?? 0);
        setPage(data.page ?? pageNumber);
        setTotalPages(data.pages ?? 1);
      } catch (e) {
        console.error("Ошибка загрузки файлов", e);
        setError("Не удалось загрузить файлы. Попробуйте ещё раз.");
      } finally {
        setLoading(false);
      }
    },
    [limit, sortBy, sortDir, selectedTags]
  );

  useEffect(() => {
    loadFiles(1);
  }, [loadFiles]);

  const loadTags = useCallback(async () => {
    try {
      setTagsLoading(true);

      const res = await api.get("/files/tags", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      const data = res.data;

      let tags = [];
      if (Array.isArray(data)) {
        tags = data.map((x) => x?.name).filter(Boolean);
      }

      tags = Array.from(new Set(tags)).sort((a, b) =>
        String(a).localeCompare(String(b), "ru")
      );

      setAvailableTags(tags);
      setSelectedTags((prev) => prev.filter((t) => tags.includes(t)));
    } catch (e) {
      console.error("Ошибка загрузки тегов", e);
      setAvailableTags([]);
    } finally {
      setTagsLoading(false);
    }
  }, []);

  const handleDownload = async (id) => {
    const token = localStorage.getItem("token");
    try {
      await downloadFile(id, token);
    } catch (e) {
      console.error("Ошибка скачивания", e);
      alert("Не удалось скачать файл");
    }
  };

  const toggleSortDir = () => {
    setSortDir((prev) => (prev === "desc" ? "asc" : "desc"));
  };

  const visibleFiles = useMemo(() => files.slice(0, limit), [files, limit]);
  const from = total === 0 ? 0 : (page - 1) * limit + 1;
  const to =
    total === 0 ? 0 : Math.min((page - 1) * limit + visibleFiles.length, total);

  return (
    <div className="files-page">
      <div className="files-card">
        <div className="files-header">
          <div>
            <h2 className="files-title">{pageTitle}</h2>
            <p className="files-subtitle">
              Скачивайте файлы в один клик из нашей библиотеки!
            </p>
          </div>

          <div className="files-actions">
            <div className="sort-control">
              <span className="sort-label">Сортировать по: </span>
              <SortSelect
                value={sortBy}
                onChange={setSortBy}
                disabled={loading}
              />
            </div>

            <button
              className="btn btn-ghost"
              onClick={toggleSortDir}
              disabled={loading}
              title="Направление сортировки"
            >
              {sortDir === "desc" ? "По убыванию" : "По возрастанию"}
            </button>

            <button
              className="btn btn-ghost"
              onClick={() => loadFiles(page)}
              disabled={loading}
              title="Обновить"
            >
              Обновить
            </button>
          </div>
        </div>

        <div className="files-filters">
          <div className="filters-title">Теги:</div>

          <div className="filters-row">
            <TagsMultiSelect
              options={availableTags}
              value={selectedTags}
              onChange={setSelectedTags}
              disabled={loading || tagsLoading}
              placeholder={tagsLoading ? "Загрузка…" : "Выберите теги"}
              onOpen={loadTags}
            />

            <div className="selected-tags">
              {selectedTags.map((tag) => (
                <span key={tag} className="tag-pill">
                  <span className="tag-pill-text">{tag}</span>
                  <button
                    type="button"
                    className="tag-pill-x"
                    onClick={() => removeTag(tag)}
                    disabled={loading}
                    aria-label={`Убрать тег ${tag}`}
                    title="Убрать"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>

        {error ? (
          <div className="state state-error">
            <div className="state-title">Что-то пошло не так</div>
            <div className="state-text">{error}</div>
            <button
              className="btn"
              onClick={() => loadFiles(page)}
              disabled={loading}
            >
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
              <div className="skeleton-row" />
            </div>
          </div>
        ) : visibleFiles.length === 0 ? (
          <div className="state">
            <div className="state-title">Файлов пока нет</div>
            <div className="state-text">
              Здесь появятся ваши загруженные файлы.
            </div>
          </div>
        ) : (
          <div className="table-wrap">
            <table className="files-table">
              <thead>
                <tr>
                  <th>Книга</th>
                  <th>Размер</th>
                  <th>Добавлен/Изменён</th>
                  <th className="th-actions">Действие</th>
                </tr>
              </thead>

              <tbody>
                {visibleFiles.map((file) => {
                  const tags = normalizeTags(
                    file.tags ?? file.file_tags ?? file.tag_names
                  );
                  return (
                    <tr key={file.id}>
                      <td>
                        <div className="file-cell">
                          <span className="file-dot" aria-hidden="true" />
                          <div className="file-info">
                            <span
                              className="file-name"
                              title={file.object_name}
                            >
                              {file.object_name}
                            </span>
                            {tags.length > 0 && (
                              <span
                                className="file-tags"
                                title={tags.join(", ")}
                              >
                                {tags.join(", ")}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>

                      <td className="file-meta">{formatSize(file.size)}</td>
                      <td className="file-meta">
                        {formatDate(file.last_modified)}
                      </td>

                      <td className="td-actions">
                        <button
                          className="btn btn-primary"
                          onClick={() => handleDownload(file.id)}
                        >
                          Скачать
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <div className="files-footer">
          <div className="pagination">
            <button
              className="btn btn-ghost"
              disabled={!canPrev}
              onClick={() => loadFiles(page - 1)}
            >
              Назад
            </button>

            <div className="page-indicator">
              <span className="page-pill">{page}</span>
              <span className="page-sep">/</span>
              <span className="page-muted">{totalPages}</span>
            </div>

            <button
              className="btn btn-ghost"
              disabled={!canNext}
              onClick={() => loadFiles(page + 1)}
            >
              Вперёд
            </button>
          </div>

          <div className="hint">
            {total > 0 ? `Показано: ${from}–${to} из ${total}` : ""}
          </div>
        </div>
      </div>
    </div>
  );
}
