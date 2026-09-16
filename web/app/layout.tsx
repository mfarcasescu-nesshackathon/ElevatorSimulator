import type { Metadata, ReactNode } from "next";
import { ReleaseNav } from "@/components/release-nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Elevator Simulator",
  description: "Destination-dispatch elevator simulation with a live 3D view",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        <ReleaseNav />
        {children}
      </body>
    </html>
  );
}
