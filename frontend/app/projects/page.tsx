"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<{ id: string; name: string; status: string; stage: number }[]>([]);

  useEffect(() => {
    apiClient.listProjects().then(setProjects).catch(() => {});
  }, []);

  return (
    <div className="max-w-3xl mx-auto mt-12 px-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Projects</h1>
        <Link
          href="/brief"
          className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded text-white transition-colors text-sm"
        >
          New Project
        </Link>
      </div>

      {projects.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-gray-400 mb-4">No projects yet. Create your first UGC video!</p>
          <Link href="/upload" className="text-blue-400 hover:underline">
            Create a persona first
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className="block bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors"
            >
              <div className="flex justify-between items-center">
                <div>
                  <div className="font-medium">{p.name}</div>
                  <div className="text-sm text-gray-400">Stage: {p.stage}/9</div>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${
                  p.status === "complete" ? "bg-green-500/20 text-green-400" :
                  p.status === "failed" ? "bg-red-500/20 text-red-400" :
                  "bg-blue-500/20 text-blue-400"
                }`}>
                  {p.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
