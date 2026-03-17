import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import type { FAQItem } from '../../data/faq'

export default function FAQAccordion({ items }: { items: FAQItem[] }) {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  return (
    <div className="divide-y divide-slate-200 rounded-2xl border border-slate-200 bg-white">
      {items.map((item, i) => (
        <div key={i}>
          <button
            onClick={() => setOpenIndex(openIndex === i ? null : i)}
            className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left transition-colors hover:bg-slate-50"
          >
            <span className="font-semibold text-slate-900">{item.question}</span>
            <ChevronDown
              className={`h-5 w-5 flex-shrink-0 text-slate-400 transition-transform duration-200 ${
                openIndex === i ? 'rotate-180' : ''
              }`}
            />
          </button>
          <div
            className={`overflow-hidden transition-all duration-300 ${
              openIndex === i ? 'max-h-96 pb-5' : 'max-h-0'
            }`}
          >
            <p className="px-6 text-slate-600 leading-relaxed">{item.answer}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
