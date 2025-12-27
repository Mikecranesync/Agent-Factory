# Rivet Landing Page - Deployment Guide

## Prerequisites

1. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository** - Code should be pushed to GitHub
3. **Stripe Account** - Get your Stripe Price IDs from the Stripe dashboard

## Option 1: Deploy via Vercel Dashboard (Recommended)

### Step 1: Connect GitHub Repository

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click "Import Git Repository"
3. Select your GitHub account and repository
4. Choose "Agent-Factory" repository

### Step 2: Configure Project

1. **Root Directory**: Set to `products/landing`
2. **Framework Preset**: Next.js (auto-detected)
3. **Build Command**: `npm run build` (auto-filled)
4. **Output Directory**: `.next` (auto-filled)

### Step 3: Add Environment Variables

Click "Environment Variables" and add:

```env
NEXT_PUBLIC_STRIPE_PRICE_BASIC=price_xxx_basic
NEXT_PUBLIC_STRIPE_PRICE_PRO=price_xxx_pro
NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE=price_xxx_enterprise
API_URL=https://your-backend-api.com
NEXT_PUBLIC_API_URL=https://your-backend-api.com
```

**Where to get Stripe Price IDs:**
1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to Products → Click your product
3. Copy the Price ID (starts with `price_`)

### Step 4: Deploy

1. Click "Deploy"
2. Wait 2-3 minutes for build to complete
3. Your site will be live at `https://your-project.vercel.app`

## Option 2: Deploy via Vercel CLI

### Step 1: Install Vercel CLI

```bash
npm i -g vercel
```

### Step 2: Login to Vercel

```bash
vercel login
```

### Step 3: Deploy

```bash
cd products/landing
vercel
```

Follow the prompts:
- **Set up and deploy?** Yes
- **Which scope?** Select your account
- **Link to existing project?** No
- **Project name?** rivet-landing (or your choice)
- **Directory?** ./ (current directory)

### Step 4: Add Environment Variables

```bash
vercel env add NEXT_PUBLIC_STRIPE_PRICE_BASIC
vercel env add NEXT_PUBLIC_STRIPE_PRICE_PRO
vercel env add NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE
vercel env add API_URL
vercel env add NEXT_PUBLIC_API_URL
```

For each, paste the value when prompted and select "Production" environment.

### Step 5: Redeploy with Environment Variables

```bash
vercel --prod
```

## Option 3: Deploy from Local Machine (Quick Test)

```bash
cd products/landing
vercel --prod
```

This will:
1. Build your project
2. Upload to Vercel
3. Deploy to production
4. Give you a live URL

## Post-Deployment

### 1. Test the Deployment

Visit your deployed URL and test:
- Landing page loads correctly
- Pricing page displays all tiers
- Email input accepts text
- Checkout button (will fail until backend is configured)
- Success page displays

### 2. Configure Custom Domain (Optional)

In Vercel Dashboard:
1. Go to Settings → Domains
2. Add your custom domain (e.g., `rivet.com`)
3. Update DNS records with your domain provider
4. Wait for DNS propagation (5-60 minutes)

### 3. Connect Backend API

Update environment variables with production backend URL:

```bash
# Update API_URL to point to your production backend
vercel env add API_URL production
# Enter: https://your-backend-api.railway.app
```

Then redeploy:
```bash
vercel --prod
```

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `NEXT_PUBLIC_STRIPE_PRICE_BASIC` | Stripe Price ID for Basic tier | `price_1ABC123basic` |
| `NEXT_PUBLIC_STRIPE_PRICE_PRO` | Stripe Price ID for Pro tier | `price_1ABC123pro` |
| `NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE` | Stripe Price ID for Enterprise tier | `price_1ABC123enterprise` |
| `API_URL` | Backend FastAPI URL (server-side) | `https://api.rivet.com` |
| `NEXT_PUBLIC_API_URL` | Backend FastAPI URL (client-side) | `https://api.rivet.com` |

**Note**: Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

## Troubleshooting

### Build Fails

**Error**: `Module not found`
- **Fix**: Run `npm install` locally and commit `package-lock.json`

**Error**: `TypeScript errors`
- **Fix**: Run `npm run build` locally to see errors
- Fix TypeScript errors before deploying

### Checkout Not Working

**Error**: "Checkout failed" or network error
- **Check**: Backend API is running and accessible
- **Check**: `API_URL` environment variable is correct
- **Check**: Backend has CORS enabled for your domain

### Environment Variables Not Working

**Symptom**: Variables are `undefined`
- **Fix**: Redeploy after adding environment variables
- **Fix**: Variables with `NEXT_PUBLIC_` prefix must be set at build time

### Domain Not Working

**Symptom**: Custom domain shows 404
- **Check**: DNS records are configured correctly
- **Check**: Wait for DNS propagation (up to 48 hours)
- **Check**: Domain is verified in Vercel dashboard

## Vercel Configuration (Optional)

Create `vercel.json` in `products/landing/`:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "regions": ["iad1"],
  "env": {
    "NEXT_PUBLIC_STRIPE_PRICE_BASIC": "@stripe-price-basic",
    "NEXT_PUBLIC_STRIPE_PRICE_PRO": "@stripe-price-pro",
    "NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE": "@stripe-price-enterprise",
    "API_URL": "@api-url"
  }
}
```

This enables:
- Custom build commands
- Region selection (iad1 = US East)
- Environment variable references

## Production Checklist

Before going live:

- [ ] All environment variables configured
- [ ] Stripe Price IDs are production values (not test)
- [ ] Backend API is deployed and accessible
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active (auto-enabled by Vercel)
- [ ] Test checkout flow end-to-end
- [ ] Analytics configured (Vercel Analytics, Google Analytics)
- [ ] Error tracking configured (Sentry, LogRocket)

## Monitoring

### Vercel Analytics

Enable in Vercel Dashboard:
1. Go to Analytics tab
2. Enable Web Analytics
3. View real-time traffic and performance

### Vercel Logs

View deployment logs:
1. Go to Deployments tab
2. Click on a deployment
3. View build logs and runtime logs

### Performance

Check performance:
1. Run Lighthouse audit
2. Check Vercel Speed Insights
3. Optimize images and bundle size

## Rollback

If deployment has issues:

1. Go to Deployments tab in Vercel
2. Find previous working deployment
3. Click "Promote to Production"
4. Previous version is now live

## Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Next.js Docs**: [nextjs.org/docs](https://nextjs.org/docs)
- **Vercel Support**: support@vercel.com

## Cost

- **Free Tier**: 100GB bandwidth, unlimited deployments
- **Pro Tier** ($20/month): Custom domains, analytics, team collaboration
- **Enterprise**: Custom pricing for high-traffic sites

For most use cases, the free tier is sufficient for testing and early production.

## Next Steps After Deployment

1. **Test Checkout Flow** with real Stripe account
2. **Set up Analytics** to track conversions
3. **Configure Error Tracking** for production issues
4. **Add Google Analytics** or Plausible for visitor tracking
5. **Set up A/B Testing** for pricing optimization
6. **Configure Email Integration** for lead capture
