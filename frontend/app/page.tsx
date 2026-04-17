"use client";

import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

export default function Home() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    apiGet("/").then(setData);
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>Strike3</h1>

      <h2>Backend Response:</h2>

      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}