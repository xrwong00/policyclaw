import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PolicyClaw",
  description: "Insurance decision intelligence MVP",
  icons: {
    icon: [
      {
        url: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%23c84f33'/><text x='50%25' y='54%25' font-family='Georgia,serif' font-size='20' font-weight='700' fill='%23fff' text-anchor='middle' dominant-baseline='middle'>P</text></svg>",
        type: "image/svg+xml",
      },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
