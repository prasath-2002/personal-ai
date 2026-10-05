import type { Metadata } from "next";
import "./globals.css";


export const metadata: Metadata = {
  title: "Personal AI",
  description: "Your personal assistant for conversations and document questions",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
