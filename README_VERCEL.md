# Hosting on Vercel

This project is configured for deployment on Vercel.

## Prerequisites

1.  **GitHub Account**: Your code must be pushed to a GitHub repository.
2.  **Vercel Account**: Sign up at [vercel.com](https://vercel.com) using your GitHub account.
3.  **Database Services**:
    *   **PostgreSQL**: You need a hosted PostgreSQL database (e.g., [Neon](https://neon.tech), [Supabase](https://supabase.com), or [Render](https://render.com)).
    *   **MongoDB**: You need a hosted MongoDB database (e.g., [MongoDB Atlas](https://www.mongodb.com/atlas)).

## Deployment Steps

### 1. Push Code to GitHub

Initialize git (if not done) and push your code:

```bash
git init
git add .
git commit -m "Initial commit for Vercel deployment"
# Add your remote origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Import Project in Vercel

1.  Go to your Vercel Dashboard.
2.  Click **"Add New..."** -> **"Project"**.
3.  Import your GitHub repository.

### 3. Configure Environment Variables

In the "Configure Project" screen, add the following Environment Variables (copy from your `.env` but use production values):

*   `DATABASE_URL`: Your hosted PostgreSQL connection string.
    *   *Format*: `postgresql://user:password@host:port/database`
    *   *Note*: Ensure it uses `postgresql://` (the app handles the conversion to `postgresql+asyncpg://`).
*   `MONGODB_URL`: Your hosted MongoDB connection string.
*   `JWT_SECRET_KEY`: Generate a secure random string (e.g., `openssl rand -hex 32`).
*   `JWT_ALGORITHM`: `HS256`
*   `ACCESS_TOKEN_EXPIRE_MINUTES`: `30` (or your preference)
*   `GROQ_API_KEY`: Your Groq API key.
*   `GRAPHHOPPER_API_KEY`: Your GraphHopper API key.
*   `GROQ_MODEL`: `llama-3.3-70b-versatile` (or your preferred model).

### 4. Deploy

1.  Click **"Deploy"**.
2.  Vercel will build the project and install dependencies from `requirements.txt`.
3.  Once deployed, you will get a public URL (e.g., `https://your-project.vercel.app`).

### 5. Verify Deployment

*   Visit `https://your-project.vercel.app/docs` to see the API documentation.
*   The frontend should be available at the root URL `https://your-project.vercel.app`.

## Troubleshooting

*   **Database Connection Errors**: Ensure your database allows connections from Vercel's IP addresses (set to "Allow all" or "0.0.0.0/0" for testing).
*   **Missing Dependencies**: Check the "Build Logs" in Vercel if the deployment fails.
*   **Static Files**: If the frontend doesn't load, ensure the `static` folder is present in the repository.
