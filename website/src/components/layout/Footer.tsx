import { Link } from 'react-router-dom'

const footerLinks = {
  Produit: [
    { label: 'Fonctionnalités', to: '/fonctionnalites' },
    { label: 'Comment ça marche', to: '/comment-ca-marche' },
    { label: 'Télécharger', to: '/telecharger' },
  ],
  Support: [
    { label: 'FAQ', to: '/faq' },
    { label: 'À propos', to: '/a-propos' },
  ],
}

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="sm:col-span-2 lg:col-span-2">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-800 text-xs font-extrabold text-brand-300">
                FB
              </div>
              <span className="text-lg font-bold text-slate-900">
                Flexi<span className="text-brand-600">Beam</span>
              </span>
            </Link>
            <p className="mt-3 max-w-md text-sm leading-relaxed text-slate-500">
              Application de dimensionnement et de vérification des poutres en
              béton armé. Flexion, sollicitations, effort tranchant, fissuration
              et visualisation 2D/3D — dans une seule interface.
            </p>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h4 className="text-sm font-semibold text-slate-900">{title}</h4>
              <ul className="mt-3 space-y-2">
                {links.map((l) => (
                  <li key={l.to}>
                    <Link
                      to={l.to}
                      className="text-sm text-slate-500 transition-colors hover:text-brand-600"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 border-t border-slate-100 pt-6 text-center text-xs text-slate-400">
          © {new Date().getFullYear()} FlexiBeam. Projet de génie civil.
        </div>
      </div>
    </footer>
  )
}
