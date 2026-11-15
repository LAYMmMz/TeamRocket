# 🚀 Quick Start Guide for Frontend & Integration Teammates

Welcome to the NASA Space Apps Challenge frontend repository setup! To connect your Next.js components to our Supabase backend, follow these 3 quick steps:

# Step 1: Install the Supabase Client
Run this command in your terminal inside the project root folder to install the required package:

npm install @supabase/supabase-js

# Step 2: Configure Your Environment Variables
Create a file named .env.local right in the root of your project directory (make sure it is added to your .gitignore so secrets are never pushed publicly). Add your public credentials provided by the database team:

# Code snippet
NEXT_PUBLIC_SUPABASE_URL=https://ziecxjoeljxoocixejtz.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_voJTt1u1bJHhGZD6YAbJkA_XHOuPhEP

⚠️ Important: Never use the service-role/secret key in frontend code! Always use the public anon key, as data access is governed securely by Supabase Row-Level Security (RLS).

## Step 3: Import and Use Query Helpers
We’ve set up centralized query helpers in lib/supabaseQueries.js to handle time-series ordering (measured_at) and Section 4.1 data dictionary standards automatically. You can import them directly into your components:

JavaScript
import { getAstronautVitals, getPersonalDoses, getActiveAlerts } from '@/lib/supabaseQueries'

// Example inside your page or component
export default async function Page() {
    const vitals = await getAstronautVitals('astronaut-uuid-here')
    // Render your UI components here...
}