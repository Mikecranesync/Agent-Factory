import Link from "next/link";

export default function CTA() {
  return (
    <section className="py-20 px-4 bg-blue-600">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
          Ready to modernize your maintenance?
        </h2>
        <Link
          href="/pricing"
          className="inline-block bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100 transition"
        >
          Start Free Trial
        </Link>
        <p className="text-blue-100 mt-4 text-lg">
          No credit card required for 14-day trial
        </p>
      </div>
    </section>
  );
}
