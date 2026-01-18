import "./home.css";

export default function Home() {
  return (
    <div className="home-page">
      <section className="home-hero">
        <div className="home-content">
          <span className="home-kicker">Добро пожаловать!</span>
          <h1 className="home-title">Хранилище книг и учебных материалов</h1>
          <p className="home-text">
            Загружайте, сортируйте и обсуждайте файлы. Добавляйте теги,
            оставляйте комментарии и следите за популярностью материалов. Проект
            сделан в качестве курсовой работы Божедонов И.В. группы 0ВМ42
          </p>
          <div className="home-actions">
            <span className="home-note">
              Войдите в аккаунт, чтобы получить доступ к файлам.
            </span>
          </div>
        </div>
        <div className="home-card">
          <div className="home-card-title">Возможности</div>
          <ul className="home-list">
            <li>Быстрый поиск и фильтрация по тегам</li>
            <li>Просмотр описаний и обсуждений</li>
            <li>Сортировка по дате, размеру и лайкам</li>
            <li>Удобное управление своими файлами</li>
          </ul>
        </div>
      </section>
    </div>
  );
}
