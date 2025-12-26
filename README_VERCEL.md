# Hosting on Vercel with Integrations

This project is configured for deployment on Vercel. You can use **Vercel Integrations** to easily connect Supabase (Postgres) and MongoDB Atlas without manually copying many environment variables.

## 1. Deploy Code

1.  Push your code to GitHub.
2.  Import the project in Vercel.
3.  Deploy. (The build might fail initially; this is expected until we add the databases).

## 2. Set Up Supabase (PostgreSQL) via Integration

1.  Go to your **Vercel Project Dashboard**.
2.  Click the **Settings** tab -> **Integrations**.
3.  Click **Browse Marketplace**.
4.  Search for **Supabase** and click **Add Integration**.
5.  Select your Vercel account and the project you just created.
6.  Follow the prompts to:
    *   **Connect** to an existing Supabase project, OR
    *   **Create** a new Supabase project directly from the interface.
7.  Once connected, this will automatically add environment variables like `SUPABASE_URL` and `SUPABASE_KEY` to your project.
    *   **Important Check**: Go to **Settings** -> **Environment Variables**. Check if `DATABASE_URL` is present.
    *   **If `DATABASE_URL` is missing**: You must manually add it.
        1.  Go to your [Supabase Dashboard](https://supabase.com/dashboard).
        2.  Go to **Project Settings** -> **Database**.
        3.  Copy the **URI** connection string (e.g., `postgresql://postgres...`).
        4.  Add it as a new environment variable named `DATABASE_URL` in Vercel.

### Enable PostGIS (Required)
The integration does not enable extensions for you.
1.  Go to your Supabase Dashboard -> **SQL Editor**.
2.  Run: `CREATE EXTENSION IF NOT EXISTS postgis;`

## 3. Set Up MongoDB Atlas via Integration

1.  Go to your **Vercel Project Dashboard**.
2.  Click the **Settings** tab -> **Integrations**.
3.  Click **Browse Marketplace**.
4.  Search for **MongoDB Atlas** and click **Add Integration**.
5.  Select your Vercel account and project.
6.  Follow the prompts to log in to MongoDB Atlas and select your cluster.
7.  This will automatically add the `MONGODB_URI` environment variable to your project.
    *   *Note*: The app is updated to recognize `MONGODB_URI` automatically.

## 4. Other Environment Variables

Go to **Settings** -> **Environment Variables** and ensure you have these manual variables:

*   `JWT_SECRET_KEY`: Generate a secure random string (e.g., `openssl rand -hex 32`).
*   `GROQ_API_KEY`: Your Groq API key.
*   `GRAPHHOPPER_API_KEY`: Your GraphHopper API key.
*   `GROQ_MODEL`: `llama-3.3-70b-versatile`

## 5. Redeploy

1.  Go to the **Deployments** tab.
2.  Click the three dots (`...`) next to your latest deployment.
3.  Select **Redeploy**.
