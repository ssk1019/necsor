module.exports = {
  apps: [
    {
      name: "backend",
      script: "gunicorn",
      args: "-w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000",
      cwd: "./Backend",
      interpreter: "python3", // 確保伺服器上有 python3
      env: {
        NODE_ENV: "production",
      },
    },
    {
      name: "frontend",
      script: "npm",
      args: "start",
      cwd: "./Frontend",
      env: {
        NODE_ENV: "production",
        PORT: 3000,
      },
    },
  ],
};
