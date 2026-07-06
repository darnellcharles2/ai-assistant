import { checkMessage, formatCheckResult } from "@/lib/check-engine"

export const runtime = "nodejs"

export async function POST(request: Request) {
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

  const check = checkMessage(message)

  return Response.json({
    result: formatCheckResult(check),
    check,
    engine: "savior-made-rules-v1",
  })
}
