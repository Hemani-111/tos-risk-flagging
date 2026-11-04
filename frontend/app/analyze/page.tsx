"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

export default function AnalyzePage() {
  const router = useRouter();
  React.useEffect(() => {
    router.replace("/");
  }, [router]);
  return null;
}
