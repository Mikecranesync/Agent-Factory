# WORKSTREAM 2: FRONTEND + PAYMENTS
# Tab 2 of 3
# Copy everything below this line into Claude Code CLI

You are WS-2 (Frontend) in a 3-tab parallel development sprint for Rivet MVP.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task
- If context reaches 80%, checkpoint and summarize

## YOUR IDENTITY
- Workstream: WS-2 (Frontend + Payments)
- Branch: rivet-frontend
- Focus: Landing page, Stripe checkout, user onboarding

## FIRST ACTIONS
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b rivet-frontend
git push -u origin rivet-frontend
```

## EXISTING CODE
```
agent_factory/api/routers/stripe.py    # Full Stripe implementation (DONE)
agent_factory/rivet_pro/stripe_integration.py  # Stripe manager (exists)
```

The Stripe backend is DONE. You're building the frontend that calls it.

## YOUR TASKS

### Phase 1: Landing Page Structure (Day 1)

**Task 1.1: Initialize Next.js App**
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
mkdir -p products/landing
cd products/landing
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir
```

**Task 1.2: Project Structure**
```
products/landing/
├── app/
│   ├── page.tsx              # Landing page
│   ├── pricing/page.tsx      # Pricing page
│   ├── success/page.tsx      # Post-checkout success
│   ├── layout.tsx            # Root layout
│   └── api/
│       └── checkout/route.ts # Calls backend API
├── components/
│   ├── Hero.tsx
│   ├── Features.tsx
│   ├── HowItWorks.tsx
│   ├── Pricing.tsx
│   └── CTA.tsx
├── lib/
│   └── api.ts                # API client
└── public/
    └── images/
```

### Phase 2: Landing Page Content (Day 1)

**Task 2.1: Hero Section**
```tsx
// components/Hero.tsx
<section className="...">
  <h1>Voice-First CMMS for Field Technicians</h1>
  <p>Create work orders by voice. Ask AI about any schematic. 
     Works on Telegram - no app to install.</p>
  <Button href="/pricing">Get Started</Button>
  <Button href="#how-it-works" variant="secondary">See How It Works</Button>
</section>
```

**Task 2.2: Features Section**
Three cards:
1. 🎤 **Voice Work Orders** - "Describe the problem, we create the work order"
2. 📊 **Chat with Your Print** - "Upload any schematic, ask questions"  
3. 📱 **Works on Telegram** - "No app to download, works offline"

**Task 2.3: How It Works Section**
Three steps:
1. Open Telegram → Search @RivetCEO_bot
2. Send a voice message → "The main pump is making noise"
3. Work order created → Automatically logged with equipment details

**Task 2.4: CTA Section**
```tsx
<section>
  <h2>Ready to modernize your maintenance?</h2>
  <Button href="/pricing">Start Free Trial</Button>
  <p>No credit card required for 14-day trial</p>
</section>
```

### Phase 3: Pricing Page (Day 2)

**Task 3.1: Pricing Cards**
```tsx
// app/pricing/page.tsx
const tiers = [
  {
    name: "Basic",
    price: "$20",
    period: "/tech/month",
    features: [
      "Voice work orders via Telegram",
      "Up to 5 equipment prints",
      "Email support"
    ],
    cta: "Start Free Trial",
    priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_BASIC
  },
  {
    name: "Pro",
    price: "$40",
    period: "/tech/month",
    popular: true,
    features: [
      "Everything in Basic",
      "Unlimited prints",
      "Chat with Print (AI Q&A)",
      "Priority support"
    ],
    cta: "Start Free Trial",
    priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_PRO
  },
  {
    name: "Enterprise",
    price: "$99",
    period: "/tech/month",
    features: [
      "Everything in Pro",
      "Predictive maintenance AI",
      "API access",
      "SSO/SAML",
      "Dedicated support"
    ],
    cta: "Contact Sales",
    priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE
  }
];
```

**Task 3.2: Checkout Button**
```tsx
async function handleCheckout(priceId: string, tier: string) {
  const res = await fetch('/api/checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      email: userEmail,
      tier: tier 
    })
  });
  const { checkout_url } = await res.json();
  window.location.href = checkout_url;
}
```

**Task 3.3: API Route to Backend**
```typescript
// app/api/checkout/route.ts
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const { email, tier } = await request.json();
  
  // Call our FastAPI backend
  const res = await fetch(`${process.env.API_URL}/api/checkout/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, tier })
  });
  
  const data = await res.json();
  return NextResponse.json(data);
}
```

### Phase 4: Success Page (Day 2)

**Task 4.1: Post-Checkout Success**
```tsx
// app/success/page.tsx
export default function SuccessPage({ searchParams }) {
  return (
    <div className="text-center py-20">
      <h1>🎉 Welcome to Rivet!</h1>
      <p>Your account is ready. Here's how to get started:</p>
      
      <ol className="text-left max-w-md mx-auto mt-8">
        <li>1. Open Telegram on your phone</li>
        <li>2. Search for <strong>@RivetCEO_bot</strong></li>
        <li>3. Tap <strong>Start</strong></li>
        <li>4. Send your first voice message!</li>
      </ol>
      
      <a href="https://t.me/RivetCEO_bot" className="btn-primary mt-8">
        Open Telegram Bot →
      </a>
    </div>
  );
}
```

### Phase 5: Environment & Deploy (Day 3)

**Task 5.1: Environment Variables**
Create `products/landing/.env.local`:
```
NEXT_PUBLIC_STRIPE_PRICE_BASIC=price_xxx
NEXT_PUBLIC_STRIPE_PRICE_PRO=price_xxx
NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE=price_xxx
API_URL=http://localhost:8000
```

**Task 5.2: Deploy to Vercel**
```bash
cd products/landing
npx vercel
# Follow prompts, set env vars in Vercel dashboard
```

## COMMIT PROTOCOL
After EACH task:
```bash
git add -A
git commit -m "WS-2: [component] description"
git push origin rivet-frontend
```

## SUCCESS CRITERIA
- [ ] Landing page loads at localhost:3000
- [ ] Pricing page shows 3 tiers
- [ ] Checkout redirects to Stripe
- [ ] Success page shows next steps
- [ ] Mobile responsive
- [ ] Deployed to Vercel

## DEPENDENCIES
- WS-1 must have API running for checkout to work
- For now, can test with mock API responses

## UPDATE STATUS
After each phase, update: `/sprint/STATUS_WS2.md`

## START NOW
Begin with Task 1.1 - Initialize Next.js app.
