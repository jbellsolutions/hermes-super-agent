import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "agent-os",
  description: "One agent. One state. Every channel.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "ui-sans-serif, system-ui, sans-serif", margin: 0 }}>
        {children}
      </body>
    </html>
  );
}
