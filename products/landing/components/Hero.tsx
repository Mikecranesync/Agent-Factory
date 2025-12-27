import Link from "next/link";
import { Mic, FileText, Wrench } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative py-20 px-4 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-rivet-dark via-rivet-gray to-rivet-dark" />

      <div className="relative max-w-6xl mx-auto text-center">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center gap-3">
            <Wrench className="w-12 h-12 text-rivet-orange" />
            <span className="text-4xl font-bold text-white">Rivet</span>
          </div>
        </div>

        {/* Headline */}
        <h1 className="text-5xl md:text-7xl font-bold mb-6 text-white">
          Your AI <span className="text-rivet-orange">Maintenance Assistant</span>
        </h1>

        <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
          Voice-first CMMS for field technicians. Upload prints, get instant answers,
          create work orders by speaking.
        </p>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          <div className="flex items-center gap-2 bg-rivet-gray px-4 py-2 rounded-full">
            <Mic className="w-5 h-5 text-rivet-orange" />
            <span className="text-white">Voice Commands</span>
          </div>
          <div className="flex items-center gap-2 bg-rivet-gray px-4 py-2 rounded-full">
            <FileText className="w-5 h-5 text-rivet-orange" />
            <span className="text-white">Print Analysis</span>
          </div>
          <div className="flex items-center gap-2 bg-rivet-gray px-4 py-2 rounded-full">
            <Wrench className="w-5 h-5 text-rivet-orange" />
            <span className="text-white">Work Orders</span>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/pricing"
            className="bg-rivet-orange hover:bg-orange-600 text-white px-8 py-4 rounded-lg text-lg font-semibold transition"
          >
            Start Free Trial
          </Link>
          <Link
            href={process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "#"}
            className="border border-white hover:bg-white hover:text-rivet-dark px-8 py-4 rounded-lg text-lg font-semibold transition text-white"
          >
            Try on Telegram
          </Link>
        </div>
      </div>
    </section>
  );
}
