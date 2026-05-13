"use client";

import { Suspense } from "react";
import { BriefPage as BriefPageInner } from "./BriefPage";

export default function BriefPageWrapper() {
  return (
    <Suspense fallback={<div className="max-w-2xl mx-auto mt-12 px-6 text-gray-400">Loading...</div>}>
      <BriefPageInner />
    </Suspense>
  );
}
