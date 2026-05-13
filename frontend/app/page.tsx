import Link from "next/link";

export default function HomePage() {
  return (
    <div className="max-w-3xl mx-auto mt-20 px-6 text-center">
      <h1 className="text-4xl font-bold mb-4">
        Create AI-powered UGC videos
      </h1>
      <p className="text-gray-400 text-lg mb-8 max-w-xl mx-auto">
        Upload your face and voice, write a script, and generate authentic
        UGC-style videos with AI. Perfect for product reviews, testimonials,
        unboxings, and more.
      </p>
      <div className="flex gap-4 justify-center mb-16">
        <Link
          href="/register"
          className="bg-blue-600 hover:bg-blue-500 px-6 py-3 rounded-lg font-medium text-white transition-colors"
        >
          Get Started
        </Link>
        <Link
          href="/login"
          className="border border-gray-700 hover:border-gray-500 px-6 py-3 rounded-lg font-medium transition-colors"
        >
          Login
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
        {[
          {
            title: "Upload Your Identity",
            desc: "Upload a short video of your face and a voice sample. We verify it's you.",
          },
          {
            title: "Write Your Script",
            desc: "Pick a UGC template — review, testimonial, unboxing — or write your own.",
          },
          {
            title: "Generate & Review",
            desc: "Our AI generates the video. You review and approve before exporting.",
          },
        ].map((feature) => (
          <div key={feature.title} className="bg-gray-900 border border-gray-800 rounded-lg p-6">
            <h3 className="font-semibold mb-2">{feature.title}</h3>
            <p className="text-sm text-gray-400">{feature.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
