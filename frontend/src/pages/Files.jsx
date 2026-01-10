import { useEffect, useMemo, useState } from "react";
import { getFiles, downloadFile } from "../api/files";
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

export default function Files() {
  const [files, setFiles] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const limit = 10;

  const canPrev = page > 1 && !loading;
  const canNext = page < totalPages && !loading;

  const pageTitle = useMemo(() => {
    if (loading) return "Загрузка…";
    if (error) return "Ошибка";
    return "Мои файлы";
  }, [loading, error]);

  const loadFiles = async (pageNumber) => {
    try {
      setError("");
      setLoading(true);
      const data = await getFiles(pageNumber, limit);
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
  };

  useEffect(() => {
    loadFiles(1);
  }, []);

  const handleDownload = async (id) => {
    try {
      await downloadFile(id);
    } catch (e) {
      console.error("Ошибка скачивания", e);
      alert("Не удалось скачать файл");
    }
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
              Управляйте файлами и скачивайте их в один клик
            </p>
          </div>

          <button
            className="btn btn-ghost"
            onClick={() => loadFiles(page)}
            disabled={loading}
            title="Обновить"
          >
            Обновить
          </button>
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
                  <th>Имя файла</th>
                  <th>Размер</th>
                  <th>Добавлен/Изменён</th>
                  <th className="th-actions">Действие</th>
                </tr>
              </thead>

              <tbody>
                {visibleFiles.map((file) => (
                  <tr key={file.id}>
                    <td>
                      <div className="file-cell">
                        <span className="file-dot" aria-hidden="true" />
                        <span className="file-name" title={file.object_name}>
                          {file.object_name}
                        </span>
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
                ))}
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
