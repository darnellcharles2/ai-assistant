"use client"

import { FormEvent, useMemo, useState } from "react"

type CheckState = "idle" | "loading" | "done" | "error"

const examples = [
  "I want my words to build people up and give grace.",
  "God will definitely make me rich if I post this.",
  "I think God may be teaching me to trust Him this season.",
]

export default function Home() {
  const [message, setMessage] = useState("")
  const [result, setResult] = useState("")
  const [error, setError] = useState("")
  const [state, setState] = useState<CheckState>("idle")

  const remaining = useMemo(() => 5000 - message.length, [message])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setResult("")

    if (!message.trim()) {
      setError("Paste a message first.")
      setState("error")
      return
    }

    setState("loading")

    try {
      const response = await fetch("/api/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || "Something went wrong.")
      }

      setResult(data.result)
      setState("done")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong.")
      setState("error")
    }
  }

  return (
    <main className="shell">
      <section className="topbar" aria-label="Savior Made CHECK">
        <div className="mark" aria-hidden="true">
          <span />
        </div>
        <div>
          <p className="eyebrow">Savior Made CHECK</p>
          <h1>Bring the words back to the Cross.</h1>
        </div>
        <p className="costBadge">Free rule-based engine</p>
      </section>

      <section className="workspace" aria-label="Message checker">
        <form className="composer" onSubmit={handleSubmit}>
          <div className="sectionHeader">
            <label htmlFor="message">Message to review</label>
            <span>No AI cost per check</span>
          </div>
          <textarea
            id="message"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            maxLength={5000}
            placeholder="Paste the post, caption, comment, testimony, lyric, or announcement..."
          />

          <div className="composerFooter">
            <span className={remaining < 300 ? "limit warning" : "limit"}>
              {remaining.toLocaleString()} characters left
            </span>
            <button type="submit" disabled={state === "loading"}>
              {state === "loading" ? "Checking..." : "Check Message"}
            </button>
          </div>
        </form>

        <aside className="examples" aria-label="Examples">
          <h2>Quick Tests</h2>
          {examples.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => {
                setMessage(example)
                setResult("")
                setError("")
                setState("idle")
              }}
            >
              {example}
            </button>
          ))}
          <div className="legend" aria-label="CHECK status legend">
            <span><b>Green</b> Aligned</span>
            <span><b>Yellow</b> Discern</span>
            <span><b>Blue</b> Counsel</span>
            <span><b>Red</b> Hold</span>
          </div>
        </aside>
      </section>

      <section className="resultPanel" aria-live="polite">
        {state === "idle" && (
          <div className="empty">
            <h2>Ready when you are.</h2>
            <p>The check runs from your own SAVIOR / MADE / CHECK rules, so the free product does not burn paid AI tokens.</p>
          </div>
        )}

        {state === "loading" && (
          <div className="empty">
            <h2>Checking the message...</h2>
            <p>Reviewing wording, risk, clarity, counsel triggers, and release guidance.</p>
          </div>
        )}

        {state === "error" && (
          <div className="error">
            <h2>Could not check the message.</h2>
            <p>{error}</p>
          </div>
        )}

        {state === "done" && <pre className="result">{result}</pre>}
      </section>
    </main>
  )
}
