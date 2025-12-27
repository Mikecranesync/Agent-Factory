#!/bin/bash
# Rivet Landing Page - Quick Deployment Script

echo "🚀 Rivet Landing Page Deployment"
echo "=================================="
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found"
    echo "📦 Installing Vercel CLI..."
    npm i -g vercel
fi

echo "✅ Vercel CLI installed"
echo ""

# Login to Vercel
echo "🔐 Logging in to Vercel..."
vercel login
echo ""

# Deploy to production
echo "🚀 Deploying to production..."
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Add environment variables in Vercel dashboard"
echo "2. Go to https://vercel.com/dashboard"
echo "3. Select your project → Settings → Environment Variables"
echo "4. Add the following variables:"
echo "   - NEXT_PUBLIC_STRIPE_PRICE_BASIC"
echo "   - NEXT_PUBLIC_STRIPE_PRICE_PRO"
echo "   - NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE"
echo "   - API_URL"
echo "   - NEXT_PUBLIC_API_URL"
echo "5. Redeploy: vercel --prod"
echo ""
echo "📖 See DEPLOYMENT.md for detailed instructions"
