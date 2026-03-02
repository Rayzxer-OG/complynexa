"use client";

import { useCallback, useEffect, useState } from "react";
import { getComplianceChecklist, type ComplianceChecklistItem } from "@/lib/api";

export function useComplianceChecklist(unitId: string | null) {
  const [items, setItems] = useState<ComplianceChecklistItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | unknown>(null);

  const refresh = useCallback(async () => {
    if (!unitId) {
      setItems([]);
      setError(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getComplianceChecklist(unitId);
      setItems(data);
    } catch (e) {
      setError(e);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [unitId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { items, loading, error, refresh };
}
