// Renderiza texto plano con párrafos, títulos («## ») y listas («- ») sin usar HTML crudo (evita XSS).
export default function TextoRico({ texto = '', className = '' }) {
  const bloques = texto.split(/\n\s*\n/).map((b) => b.trim()).filter(Boolean)
  return (
    <div className={`prosa ${className}`}>
      {bloques.map((b, i) => {
        if (b.startsWith('## ')) return <h2 key={i}>{b.slice(3)}</h2>
        const lineas = b.split('\n')
        if (lineas.every((l) => l.trim().startsWith('- '))) {
          return (
            <ul key={i}>
              {lineas.map((l, j) => <li key={j}>{l.trim().slice(2)}</li>)}
            </ul>
          )
        }
        return <p key={i} className="whitespace-pre-line">{b}</p>
      })}
    </div>
  )
}
