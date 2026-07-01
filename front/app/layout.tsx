import "./globals.css";

import { Providers } from "./providers";

export const metadata = {
  title: "Continuous Discovery Agent",
  description: "Consultant-facing organizational learning copilot"
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ja">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
