import type { Metadata } from "next";
import { CartProvider } from "@/components/CartProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Grocery Commerce",
  description: "Shwapno-style AI-enabled grocery commerce demo.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <CartProvider>{children}</CartProvider>
      </body>
    </html>
  );
}
