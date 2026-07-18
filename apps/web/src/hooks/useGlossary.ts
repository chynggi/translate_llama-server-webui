import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getGlossary } from "../api/glossary";

export function useGlossary(initialQuery = "") {
  const [q, setQ] = useState(initialQuery);
  const query = useQuery({
    queryKey: ["glossary", q],
    queryFn: () => getGlossary(q),
  });
  return { q, setQ, ...query };
}
