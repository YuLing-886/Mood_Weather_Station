import { useEffect, useState } from "react";
import { loadMoodData } from "../data/loadData";
import type { DataBundle } from "../types";

interface DataState {
  data: DataBundle | null;
  loading: boolean;
  error: string | null;
}

export function useMoodData(): DataState {
  const [state, setState] = useState<DataState>({ data: null, loading: true, error: null });

  useEffect(() => {
    let alive = true;
    loadMoodData()
      .then((data) => {
        if (alive) setState({ data, loading: false, error: null });
      })
      .catch((error: unknown) => {
        if (alive) setState({ data: null, loading: false, error: error instanceof Error ? error.message : String(error) });
      });
    return () => {
      alive = false;
    };
  }, []);

  return state;
}
