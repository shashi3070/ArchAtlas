import type { ReactNode } from 'react'

/**
 * Minimal markdown renderer for lesson sections: headings, unordered/ordered
 * lists, fenced code blocks, bold and inline code. Deliberately tiny - rich
 * authoring belongs to the content pipeline later, not the runtime.
 */

function renderInline(text: string): ReactNode[] {
  const parts: ReactNode[] = []
  // Split on **bold** and `code` while keeping delimiters.
  const regex = /(\*\*[^*]+\*\*|`[^`]+`)/g
  let last = 0
  let match: RegExpExecArray | null
  let key = 0
  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index))
    const token = match[0]
    if (token.startsWith('**')) {
      parts.push(<strong key={key++}>{token.slice(2, -2)}</strong>)
    } else {
      parts.push(<code key={key++}>{token.slice(1, -1)}</code>)
    }
    last = match.index + token.length
  }
  if (last < text.length) parts.push(text.slice(last))
  return parts
}

export function Markdown({ source }: { source: string }) {
  const lines = source.split('\n')
  const blocks: ReactNode[] = []
  let i = 0
  let key = 0

  while (i < lines.length) {
    const line = lines[i]

    if (line.startsWith('```')) {
      const code: string[] = []
      i++
      while (i < lines.length && !lines[i].startsWith('```')) {
        code.push(lines[i])
        i++
      }
      i++ // closing fence
      blocks.push(
        <pre key={key++}>
          <code>{code.join('\n')}</code>
        </pre>,
      )
      continue
    }

    if (/^#{1,3}\s/.test(line)) {
      const level = line.match(/^#+/)![0].length
      const content = line.replace(/^#+\s*/, '')
      const Tag = (`h${level + 1}` as unknown) as 'h2'
      blocks.push(<Tag key={key++}>{renderInline(content)}</Tag>)
      i++
      continue
    }

    if (/^\s*[-*]\s/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^\s*[-*]\s/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s/, ''))
        i++
      }
      blocks.push(
        <ul key={key++}>
          {items.map((item, idx) => (
            <li key={idx}>{renderInline(item)}</li>
          ))}
        </ul>,
      )
      continue
    }

    if (/^\s*\d+\.\s/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^\s*\d+\.\s/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s/, ''))
        i++
      }
      blocks.push(
        <ol key={key++}>
          {items.map((item, idx) => (
            <li key={idx}>{renderInline(item)}</li>
          ))}
        </ol>,
      )
      continue
    }

    if (line.trim() === '') {
      i++
      continue
    }

    // Paragraph until blank line.
    const para: string[] = []
    while (i < lines.length && lines[i].trim() !== '' && !/^(```|#{1,3}\s|\s*[-*]\s|\s*\d+\.\s)/.test(lines[i])) {
      para.push(lines[i])
      i++
    }
    blocks.push(<p key={key++}>{renderInline(para.join(' '))}</p>)
  }

  return <div className="markdown">{blocks}</div>
}
