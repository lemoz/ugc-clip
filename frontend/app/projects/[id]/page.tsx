export default async function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <div className="max-w-3xl mx-auto mt-12 px-6">
      <h1 className="text-2xl font-bold mb-2">Project {id}</h1>
      <p className="text-gray-400 mb-8">Pipeline status and video preview</p>

      <div className="space-y-4">
        {[
          { stage: 0, name: "Onboarding & Verification", done: true },
          { stage: 1, name: "Content Brief", done: true },
          { stage: 2, name: "Structured Artifacts", done: true },
          { stage: 3, name: "Pre-Generation Gates", done: true },
          { stage: 4, name: "Visual Anchors", done: false },
          { stage: 5, name: "Segment Generation", done: false },
          { stage: 6, name: "Audio Mix", done: false },
          { stage: 7, name: "FFmpeg Assembly", done: false },
          { stage: 8, name: "Post-Generation Gates", done: false },
          { stage: 9, name: "Human Review", done: false },
        ].map((s) => (
          <div
            key={s.stage}
            className={`flex items-center gap-3 p-3 rounded border ${
              s.done ? "border-green-800 bg-green-500/5" : "border-gray-800"
            }`}
          >
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                s.done ? "bg-green-500 text-white" : "bg-gray-800 text-gray-500"
              }`}
            >
              {s.done ? "✓" : s.stage}
            </div>
            <span className={s.done ? "text-gray-200" : "text-gray-500"}>
              {s.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
