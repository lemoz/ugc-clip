"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const data = await apiClient.register(email, password, displayName);
      localStorage.setItem("token", data.access_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  }

  return (
    <div className="max-w-md mx-auto mt-20 px-6">
      <h1 className="text-2xl font-bold mb-6">Create Account</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Display Name</label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100 focus:outline-none focus:border-blue-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100 focus:outline-none focus:border-blue-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100 focus:outline-none focus:border-blue-500"
            required
          />
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2 rounded font-medium transition-colors"
        >
          Create Account
        </button>
      </form>
      <p className="text-sm text-gray-400 mt-4 text-center">
        Already have an account?{" "}
        <Link href="/login" className="text-blue-400 hover:underline">
          Login
        </Link>
      </p>
    </div>
  );
}
