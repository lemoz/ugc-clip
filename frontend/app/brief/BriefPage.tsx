"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient } from "@/lib/api";

const TEMPLATES = [
  { slug: "product-review", name: "Product Review", desc: "Honest review of a product" },
  { slug: "testimonial", name: "Testimonial", desc: "Share your transformation story" },
  { slug: "unboxing", name: "Unboxing", desc: "First impression unboxing" },
  { slug: "day-in-life", name: "Day in the Life", desc: "Naturally feature a product in your day" },
];

export function BriefPage() {
  const searchParams = useSearchParams();
  const personaId = searchParams.get("persona_id") || "";
  const [personas, setPersonas] = useState<{ id: string; name: string }[]>([]);
  const [selectedPersona, setSelectedPersona] = useState(personaId);
  const [template, setTemplate] = useState("product-review");
  const [productName, setProductName] = useState("");
  const [cta, setCta] = useState("");
  const [tone, setTone] = useState("casual");
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    apiClient.listPersonas().then(setPersonas).catch(() => {});
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      if (!selectedPersona) {
        setError("Please select a persona");
        return;
      }
      const brief = await apiClient.createBrief({
        template_slug: template,
        title: `Brief: ${productName || "Untitled"}`,
        product_name: productName,
        call_to_action: cta,
        tone,
        target_duration: 30,
      });
      const project = await apiClient.createProjectFromBrief({
        persona_id: selectedPersona,
        brief_id: brief.id,
        name: brief.title,
      });
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    }
  }

  return (
    <div className="max-w-2xl mx-auto mt-12 px-6">
      <h1 className="text-2xl font-bold mb-6">Create Content Brief</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <label className="block text-sm text-gray-400 mb-2">Persona</label>
          <select
            value={selectedPersona}
            onChange={(e) => setSelectedPersona(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100"
            required
          >
            <option value="">Select a persona...</option>
            {personas.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <label className="block text-sm text-gray-400 mb-3">Template</label>
          <div className="grid grid-cols-2 gap-3">
            {TEMPLATES.map((t) => (
              <button
                key={t.slug}
                type="button"
                onClick={() => setTemplate(t.slug)}
                className={`text-left p-3 rounded border transition-colors ${
                  template === t.slug
                    ? "border-blue-500 bg-blue-500/10 text-blue-300"
                    : "border-gray-700 hover:border-gray-500"
                }`}
              >
                <div className="font-medium text-sm">{t.name}</div>
                <div className="text-xs text-gray-400 mt-1">{t.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Product / Service Name</label>
            <input
              type="text"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              placeholder="What are you promoting?"
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Call to Action</label>
            <input
              type="text"
              value={cta}
              onChange={(e) => setCta(e.target.value)}
              placeholder="e.g., Check the link in my bio"
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Tone</label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100"
            >
              <option value="casual">Casual</option>
              <option value="excited">Excited</option>
              <option value="emotional">Emotional</option>
              <option value="relaxed">Relaxed</option>
            </select>
          </div>
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-lg font-medium transition-colors"
        >
          Create Project
        </button>
      </form>
    </div>
  );
}
