"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api";

export default function PersonasPage() {
  const [personas, setPersonas] = useState<{ id: string; name: string; display_name: string }[]>([]);

  useEffect(() => {
    apiClient.listPersonas().then(setPersonas).catch(() => {});
  }, []);

  return (
    <div className="max-w-3xl mx-auto mt-12 px-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Personas</h1>
        <Link
          href="/upload"
          className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded text-white transition-colors text-sm"
        >
          New Persona
        </Link>
      </div>

      {personas.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-gray-400">No personas created yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {personas.map((p) => (
            <div
              key={p.id}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex justify-between items-center"
            >
              <span className="font-medium">{p.display_name || p.name}</span>
              <Link
                href={`/brief?persona_id=${p.id}`}
                className="text-blue-400 hover:underline text-sm"
              >
                Create Brief
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
