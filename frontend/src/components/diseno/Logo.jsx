import { Link } from 'react-router-dom'

export default function Logo({ className = '' }) {
  return (
    <Link to="/" aria-label="Cosplay Chile, inicio" className={`inline-flex shrink-0 items-center gap-3 text-white no-underline ${className}`}>
      <span
        aria-hidden="true"
        className="inline-flex size-10 items-center justify-center rounded-full bg-[linear-gradient(135deg,#ff7a6b,#ff2fa0_60%,#7a2cff)] font-display text-[22px] font-extrabold text-white"
      >
        C
      </span>
      <span aria-hidden="true" className="font-display text-2xl font-bold tracking-[.01em]">Cosplay Chile</span>
    </Link>
  )
}
