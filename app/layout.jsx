// app/layout.jsx
import "./globals.css";

export const metadata = {
  title: "YB Task Management",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
