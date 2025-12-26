# Hosting on Vercel with Supabase & MongoDB Atlas

This project is configured for deployment on Vercel, using **Supabase** for the relational database (PostgreSQL) and **MongoDB Atlas** for the NoSQL database.

## 1. Deploy Code

1.  Push your code to GitHub.
2.  Import the project in Vercel.
3.  Deploy. (The build might fail initially if environment variables are missing; this is normal).

## 2. Set Up Supabase (PostgreSQL)

Since you are using Supabase for the PostgreSQL database:

1.  **Create Project**: Go to [Supabase](https://supabase.com/) and create a new project.
2.  **Enable PostGIS**:
    *   Go to the **SQL Editor** in the left sidebar.
    *   Click **New Query**.
    *   Run: `CREATE EXTENSION IF NOT EXISTS postgis;`
    *   Click **Run**.
3.  **Get Connection String**:
    *   Go to **Project Settings** (gear icon) -> **Database**.
    *   Under **Connection string**, make sure **URI** is selected.
    *   Copy the connection string. It looks like: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`.
    *   *Tip*: Use the "Transaction" pooler (port 6543) if available, or "Session" (port 5432) if you encounter issues. For this async Python app, the standard connection string often works best.
4.  **Add to Vercel**:
    *   Go to your Vercel Project Dashboard -> **Settings** -> **Environment Variables**.
    *   Add a new variable named `DATABASE_URL`.
    *   Paste your Supabase connection string as the value (replace `[password]` with your actual database password).

## 3. Set Up MongoDB Atlas

Since you are using MongoDB Atlas:

1.  **Create Cluster**: Go to [MongoDB Atlas](https://www.mongodb.com/atlas) and create a cluster.
2.  **Get Connection String**:
    *   Click **Connect** on your cluster.
    *   Select **Drivers**.
    *   Copy the connection string (e.g., `mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority`).
3.  **Network Access**:
    *   Go to **Network Access** in the Atlas sidebar.
    *   Click **Add IP Address**.
    *   Select **Allow Access from Anywhere** (0.0.0.0/0). *This is required because Vercel's IP addresses are dynamic.*
4.  **Add to Vercel**:
    *   Go to your Vercel Project Dashboard -> **Settings** -> **Environment Variables**.
    *   Add a new variable named `MONGODB_URL`.
    *   Paste your Atlas connection string (replace `<username>` and `<password>` with your actual credentials).

## 4. Other Environment Variables

In Vercel **Settings** -> **Environment Variables**, ensure you also have:

*   `JWT_SECRET_KEY`: Generate a secure random string (e.g., `openssl rand -hex 32`).
*   `GROQ_API_KEY`: Your Groq API key.
*   `GRAPHHOPPER_API_KEY`: Your GraphHopper API key.
*   `GROQ_MODEL`: `llama-3.3-70b-versatile`

## 5. Redeploy

After adding all environment variables (`DATABASE_URL`, `MONGODB_URL`, and the keys):

1.  Go to the **Deployments** tab in Vercel.
2.  Click the three dots (`...`) next to your latest deployment (or the failed one) and select **Redeploy**.
3.  Ensure **Redeploy** is checked (not "Redeploy with existing build cache" if you want to be safe, though usually fine).
