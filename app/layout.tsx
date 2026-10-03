import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Savior Made CHECK",
  description: "A simple Scripture-conscious message review assistant.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
