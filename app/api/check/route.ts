import { SAVIOR_MADE_SYSTEM_PROMPT } from "@/lib/savior-made-prompt"

export const runtime = "nodejs"

type OpenAIResponse = {
  output_text?: string
  output?: Array<{
    content?: Array<{
      text?: string
      type?: string
    }>
  }>
  error?: {
    message?: string
  }
}

function extractText(data: OpenAIResponse) {
  if (data.output_text) return data.output_text

  return (
    data.output
      ?.flatMap((item) => item.content ?? [])
      .map((content) => content.text)
      .filter(Boolean)
      .join("\n")
      .trim() ?? ""
  )
}

export async function POST(request: Request) {
  const apiKey = process.env.OPENAI_API_KEY

  if (!apiKey) {
    return Response.json(
      { error: "OPENAI_API_KEY is not configured on the server." },
      { status: 500 },
    )
  }

  const body = await request.json().catch(() => null)
  const message = typeof body?.message === "string" ? body.message.trim() : ""

  if (!message) {
    return Response.json({ error: "Please paste a message to check." }, { status: 400 })
  }

  if (message.length > 5000) {
    return Response.json(
      { error: "Please keep the message under 5,000 characters." },
      { status: 400 },
    )
  }

  const model = process.env.OPENAI_MODEL || "gpt-4.1-mini"

  const response = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
      temperature: 0.2,
      max_output_tokens: 900,
      input: [
        {
          role: "system",
          content: SAVIOR_MADE_SYSTEM_PROMPT,
        },
        {
          role: "user",
          content: `Review this message:\n\n${message}`,
        },
      ],
    }),
  })

  const data = (await response.json().catch(() => ({}))) as OpenAIResponse

  if (!response.ok) {
    const message = data.error?.message || "The AI review could not be completed."
    const friendlyQuotaMessage =
      "The AI connection is set up, but this OpenAI project has no available quota or billing credits yet. Add billing or credits in OpenAI Platform, then try again."

    return Response.json(
      { error: message.toLowerCase().includes("quota") ? friendlyQuotaMessage : message },
      { status: response.status },
    )
  }

  const result = extractText(data)

  if (!result) {
    return Response.json(
      { error: "The AI review returned an empty result." },
      { status: 502 },
    )
  }

  return Response.json({ result })
}
