export default function Features() {
  const features = [
    {
      icon: "🎤",
      title: "Voice Work Orders",
      description: "Describe the problem, we create the work order. No typing, no forms."
    },
    {
      icon: "📊",
      title: "Chat with Your Print",
      description: "Upload any schematic, ask questions. Get instant answers from AI."
    },
    {
      icon: "📱",
      title: "Works on Telegram",
      description: "No app to download, works offline. Already on your phone."
    }
  ];

  return (
    <section className="py-20 px-4 bg-white">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">
          Maintenance Made Simple
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-gray-50 p-8 rounded-lg text-center hover:shadow-lg transition"
            >
              <div className="text-6xl mb-4">{feature.icon}</div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-gray-600">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
