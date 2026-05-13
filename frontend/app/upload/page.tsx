"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";

export default function UploadPage() {
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [personas, setPersonas] = useState<{ id: string; name: string }[]>([]);
  const router = useRouter();

  useEffect(() => {
    apiClient.listPersonas().then(setPersonas).catch(() => {});
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const persona = await apiClient.createPersona(name);
      router.push(`/personas/${persona.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create persona");
    }
  }

  return (
    <div className="max-w-2xl mx-auto mt-12 px-6">
      <h1 className="text-2xl font-bold mb-6">Create a Persona</h1>
      <p className="text-gray-400 mb-8">
        A persona represents you in your videos. Create one to get started with UGC generation.
      </p>

      <form onSubmit={handleCreate} className="space-y-4 bg-gray-900 border border-gray-800 rounded-lg p-6 mb-8">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Persona Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., My UGC Persona"
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100 focus:outline-none focus:border-blue-500"
            required
          />
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2 rounded font-medium transition-colors"
        >
          Create Persona
        </button>
      </form>

      {personas.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Your Personas</h2>
          <div className="space-y-2">
            {personas.map((p) => (
              <div
                key={p.id}
                className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex justify-between items-center"
              >
                <span>{p.name}</span>
                <span className="text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded">
                  Pending verification
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
