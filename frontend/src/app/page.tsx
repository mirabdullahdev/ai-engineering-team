"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [status, setStatus] = useState("checking…");

  useEffect(() => {
    fetch("http://localhost:8000/api/health")
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus("backend offline"));
  }, []);

  return (
    <main className="grid min-h-screen place-items-center">
      <p className="text-2xl font-semibold text-violet-600">Backend: {status}</p>
    </main>
  );
}
