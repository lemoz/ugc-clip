"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

export function NavBar() {
  const [user, setUser] = useState<{ email: string } | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      apiClient.getMe().then(setUser).catch(() => localStorage.removeItem("token"));
    }
  }, []);

  return (
    <nav className="border-b border-gray-800 px-6 py-3 flex items-center justify-between">
      <Link href="/" className="font-bold text-lg text-blue-400">
        UGC Clip
      </Link>
      <div className="flex gap-4 items-center text-sm">
        {user ? (
          <>
            <Link href="/projects" className="hover:text-blue-400 transition-colors">
              Projects
            </Link>
            <Link href="/personas" className="hover:text-blue-400 transition-colors">
              Personas
            </Link>
            <span className="text-gray-400">{user.email}</span>
            <button
              onClick={() => {
                localStorage.removeItem("token");
                setUser(null);
              }}
              className="text-gray-400 hover:text-red-400 transition-colors"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link href="/login" className="hover:text-blue-400 transition-colors">
              Login
            </Link>
            <Link
              href="/register"
              className="bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-white transition-colors"
            >
              Sign Up
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
