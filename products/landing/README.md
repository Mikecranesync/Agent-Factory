# Rivet Landing Page

Voice-First CMMS for Field Technicians - Marketing website with Stripe checkout integration.

## Features

- **Landing Page** - Hero, Features, How It Works, CTA sections
- **Pricing Page** - 3 pricing tiers (Basic, Pro, Enterprise) with email collection
- **Checkout Flow** - Integration with FastAPI backend for Stripe checkout
- **Success Page** - Post-checkout onboarding instructions
- **Responsive Design** - Mobile-first with Tailwind CSS

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Deployment**: Vercel

## Development

### Prerequisites

- Node.js 18+
- npm or pnpm

### Setup

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.local.example .env.local

# Edit .env.local with your values:
# - NEXT_PUBLIC_STRIPE_PRICE_BASIC
# - NEXT_PUBLIC_STRIPE_PRICE_PRO
# - NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE
# - API_URL (backend FastAPI URL)

# Run development server
npm run dev
```

The app will be available at http://localhost:3000 (or http://localhost:8888 if 3000 is in use).

### Build

```bash
npm run build
npm run start
```

## Environment Variables

Create a `.env.local` file with:

```env
# Stripe Price IDs (get from Stripe dashboard)
NEXT_PUBLIC_STRIPE_PRICE_BASIC=price_xxx_basic
NEXT_PUBLIC_STRIPE_PRICE_PRO=price_xxx_pro
NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE=price_xxx_enterprise

# Backend API URL
API_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment to Vercel

### One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/Agent-Factory)

### Manual Deploy

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy
cd products/landing
vercel
```

### Environment Variables in Vercel

In your Vercel project dashboard, add the following environment variables:

1. Go to Settings → Environment Variables
2. Add each variable from `.env.local`:
   - `NEXT_PUBLIC_STRIPE_PRICE_BASIC`
   - `NEXT_PUBLIC_STRIPE_PRICE_PRO`
   - `NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE`
   - `API_URL`
   - `NEXT_PUBLIC_API_URL`

3. Redeploy after adding variables

## Project Structure

```
products/landing/
├── app/
│   ├── page.tsx              # Landing page
│   ├── pricing/page.tsx      # Pricing page
│   ├── success/page.tsx      # Post-checkout success
│   ├── layout.tsx            # Root layout
│   ├── globals.css           # Global styles
│   └── api/
│       └── checkout/route.ts # Checkout API route
├── components/
│   ├── Hero.tsx
│   ├── Features.tsx
│   ├── HowItWorks.tsx
│   └── CTA.tsx
├── lib/
│   └── api.ts                # API client
└── public/
    └── images/
```

## Routes

- `/` - Landing page
- `/pricing` - Pricing tiers and checkout
- `/success` - Post-checkout onboarding
- `/api/checkout` - Backend proxy for Stripe checkout

## Backend Integration

The frontend communicates with the FastAPI backend at `/api/checkout`:

**POST /api/checkout/create**
```json
{
  "email": "user@example.com",
  "tier": "pro"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_xxx"
}
```

## Live Deployment

**Production URL:** https://landing-zeta-plum.vercel.app

**Deployed:** 2025-12-27

**Status:** ✅ All pages live and functional

## Success Criteria

- [x] Landing page loads at localhost:3000
- [x] Pricing page shows 3 tiers
- [x] Checkout redirects to Stripe (when backend is running)
- [x] Success page shows next steps
- [x] Mobile responsive
- [x] Deployed to Vercel

## Notes

- The backend API must be running for checkout to work
- For local testing without backend, the checkout will fail gracefully
- Enterprise tier redirects to email instead of Stripe
- Free 14-day trial messaging (no credit card required)

## Contact

For questions or support: support@rivet.com
