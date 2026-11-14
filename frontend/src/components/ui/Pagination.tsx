interface PaginationProps {
  page: number;
  pageCount: number;
  totalItems: number;
  pageSize: number;
  label: string;
  onPageChange: (page: number) => void;
}

export function Pagination({
  page,
  pageCount,
  totalItems,
  pageSize,
  label,
  onPageChange,
}: PaginationProps) {
  if (totalItems === 0) return null;

  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalItems);
  const pages = Array.from({ length: pageCount }, (_, index) => index + 1);

  return (
    <nav className="pagination" aria-label={`Paginación de ${label}`}>
      <span>
        Mostrando{" "}
        <strong>
          {start}–{end}
        </strong>{" "}
        de <strong>{totalItems}</strong> {label}
      </span>
      <div>
        <button
          type="button"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page === 1}
        >
          Anterior
        </button>
        {pages.map((number) => (
          <button
            type="button"
            className={page === number ? "current" : ""}
            onClick={() => onPageChange(number)}
            aria-current={page === number ? "page" : undefined}
            aria-label={`Página ${number}`}
            key={number}
          >
            {number}
          </button>
        ))}
        <button
          type="button"
          onClick={() => onPageChange(Math.min(pageCount, page + 1))}
          disabled={page === pageCount}
        >
          Siguiente
        </button>
      </div>
    </nav>
  );
}
