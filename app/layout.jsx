import '../styles/globals.css';
import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";

export const metadata = {
  title: "YB Task UI",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="flex">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Topbar />
          <main className="p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}