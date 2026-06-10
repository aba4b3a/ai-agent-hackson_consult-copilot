import "./globals.css";

export const metadata = {
  title: "AI QualityOps Agent",
  description: "AI-powered QualityOps dashboard"
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
