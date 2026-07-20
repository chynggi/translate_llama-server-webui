import { useCallback, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  appendMessage,
  createConversation,
  deleteConversation,
  getConversation,
  importConversation,
  listConversations,
  patchConversation,
} from "../api/conversations";
import type {
  AppendMessageRequest,
  ConversationDetail,
  ConversationMessage,
  ConversationSession,
} from "../types";

export interface ConversationsState {
  conversations: ConversationSession[];
  listLoading: boolean;
  activeId: string | null;
  session: ConversationSession | null;
  messages: ConversationMessage[];
  detailLoading: boolean;
  error: string;
  select: (id: string) => Promise<void>;
  clearSelection: () => void;
  createNew: () => Promise<ConversationDetail>;
  remove: (id: string) => Promise<void>;
  rename: (id: string, name: string) => Promise<void>;
  post: (body: AppendMessageRequest) => Promise<ConversationMessage>;
  navigate: (leafId: string) => Promise<void>;
  setThinkingEnabled: (enabled: boolean) => Promise<void>;
  importJsonl: (text: string) => Promise<void>;
  refreshDetail: () => Promise<void>;
}

export function useConversations(): ConversationsState {
  const queryClient = useQueryClient();
  const listQuery = useQuery({
    queryKey: ["conversations"],
    queryFn: listConversations,
  });
  const [activeId, setActiveId] = useState<string | null>(null);
  const activeIdRef = useRef<string | null>(null);
  const [session, setSession] = useState<ConversationSession | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");

  const setActive = useCallback((id: string | null) => {
    activeIdRef.current = id;
    setActiveId(id);
  }, []);

  const refreshList = useCallback(
    () => queryClient.invalidateQueries({ queryKey: ["conversations"] }),
    [queryClient]
  );

  const loadDetail = useCallback(async (id: string, showSpinner = true) => {
    if (showSpinner) setDetailLoading(true);
    try {
      const detail = await getConversation(id);
      setSession(detail.session);
      setMessages(detail.messages);
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Load failed");
    } finally {
      if (showSpinner) setDetailLoading(false);
    }
  }, []);

  const select = useCallback(
    async (id: string) => {
      setActive(id);
      await loadDetail(id);
    },
    [loadDetail, setActive]
  );

  const clearSelection = useCallback(() => {
    setActive(null);
    setSession(null);
    setMessages([]);
  }, [setActive]);

  const createNew = useCallback(async () => {
    const detail = await createConversation({});
    await refreshList();
    setActive(detail.session.id);
    setSession(detail.session);
    setMessages(detail.messages);
    return detail;
  }, [refreshList, setActive]);

  const remove = useCallback(
    async (id: string) => {
      await deleteConversation(id);
      if (activeIdRef.current === id) {
        setActive(null);
        setSession(null);
        setMessages([]);
      }
      await refreshList();
    },
    [refreshList, setActive]
  );

  const rename = useCallback(
    async (id: string, name: string) => {
      const { session: updated } = await patchConversation(id, { name });
      if (id === activeIdRef.current) setSession(updated);
      await refreshList();
    },
    [refreshList]
  );

  const post = useCallback(
    async (body: AppendMessageRequest) => {
      const convId = activeIdRef.current;
      if (!convId) throw new Error("no active conversation");
      const result = await appendMessage(convId, body);
      // Silent reload keeps parent children links consistent.
      await loadDetail(convId, false);
      await refreshList();
      return result.message;
    },
    [loadDetail, refreshList]
  );

  const navigate = useCallback(
    async (leafId: string) => {
      const convId = activeIdRef.current;
      if (!convId) return;
      setSession((current) =>
        current ? { ...current, currNode: leafId } : current
      );
      await patchConversation(convId, { currNode: leafId });
    },
    []
  );

  const setThinkingEnabled = useCallback(
    async (enabled: boolean) => {
      const convId = activeIdRef.current;
      if (!convId) return;
      const { session: updated } = await patchConversation(convId, {
        thinkingEnabled: enabled,
      });
      setSession(updated);
    },
    []
  );

  const importJsonl = useCallback(
    async (text: string) => {
      const detail = await importConversation(text);
      await refreshList();
      setActive(detail.session.id);
      setSession(detail.session);
      setMessages(detail.messages);
    },
    [refreshList, setActive]
  );

  const refreshDetail = useCallback(async () => {
    if (activeIdRef.current) await loadDetail(activeIdRef.current, false);
  }, [loadDetail]);

  return {
    conversations: listQuery.data?.conversations ?? [],
    listLoading: listQuery.isLoading,
    activeId,
    session,
    messages,
    detailLoading,
    error,
    select,
    clearSelection,
    createNew,
    remove,
    rename,
    post,
    navigate,
    setThinkingEnabled,
    importJsonl,
    refreshDetail,
  };
}
