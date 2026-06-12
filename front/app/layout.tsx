import "./globals.css";

export const metadata = {
  title: "Continuous Discovery Agent",
  description: "Consultant-facing organizational learning copilot"
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
